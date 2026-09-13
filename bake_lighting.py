"""Static directional irradiance volumes. Baking happens at build time, not on camera movement.

Six normal directions per group; open/closed door variants. 15 cm voxels,
trilinear sampling, direct plus coarse diffuse indirect light, no photometric/lux claims.
"""
import base64
import json
import hashlib
from functools import lru_cache
from pathlib import Path
import numpy as np

ORIGIN=np.array([-.7,0.,-.3])
EXTENT=np.array([10.2,2.8,9.8])
SIZE=(64,20,64)

def signature(api):
    geometry=[api.resolved(e) for e in api.ELEMENTS if e['category'] in ('wall','door','finish_wall','finish_floor','ceiling')]
    return hashlib.sha256(Path(__file__).read_bytes()+Path(__file__).with_name('indirect_lighting.py').read_bytes()+json.dumps([geometry,api.SCENE_LIGHTS,api.MATERIALS],sort_keys=True).encode()).hexdigest()

def ensure(api,path):
    path=Path(path)
    if path.exists() and json.loads(path.read_text()).get('signature')==signature(api):return
    bake(api,path)

def bake(api,path):
    nx,ny,nz=SIZE
    zz,yy,xx=np.meshgrid(np.arange(nz),np.arange(ny),np.arange(nx),indexing='ij')
    points=ORIGIN+(np.stack([xx,yy,zz],axis=-1).reshape(-1,3)+.5)/SIZE*EXTENT
    variants={};indirect_stats={}
    for closed in (False,True):
        blockers=[]
        for raw in api.ELEMENTS:
            e=api.resolved(raw)
            if e['category'] not in ('wall','door'):continue
            if closed and e['category']=='door':e={**e,**e['closed']}
            blockers.append(e)
        fields={'upper':np.zeros((len(points),6)),'small':np.zeros((len(points),6))}
        for light in api.SCENE_LIGHTS:
            lp=np.array(light['position']);delta=lp-points;d2=np.sum(delta**2,axis=1)
            upper=light['fixture'].startswith('spot-') or light['fixture']=='study-central'
            valid=(d2<36)&((points[:,1]<lp[1]) if upper else True)
            ids=np.flatnonzero(valid);start=points[ids];direction=delta[ids]
            blocked=np.zeros(len(ids),dtype=bool)
            for b in blockers:
                a=b.get('rotation',0);c,s=np.cos(a),np.sin(a)
                rot=np.array([[c,0,-s],[0,1,0],[s,0,c]])
                o=(start-b['position'])@rot.T;d=direction@rot.T;half=np.array(b['size'])/2
                safe=np.where(abs(d)>1e-8,d,1e-8)
                t0=(-half-o)/safe;t1=(half-o)/safe
                enter=np.minimum(t0,t1).max(axis=1);leave=np.maximum(t0,t1).min(axis=1)
                blocked|=(leave>np.maximum(enter,.001))&(enter<.998)&(leave>.001)
            strength=light['power']*(1.25 if upper else 1)/(.45+d2[ids])
            strength[blocked]=0
            n=direction/np.maximum(np.sqrt(d2[ids,None]),1e-6)
            lobes=np.concatenate([np.maximum(n,0),np.maximum(-n,0)],axis=1)
            fields['upper' if upper else 'small'][ids]+=strength[:,None]*(.12+.88*lobes)
        from indirect_lighting import bake_indirect
        print('Baking reflected light:', 'closed doors' if closed else 'open doors',flush=True)
        indirect,stats=bake_indirect(api,blockers,points,ORIGIN,EXTENT,SIZE)
        for name in fields:fields[name]+=indirect[name]
        # Extend receiver values into adjacent solid cells. Trilinear filtering
        # at a finished face must not mix room light with black wall interiors.
        # Valid room cells are untouched; no blur crosses a room partition.
        from indirect_lighting import inside
        floors=[api.resolved(e) for e in api.ELEMENTS if e['name'].startswith('Finish_Floor')]
        valid=inside(points,floors,blockers).reshape(nz,ny,nx)
        # Three nearest-neighbour propagation passes, using only NumPy.
        # Track original source coordinates to compare real metric distances.
        coords=np.indices(valid.shape).transpose(1,2,3,0)
        nearest=coords.copy();dist=np.where(valid,0.,np.inf)
        spacing=EXTENT[::-1]/np.array(SIZE[::-1])
        for _ in range(3):
            prev=nearest.copy();prev_dist=dist.copy()
            for axis in range(3):
                for sign in (-1,1):
                    candidate=np.roll(prev,sign,axis=axis)
                    distance=np.sum(((candidate-coords)*spacing)**2,axis=-1)
                    distance[~np.isfinite(np.roll(prev_dist,sign,axis=axis))]=np.inf
                    boundary=[slice(None)]*3;boundary[axis]=0 if sign==1 else -1
                    distance[tuple(boundary)]=np.inf
                    improve=distance<dist;dist[improve]=distance[improve];nearest[improve]=candidate[improve]
        extend=(~valid)&(dist<.30**2)
        for field in fields.values():
            grid=field.reshape(nz,ny,nx,6)
            grid[extend]=grid[tuple(nearest[extend].T)]
        indirect_stats['closed' if closed else 'open']=stats
        encoded={}
        for name,field in fields.items():
            for sign,part in [('positive',field[:,:3]),('negative',field[:,3:])]:
                pixels=np.round(np.sqrt(np.clip(part/4,0,1))*255).astype('uint8')
                encoded[name+'_'+sign]=base64.b64encode(pixels.tobytes()).decode()
        variants['closed' if closed else 'open']=encoded
    result=dict(signature=signature(api),size=SIZE,origin=ORIGIN.tolist(),extent=EXTENT.tolist(),scale=4,variants=variants,indirect=indirect_stats,
                note='Direct + three coarse diffuse bounces from floors/walls/ceilings. Static 15 cm directional grid; two circuits and door states. Luminance-only transport, structural shadows; no furniture GI or lux calculation.')
    Path(path).write_text(json.dumps(result,separators=(',',':')))
    return result

@lru_cache(maxsize=8)
def decoded(encoded,size):
    return np.frombuffer(base64.b64decode(encoded),dtype='uint8').reshape((*size[::-1],3))/255

def sample(data,points,normals,closed=True,upper=True,small=True):
    """CPU counterpart of four texture lookups for verification."""
    size=np.array(data['size']);receiver=points+normals*.08;receiver[:,1]=np.minimum(receiver[:,1],2.57)
    uv=(receiver-data['origin'])/data['extent']
    q=np.clip(uv*size-.5,0,size-1);lo=np.floor(q).astype(int);hi=np.minimum(lo+1,size-1);f=q-lo
    energy=np.zeros(len(points))
    variant=data['variants']['closed' if closed else 'open']
    for group,enabled in [('upper',upper),('small',small)]:
        if not enabled:continue
        for sign in ('positive','negative'):
            grid=decoded(variant[group+'_'+sign],tuple(size))
            values=np.zeros((len(points),3))
            for a in (0,1):
                for b in (0,1):
                    for c in (0,1):
                        xyz=np.where([a,b,c],hi,lo);weight=np.prod(np.where([a,b,c],f,1-f),axis=1)
                        values+=grid[xyz[:,2],xyz[:,1],xyz[:,0]]*weight[:,None]
            n=np.maximum(normals,0) if sign=='positive' else np.minimum(normals,0)
            energy+=4*np.sum(values**2*n**2,axis=1)
    energy[np.any((uv<0)|(uv>1),axis=1)]=0
    return energy

if __name__=='__main__':
    import generate_model as m
    m.build_scene();bake(m,Path(__file__).with_name('lighting-bake.json'));print('Baked upper/small light, open/closed doors.')
