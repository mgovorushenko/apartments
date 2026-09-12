"""Offline perspective QA of the actual scene. No browser or image generation.

CPU z-buffer, near clipping, actual meshes and simple material shading. Used to
verify object placement; WebGL additionally provides rounded upholstery and
local lighting. Does not claim photorealism.
"""
import math
import base64
import json
from pathlib import Path
import numpy as np
from PIL import Image
import generate_model as m
from detail_geometry import mesh as detail_mesh


def render(bathroom=False, evening=False, overview=False, pier=False, kitchen_overview=False, room=None,cabinet_open=False):
    m.build_scene()
    width,height=1200,800
    eye=np.array([6.45,1.50,8.50]);yaw=math.atan2(3.1,-1.4);pitch=.075
    if bathroom:
        eye=np.array([7.42,1.66,3.32]);yaw=math.atan2(.40,-1.0);pitch=.08
    if overview:
        width,height=1200,1200
        eye=np.array([7.33,1.50,3.00]);yaw=math.atan2(.35,-1.0);pitch=.22
    if pier:
        width,height=1200,900
        eye=np.array([8.80,1.50,2.80]);yaw=-.30;pitch=.14
    if kitchen_overview:
        width,height=1400,1200
        eye=np.array([3.6,7.4,11.7]);target=np.array([7.35,.5,6.35]);delta=eye-target
        yaw=math.atan2(delta[2],delta[0]);pitch=math.atan2(delta[1],math.hypot(delta[0],delta[2]))
    room_bounds=None
    if room:
        width,height=1200,1000
        presets={
            'bedroom':([-2,6.3,7.5],[2.35,.45,4.1],[-.56,4.78,2.68,5.63]),
            'study':([-1.1,6.0,11],[3.7,.45,7.2],[1.0,5.94,5.63,9.32]),
            'entry':([10.6,6.4,5.4],[6.7,.5,1.9],[4.77,9.32,-.21,3.36]),
            'all':([14.6,16.5,17.6],[4.1,.35,4.65],None),
            'dog':([1.55,1.1,5.5],[.77,.3,5.13],None),
            'plant':([6.9,.88,8.4],[7.48,.61,7.89],None),
            'kitchen-wall':([8.45,1.75,7.38],[5.95,1.22,7.15],None),
            'bath-storage':([8.77,1.55,2.58],[7.40,1.36,3.50],None),
            'bath-wc':([7.75,1.16,2.70],[8.68,.45,3.20],None),
        }
        source,target,room_bounds=presets[room];eye=np.array(source);delta=eye-np.array(target)
        yaw=math.atan2(delta[2],delta[0]);pitch=math.atan2(delta[1],math.hypot(delta[0],delta[2]))
    fwd=np.array([-math.cos(pitch)*math.cos(yaw),-math.sin(pitch),-math.cos(pitch)*math.sin(yaw)])
    right=np.cross(fwd,[0,1,0]);right/=np.linalg.norm(right)
    up=np.cross(right,fwd);basis=np.array([right,up,fwd]);f=height/2/math.tan((1.35 if room=='bath-storage' else .78 if room else .75 if kitchen_overview else 1.25 if pier else 1.50 if overview else 1.10)/2)
    rgb=np.ones((height,width,3),dtype=np.float32)*([.018,.026,.045] if evening else [.92,.90,.85])
    depth=np.full((height,width),np.inf)
    ambient_path=Path(__file__).parent/'kitchen-ambient.json'
    ambient=json.loads(ambient_path.read_text()) if ambient_path.exists() else None
    atlas=np.frombuffer(base64.b64decode(ambient['pixels']),dtype=np.uint8).reshape(ambient['height'],ambient['width'])/255 if ambient else None
    def contact(p,normal):
        if atlas is None:return np.ones(p.shape[:-1])
        if normal[1]>.98 and .0<float(p[0,0,1])<.07:plane_id=4 if len(ambient['planes'])>4 else 0
        elif normal[0]<-.98 and abs(float(p[0,0,0])-9.058)<.025:plane_id=1
        elif normal[0]>.98 and abs(float(p[0,0,0])-5.945)<.025:plane_id=2
        elif normal[2]>.98 and abs(float(p[0,0,2])-4.197)<.025:plane_id=3
        else:return np.ones(p.shape[:-1])
        plane=ambient['planes'][plane_id];delta=p-plane['origin']
        u=np.array(plane['u']);v=np.array(plane['v'])
        uv=np.stack((delta@u/(u@u),delta@v/(v@v)),axis=-1)
        inside=np.all((uv>=0)&(uv<=1),axis=-1)
        resolution=256 if plane_id==4 else 128
        coords=np.clip(uv*resolution-.5,0,resolution-1);ix=np.floor(coords).astype(int);f=coords-ix
        row,col=(2,0) if plane_id==4 else divmod(plane_id,2);x=ix[...,0]+128*col;y=ix[...,1]+128*row
        x1=np.minimum(x+1,128*col+resolution-1);y1=np.minimum(y+1,128*row+resolution-1)
        values=(atlas[y,x]*(1-f[...,0])+atlas[y,x1]*f[...,0])*(1-f[...,1])+(atlas[y1,x]*(1-f[...,0])+atlas[y1,x1]*f[...,0])*f[...,1]
        return np.where(inside,values,1)
    lights=m.SCENE_LIGHTS; lp=np.array([l['position'] for l in lights]);lc=np.array([l['color'] for l in lights]);power=np.array([l['power'] for l in lights])
    blockers=[]
    for raw in m.ELEMENTS:
        e=m.resolved(raw)
        if e['category'] not in ('wall','door'):continue
        if e['category']=='door':e={**e,**e['closed']}
        blockers.append(e)
    bc=np.array([b['position'] for b in blockers]);bs=np.array([b['size'] for b in blockers])/2
    ba=np.array([b.get('rotation',0) for b in blockers]);co=np.cos(ba);si=np.sin(ba)
    light_direction=np.array([-.35,.70,.72]);light_direction/=np.linalg.norm(light_direction)
    def illumination(points,normals):
        # Vertex-sampled counterpart of the live fragment shader, for offline QA.
        if not evening:
            kitchen=(points[:,0]>-.55)&(points[:,0]<9.09)&(points[:,2]>-.05)&(points[:,2]<8.79)
            diffuse=np.maximum(normals@light_direction,0)
            return np.repeat(np.where(kitchen,.67+.13*normals[:,1]+.15*diffuse,.66+.24*diffuse)[:,None],3,axis=1)
        delta=lp[None,:,:]-points[:,None,:];d2=np.sum(delta*delta,axis=2)
        lambert=np.maximum(np.sum(normals[:,None,:]*delta/np.maximum(np.sqrt(d2)[:,:,None],1e-9),axis=2),0)
        start=points+normals*.006
        ro=start[:,None,None,:]-bc[None,None,:,:]
        direction=lp[None,:,None,:]-start[:,None,None,:]
        o=np.stack((ro[...,0]*co-ro[...,2]*si,np.broadcast_to(ro[...,1],ro[...,0].shape),ro[...,0]*si+ro[...,2]*co),axis=-1)
        d=np.stack((direction[...,0]*co-direction[...,2]*si,np.broadcast_to(direction[...,1],direction[...,0].shape[:-1]+(len(co),)),direction[...,0]*si+direction[...,2]*co),axis=-1)
        safe=np.where(np.abs(d)>.000001,d,.000001)
        t0=(-bs-o)/safe;t1=(bs-o)/safe
        enter=np.max(np.minimum(t0,t1),axis=-1);leave=np.min(np.maximum(t0,t1),axis=-1)
        blocked=np.any((leave>np.maximum(enter,.001))&(enter<.998)&(leave>.001),axis=-1)
        strength=power[None,:]/(.45+d2)*(.12+.88*lambert)
        strength=np.where(blocked|(strength<.009),0,strength)
        ambient=np.broadcast_to([.065,.078,.105],points.shape) if evening else np.repeat((.66+.24*np.maximum(normals@light_direction,0))[:,None],3,axis=1)
        return ambient+strength@lc*(1 if evening else .30)
    meshes={shape:fn() for shape,fn in [('box',m.cube_geometry),('cylinder',m.cylinder_geometry),('ceiling',m.ceiling_geometry),('hexagon',m.hexagon_geometry)]}
    def grain_noise(p):
        cell=np.floor(p);f=p-cell;f=f*f*(3-2*f)
        values=[]
        for offset in ((0,0),(1,0),(0,1),(1,1)):
            h=np.sin((cell+offset)@np.array([127.1,311.7]))*43758.5453
            values.append(h-np.floor(h))
        return (values[0]*(1-f[...,0])+values[1]*f[...,0])*(1-f[...,1])+(values[2]*(1-f[...,0])+values[3]*f[...,0])*f[...,1]
    for raw in m.ELEMENTS:
        e=m.resolved(raw)
        if e.get('rawOnly'):continue
        if cabinet_open and e.get('towelPress'):e={**e,'detail':{**e['detail'],'press':e['towelPress']}}
        if cabinet_open and e.get('cabinetMotion'):
            motion=e['cabinetMotion'];a=motion['angle'];p=motion['pivot'];dx=e['position'][0]-p[0];dz=e['position'][2]-p[2]
            e={**e,'position':[p[0]+dx*math.cos(a)+dz*math.sin(a),e['position'][1],p[2]-dx*math.sin(a)+dz*math.cos(a)],'rotation':e.get('rotation',0)+a}
        if e['category']=='door':e={**e,**e['closed']}
        if room_bounds:
            x0,x1,z0,z1=room_bounds
            if e['position'][0]+e['size'][0]/2<x0 or e['position'][0]-e['size'][0]/2>x1 or e['position'][2]+e['size'][2]/2<z0 or e['position'][2]-e['size'][2]/2>z1:continue
        if room and room not in ('dog','plant','bath-storage','bath-wc'):
            if e['category'] in ('ceiling','window') or 'CeilingLight' in e['name']:continue
            if e['category'] in ('wall','finish_wall','door'):
                base=e['position'][1]-e['size'][1]/2;height_cut=min(e['size'][1],1.35-base)
                if height_cut<=0:continue
                e={**e,'position':[e['position'][0],base+height_cut/2,e['position'][2]],'size':[e['size'][0],height_cut,e['size'][2]]}
        if kitchen_overview:
            if e['position'][0]+e['size'][0]/2<5.89 or e['position'][2]+e['size'][2]/2<4.17:continue
            if e['category'] in ('ceiling','window'):continue
            if e['category'] in ('wall','finish_wall','door'):
                base=e['position'][1]-e['size'][1]/2;height_cut=min(e['size'][1],1.35-base)
                if height_cut<=0:continue
                e={**e,'position':[e['position'][0],base+height_cut/2,e['position'][2]],'size':[e['size'][0],height_cut,e['size'][2]]}
        mat=m.MATERIALS[e['material']]
        if mat['color'][3]<.5:continue
        verts,normals,indices=detail_mesh(e) if e.get('detail') else meshes.get(e['shape'],meshes['box'])
        a=e.get('rotation',0);c,s=math.cos(a),math.sin(a)
        rot=np.array([[c,0,s],[0,1,0],[-s,0,c]])
        world=(np.array(verts).reshape(-1,3)*e['size'])@rot.T+e['position']
        cam=(world-eye)@basis.T
        if np.max(cam[:,2])<.08:continue
        normals_local=np.array(normals).reshape(-1,3)/e['size']
        normals_local/=np.maximum(np.linalg.norm(normals_local,axis=1)[:,None],1e-9)
        normals_world=normals_local@rot.T
        sampled=illumination(world,normals_world)
        for ids in np.array(indices).reshape(-1,3):
            w=world[ids];normal=np.cross(w[1]-w[0],w[2]-w[0]);length=np.linalg.norm(normal)
            if length<1e-12:continue
            normal/=length
            if np.dot(normal,eye-w[0])<=0:continue
            points=[(cam[i],world[i],sampled[i]) for i in ids];clipped=[]
            for k,cur in enumerate(points):
                prev=points[k-1];inside=cur[0][2]>=.08;pin=prev[0][2]>=.08
                if inside!=pin:
                    t=(.08-prev[0][2])/(cur[0][2]-prev[0][2])
                    clipped.append(tuple(prev[j]+t*(cur[j]-prev[j]) for j in range(3)))
                if inside:clipped.append(cur)
            for k in range(1,len(clipped)-1):
                tri=[clipped[0],clipped[k],clipped[k+1]]
                q=np.array([p[0] for p in tri]);w=np.array([p[1] for p in tri])
                screen=q[:,:2]/q[:,2,None]*[f,-f]+[width/2,height/2]
                lo=np.maximum(np.floor(screen.min(axis=0)).astype(int),[0,0]);hi=np.minimum(np.ceil(screen.max(axis=0)).astype(int),[width-1,height-1])
                if np.any(hi<lo):continue
                xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
                a,b,c=screen;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(den)<1e-9:continue
                wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
                wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;wc=1-wa-wb
                inv=wa/q[0,2]+wb/q[1,2]+wc/q[2,2]
                z=1/np.maximum(inv,1e-12);ys=slice(lo[1],hi[1]+1);xs=slice(lo[0],hi[0]+1)
                mask=(wa>=-1e-6)&(wb>=-1e-6)&(wc>=-1e-6)&(z<depth[ys,xs])
                if not mask.any():continue
                p=(wa[:,:,None]*w[0]/q[0,2]+wb[:,:,None]*w[1]/q[1,2]+wc[:,:,None]*w[2]/q[2,2])*z[:,:,None]
                uv=p[:,:,[0,2]] if abs(normal[1])>.5 else p[:,:,[2,1]] if abs(normal[0])>.5 else p[:,:,[0,1]]
                pat=mat.get('pattern',0);texture=1
                if pat==1:
                    flow=grain_noise(uv*[14,.9]);texture=.96+.12*grain_noise(uv*[70,2])+.023*np.sin(uv[:,:,0]*380+9*flow+2*np.sin(uv[:,:,1]*3.7))+.025*np.sin(uv[:,:,0]*42+6*flow)
                if pat==2:texture=.985+.025*np.sin(uv[:,:,0]*1800)*np.sin(uv[:,:,1]*1800)+.014*np.sin(uv[:,:,0]*95)*np.sin(uv[:,:,1]*110)
                if pat==3:texture=.99+.017*np.sin(uv[:,:,0]*12+np.sin(uv[:,:,1]*15))+.012*np.sin(uv[:,:,1]*71+np.sin(uv[:,:,0]*33))
                values=np.array([v[2] for v in tri])
                local=(wa[:,:,None]*values[0]/q[0,2]+wb[:,:,None]*values[1]/q[1,2]+wc[:,:,None]*values[2]/q[2,2])*z[:,:,None]
                if not evening:local*=contact(p,normal)[...,None]
                value=np.array(mat['color'][:3])*(1 if pat==4 else local)
                out=value*np.asarray(texture)[...,None] if isinstance(texture,np.ndarray) else value
                if pat!=4:out=np.minimum(out,.6)+.4*(1-np.exp(-np.maximum(out-.6,0)/.4))
                rgb[ys,xs][mask]=out[mask] if isinstance(out,np.ndarray) and out.ndim==3 else out
                depth[ys,xs][mask]=z[mask]
    path=Path(__file__).parent/'renders'/((room+'-detail-check.png') if room else 'kitchen-detail-cutaway.png' if kitchen_overview else 'bathroom-pier-trial.png' if pier else 'bathroom-render-geometry.png' if overview else (('bathroom' if bathroom else 'kitchen')+('-evening-check.png' if evening else '-day-check.png')))
    if cabinet_open:path=path.with_stem(path.stem+'-open')
    Image.fromarray((np.clip(rgb,0,1)*255).astype('uint8')).save(path)
    print(path)


if __name__=='__main__':
    import sys
    render('--bathroom' in sys.argv,'--evening' in sys.argv,'--overview' in sys.argv,'--pier' in sys.argv,'--kitchen-overview' in sys.argv,sys.argv[sys.argv.index('--room')+1] if '--room' in sys.argv else None,'--cabinet-open' in sys.argv)
