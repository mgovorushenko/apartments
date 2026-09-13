"""Coarse diffuse-patch radiosity, evaluated offline into the existing light volumes.

Three diffuse bounces between floor, wall/door and ceiling patches. Luminance
reflectance only (no colour bleeding), structural visibility, no furniture GI.
"""
import math
import numpy as np

PATCH_SIZE=.70
BOUNCES=3
# Coarse, furniture-free room patches overestimate returned energy. Keep a
# conservative visual gain; this is an approximation rather than a lux model.
INDIRECT_GAIN=.45

def visibility(start,end,blockers):
    start=np.asarray(start);direction=np.asarray(end)-start
    blocked=np.zeros(len(direction),dtype=bool)
    for b in blockers:
        a=b.get('rotation',0);c,s=math.cos(a),math.sin(a)
        r=start-b['position'];h=np.array(b['size'])/2
        o=np.stack([c*r[:,0]-s*r[:,2],r[:,1],s*r[:,0]+c*r[:,2]],axis=1)
        d=np.stack([c*direction[:,0]-s*direction[:,2],direction[:,1],s*direction[:,0]+c*direction[:,2]],axis=1)
        safe=np.where(abs(d)>1e-8,d,1e-8)
        t0=(-h-o)/safe;t1=(h-o)/safe
        enter=np.minimum(t0,t1).max(axis=1);leave=np.maximum(t0,t1).min(axis=1)
        blocked|=(leave>np.maximum(enter,.001))&(enter<.998)&(leave>.001)
    return ~blocked

def inside(points,floors,blockers):
    mask=np.zeros(len(points),dtype=bool)
    for e in floors:
        p=np.array(e['position']);h=np.array(e['size'])/2
        mask|=(abs(points[:,0]-p[0])<h[0])&(abs(points[:,2]-p[2])<h[2])
    for e in blockers:
        p=np.array(e['position']);h=np.array(e['size'])/2;r=points-p
        a=e.get('rotation',0);c,s=math.cos(a),math.sin(a)
        local=np.stack([c*r[:,0]-s*r[:,2],r[:,1],s*r[:,0]+c*r[:,2]],axis=1)
        mask&=~np.all(abs(local)<h+.001,axis=1)
    return mask

def patches(api,blockers):
    elements=[api.resolved(e) for e in api.ELEMENTS]
    floors=[e for e in elements if e['name'].startswith('Finish_Floor')]
    finishes=[e for e in elements if e['category']=='finish_wall' and not e['name'].startswith('Facade_')]
    ps=[];ns=[];areas=[];albedos=[];kinds=[]
    def reflectance(material):
        rgb=api.MATERIALS[material]['color'][:3]
        return float(np.clip(np.dot(rgb,[.2126,.7152,.0722]),.12,.88))
    def panel(center,u,v,normal,material,kind):
        u=np.array(u);v=np.array(v);normal=np.array(normal);center=np.array(center)
        nu=max(1,math.ceil(np.linalg.norm(u)/PATCH_SIZE));nv=max(1,math.ceil(np.linalg.norm(v)/PATCH_SIZE))
        area=np.linalg.norm(np.cross(u,v))/(nu*nv)
        for i in range(nu):
            for j in range(nv):
                p=center+u*((i+.5)/nu-.5)+v*((j+.5)/nv-.5)+normal*.022
                if not inside(p[None,:],floors,blockers)[0]:continue
                mat=material
                if kind=='wall':
                    axis=int(np.argmax(abs(normal)));other=[k for k in range(3) if k!=axis]
                    candidates=[e for e in finishes if e['size'][axis]<.10 and
                      abs(e['position'][axis]-p[axis])<.08 and
                      all(abs(e['position'][k]-p[k])<=e['size'][k]/2+.001 for k in other)]
                    if candidates:mat=min(candidates,key=lambda e:abs(e['position'][axis]-p[axis]))['material']
                ps.append(p);ns.append(normal);areas.append(area);albedos.append(reflectance(mat));kinds.append(kind)
    for e in floors:
        x,_,z=e['position'];sx,_,sz=e['size']
        wet='Bath' in e['name'];y=api.FINISH_SETTINGS['wet_floor' if wet else 'dry_floor']
        panel([x,y,z],[sx,0,0],[0,0,sz],[0,1,0],'stone_gray' if wet else e['material'],'floor')
        panel([x,2.8-api.FINISH_SETTINGS['ceiling_drop'],z],[sx,0,0],[0,0,sz],[0,-1,0],'ceiling_white','ceiling')
    for e in blockers:
        p=np.array(e['position']);s=np.array(e['size']);a=e.get('rotation',0);c,t=math.cos(a),math.sin(a)
        rot=np.array([[c,0,t],[0,1,0],[-t,0,c]])
        low=max(.021,p[1]-s[1]/2);high=min(2.75,p[1]+s[1]/2)
        if high<=low:continue
        for axis in (0,2):
            other=2-axis
            for sign in (-1,1):
                n=np.zeros(3);n[axis]=sign;n=rot@n
                u=np.zeros(3);u[other]=s[other];u=rot@u
                center=p+n*s[axis]/2;center[1]=(low+high)/2
                panel(center,u,[0,high-low,0],n,e['material'],'wall')
    return np.array(ps),np.array(ns),np.array(areas),np.array(albedos),kinds,floors

def bake_indirect(api,blockers,points,origin,extent,fine_size):
    p,n,area,rho,kinds,floors=patches(api,blockers)
    count=len(p);direct=np.zeros((count,2));transfer=np.zeros((count,count))
    for light in api.SCENE_LIGHTS:
        upper=light['fixture'].startswith('spot-') or light['fixture']=='study-central'
        delta=np.array(light['position'])-p;d2=np.sum(delta**2,axis=1)
        cosine=np.maximum(np.sum(n*delta,axis=1)/np.maximum(np.sqrt(d2),1e-6),0)
        valid=(cosine>0)&(d2<36)&((p[:,1]<light['position'][1]) if upper else True)
        ids=np.flatnonzero(valid)
        direct[ids,0 if upper else 1]+=cosine[ids]*light['power']*(1.25 if upper else 1)/(.45+d2[ids])*visibility(p[ids],light['position'],blockers)
    # Receiving-row normalization bounds diffuse form factors and avoids energy
    # growth from close coarse patches. Every bounce remains linear per circuit.
    for j in range(count):
        delta=p[j]-p;d2=np.sum(delta**2,axis=1);unit=delta/np.maximum(np.sqrt(d2[:,None]),1e-6)
        receive=np.maximum(np.sum(n*unit,axis=1),0);emit=np.maximum(-unit@n[j],0)
        ids=np.flatnonzero((receive>0)&(emit>0)&(d2>1e-8))
        transfer[ids,j]=area[j]*receive[ids]*emit[ids]/(math.pi*np.maximum(d2[ids],area[j]/math.pi))*visibility(p[ids],p[j],blockers)
    transfer/=np.maximum(1,transfer.sum(axis=1))[:,None]
    outgoing=direct*rho[:,None];total=outgoing.copy()
    for _ in range(BOUNCES-1):
        outgoing=(transfer@outgoing)*rho[:,None];total+=outgoing
    # Coarse transport volume is interpolated offline to the existing 64×20×64
    # grid, so runtime texture size and lookup count remain unchanged.
    coarse_size=np.array([32,10,32]);nx,ny,nz=coarse_size
    zz,yy,xx=np.meshgrid(np.arange(nz),np.arange(ny),np.arange(nx),indexing='ij')
    q=origin+(np.stack([xx,yy,zz],axis=-1).reshape(-1,3)+.5)/coarse_size*extent
    valid=inside(q,floors,blockers);fields=np.zeros((len(q),6,2));coverage=np.zeros((len(q),6))
    for j in range(count):
        delta=p[j]-q;d2=np.sum(delta**2,axis=1);unit=delta/np.maximum(np.sqrt(d2[:,None]),1e-6)
        emit=np.maximum(-unit@n[j],0)
        ids=np.flatnonzero(valid&(emit>0)&(d2<64))
        factor=area[j]*emit[ids]/(math.pi*np.maximum(d2[ids],area[j]/math.pi))*visibility(q[ids],p[j],blockers)
        lobes=np.concatenate([np.maximum(unit[ids],0),np.maximum(-unit[ids],0)],axis=1)
        weights=factor[:,None]*lobes
        fields[ids]+=weights[:,:,None]*total[j];coverage[ids]+=weights
    fields/=np.maximum(1,coverage)[:,:,None]
    grid=fields.reshape((nz,ny,nx,6,2))
    coords=np.clip((points-origin)/extent*coarse_size-.5,0,coarse_size-1)
    lo=np.floor(coords).astype(int);hi=np.minimum(lo+1,coarse_size-1);f=coords-lo
    result=np.zeros((len(points),6,2));weight_sum=np.zeros(len(points))
    valid_grid=valid.reshape(nz,ny,nx)
    for a in (0,1):
        for b in (0,1):
            for c in (0,1):
                xyz=np.where([a,b,c],hi,lo);w=np.prod(np.where([a,b,c],f,1-f),axis=1)
                w*=valid_grid[xyz[:,2],xyz[:,1],xyz[:,0]]
                weight_sum+=w
                result+=grid[xyz[:,2],xyz[:,1],xyz[:,0]]*w[:,None,None]
    result/=np.maximum(weight_sum,1e-8)[:,None,None]
    result[~inside(points,floors,blockers)]=0
    result*=INDIRECT_GAIN
    stats=dict(patches=count,bounces=BOUNCES,gain=INDIRECT_GAIN,patchSize=PATCH_SIZE,coarseSize=coarse_size.tolist(),
               ceilingMeanExitance=total[np.array(kinds)=='ceiling'].mean(axis=0).round(5).tolist())
    return {'upper':result[:,:,0],'small':result[:,:,1]},stats
