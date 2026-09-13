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
    import sys
    legacy='--legacy-evening' in sys.argv
    m.build_scene()
    art_pixels=np.asarray(Image.open(Path(__file__).parent/m.ARTWORK['source']).convert('RGB'))/255
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
            'bedroom-concept':([2.05,1.60,5.48],[2.30,1.05,3.20],None),
            'study-workplace':([4.30,1.65,7.30],[2.33,1.02,8.48],None),
            'study-interior':([5.45,1.60,6.20],[2.60,1.22,7.55],None),
            'study-piano':([1.85,1.60,8.40],[5.40,1.10,6.90],None),
            'bedroom':([-2,6.3,7.5],[2.35,.45,4.1],[-.56,4.78,2.68,5.63]),
            'study':([-1.1,6.0,11],[3.7,.45,7.2],[1.0,5.94,5.63,9.32]),
            'entry':([10.6,6.4,5.4],[6.7,.5,1.9],[4.77,9.32,-.21,3.36]),
            'all':([14.6,16.5,17.6],[4.1,.35,4.65],None),
            'exterior':([-5.5,5.4,14.9],[3.7,1.1,5.0],None),
            'dog':([1.55,1.1,5.5],[.77,.3,5.13],None),
            'plant':([6.9,.88,8.4],[7.48,.61,7.89],None),
            'kitchen-wall':([8.45,1.75,7.38],[5.95,1.22,7.15],None),
            'bath-storage':([8.77,1.55,2.58],[7.40,1.36,3.50],None),
            'bath-wc':([7.75,1.16,2.70],[8.68,.45,3.20],None),
            'bedroom-interior':([3.70,1.62,5.25],[2.05,1.0,3.2],None),
            'study-door':([4.35,1.65,7.10],[5.16,1.70,5.67],None),
            'ceiling-corner':([6.55,1.55,6.95],[5.90,2.52,5.64],None),
            'fridge-niche':([6.65,1.50,5.60],[7.23,2.35,4.50],None),
            'chair-joinery':([7.45,.36,7.12],[6.25,.43,6.18],None),
            'laundry-fronts':([6.85,1.60,.68],[8.43,1.45,.63],None),
            'study-decor':([3.80,1.60,8.50],[3.40,1.40,5.76],None),
            'coat-details':([6.65,1.32,.70],[5.90,1.15,.41],None),
            'bath-shelves':([8.95,1.62,2.20],[7.34,1.59,1.70],None),
            'pet-board':([6.15,1.20,4.85],[4.96,.95,4.12],None),
            'entry-mirror-corner':([6.20,1.55,.80],[7.18,1.5,1.30],None),
        }
        source,target,room_bounds=presets[room];eye=np.array(source);delta=eye-np.array(target)
        yaw=math.atan2(delta[2],delta[0]);pitch=math.atan2(delta[1],math.hypot(delta[0],delta[2]))
    fwd=np.array([-math.cos(pitch)*math.cos(yaw),-math.sin(pitch),-math.cos(pitch)*math.sin(yaw)])
    right=np.cross(fwd,[0,1,0]);right/=np.linalg.norm(right)
    up=np.cross(right,fwd);basis=np.array([right,up,fwd]);f=height/2/math.tan((1.3 if room=='bedroom-concept' else 1.35 if room=='bath-storage' else .78 if room else .75 if kitchen_overview else 1.25 if pier else 1.50 if overview else 1.10)/2)
    rgb=np.ones((height,width,3),dtype=np.float32)*([18/255,20/255,23/255] if evening else [235/255,235/255,230/255])
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
    light_direction=np.array([-.35,.70,.72]);light_direction/=np.linalg.norm(light_direction)
    def illumination(points,normals):
        # Vertex-sampled counterpart of the live fragment shader, for offline QA.
        if not evening:
            kitchen=(points[:,0]>-.55)&(points[:,0]<9.09)&(points[:,2]>-.05)&(points[:,2]<8.79)
            diffuse=np.maximum(normals@light_direction,0)
            return np.repeat(np.where(kitchen,.67+.13*normals[:,1]+.15*diffuse,.66+.24*diffuse)[:,None],3,axis=1)
        from bake_lighting import sample
        import sys
        energy=sample(baked,points,normals,upper='--small-only' not in sys.argv and '--lights-off' not in sys.argv,small='--upper-only' not in sys.argv and '--lights-off' not in sys.argv)
        if not legacy and '--small-only' not in sys.argv and '--lights-off' not in sys.argv:
            energy-=.25*sample(baked,points,normals,upper=True,small=False)
        return np.array([.004,.005,.008])+energy[:,None]*[1,.94,.85]
    baked=json.loads((Path(__file__).parent/'lighting-bake.json').read_text()) if evening else None
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
        if e['category'] in ('door','door_hardware'):e={**e,**e['closed']}
        if room_bounds:
            x0,x1,z0,z1=room_bounds
            if e['position'][0]+e['size'][0]/2<x0 or e['position'][0]-e['size'][0]/2>x1 or e['position'][2]+e['size'][2]/2<z0 or e['position'][2]-e['size'][2]/2>z1:continue
        if room and room not in ('dog','plant','bath-storage','bath-wc','bedroom-interior','bedroom-concept','study-door','ceiling-corner','exterior','fridge-niche','chair-joinery','laundry-fronts','study-decor','coat-details','study-workplace','study-piano','bath-shelves','pet-board','entry-mirror-corner'):
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
                if pat==8:
                    brick=uv/[.26,.075];brick[:,:,0]+=(np.floor(brick[:,:,1])%2)*.5;frac=brick-np.floor(brick)
                    joint=np.minimum(np.minimum(frac[:,:,0],1-frac[:,:,0]),np.minimum(frac[:,:,1],1-frac[:,:,1]))<.035
                    texture=np.where(joint,1.22,.91+.15*grain_noise(np.floor(brick))+.035*grain_noise(uv*90))
                values=np.array([v[2] for v in tri])
                local=(wa[:,:,None]*values[0]/q[0,2]+wb[:,:,None]*values[1]/q[1,2]+wc[:,:,None]*values[2]/q[2,2])*z[:,:,None]
                # Large ceiling triangles need per-pixel volume sampling;
                # vertex-only interpolation creates artificial dark triangles.
                if evening and e['category'] in ('ceiling','wall','finish_wall'):
                    local[mask]=illumination(p[mask],np.tile(normal,(np.count_nonzero(mask),1)))
                if not evening:local*=(1+.55*(contact(p,normal)-1))[...,None]
                elif not legacy:local*=(1+.30*(contact(p,normal)-1))[...,None]
                import sys
                is_upper=e['name'].startswith(('PlanSpot_','PlanCentral_'))
                emitter_off=evening and ('--lights-off' in sys.argv or ('--small-only' in sys.argv and is_upper) or ('--upper-only' in sys.argv and not is_upper))
                albedo=np.array(mat['color'][:3])
                if pat==8 and normal[1]>.5:albedo=np.array([.95,.945,.93]);texture=1.0
                if e.get('artwork'):
                    a=e['artwork'];along=a['along'];sign=a['sign']*(-1 if a['axis']==0 else 1)
                    ratio=e['size'][along]/e['size'][1]/a.get('ratio',1);u=.5+(p[:,:,along]-e['position'][along])/e['size'][along]*sign
                    v=.5-(p[:,:,1]-e['position'][1])/e['size'][1]
                    if ratio>1:v=.5+(v-.5)/ratio
                    else:u=.5+(u-.5)*ratio
                    ox,oy,sx,sy=a.get('region',[0,0,1,1]);u=ox+u*sx;v=oy+v*sy
                    ix=np.clip((u*(art_pixels.shape[1]-1)).astype(int),0,art_pixels.shape[1]-1)
                    iy=np.clip((v*(art_pixels.shape[0]-1)).astype(int),0,art_pixels.shape[0]-1)
                    albedo=art_pixels[iy,ix]
                if evening and not legacy and (pat!=4 or emitter_off):albedo=srgb_to_linear(albedo)
                value=albedo*(1 if pat==4 and not emitter_off else local)
                out=value*np.asarray(texture)[...,None] if isinstance(texture,np.ndarray) else value
                if pat!=4 or emitter_off:
                    out=((np.maximum(out,0)/(1+np.maximum(out,0)))**(1/2.2) if legacy else evening_display(out)) if evening else np.minimum(out,.6)+.4*(1-np.exp(-np.maximum(out-.6,0)/.4))
                rgb[ys,xs][mask]=out[mask] if isinstance(out,np.ndarray) and out.ndim==3 else out
                depth[ys,xs][mask]=z[mask]
    path=Path(__file__).parent/'renders'/((room+'-detail-check.png') if room else 'kitchen-detail-cutaway.png' if kitchen_overview else 'bathroom-pier-trial.png' if pier else 'bathroom-render-geometry.png' if overview else (('bathroom' if bathroom else 'kitchen')+('-evening-check.png' if evening else '-day-check.png')))
    if cabinet_open:path=path.with_stem(path.stem+'-open')
    import sys
    if '--upper-only' in sys.argv:path=path.with_stem(path.stem+'-upper')
    if '--small-only' in sys.argv:path=path.with_stem(path.stem+'-small')
    if '--lights-off' in sys.argv:path=path.with_stem(path.stem+'-off')
    if legacy:path=path.with_stem(path.stem+'-legacy')
    Image.fromarray((np.clip(rgb,0,1)*255).astype('uint8')).save(path)
    print(path)

def srgb_to_linear(c):
    c=np.asarray(c)
    return np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4)

def evening_display(linear_color):
    c=np.maximum(linear_color,0)
    c=c/(1+np.sum(c*[.2126,.7152,.0722],axis=-1,keepdims=True))
    return np.where(c<.0031308,c*12.92,1.055*c**(1/2.4)-.055)


if __name__=='__main__':
    import sys
    render('--bathroom' in sys.argv,'--evening' in sys.argv,'--overview' in sys.argv,'--pier' in sys.argv,'--kitchen-overview' in sys.argv,sys.argv[sys.argv.index('--room')+1] if '--room' in sys.argv else None,'--cabinet-open' in sys.argv)
