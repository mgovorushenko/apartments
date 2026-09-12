"""Static geometric sweep against actual warmer/towel triangles, in metres.

The façade is a rigid 18–20 mm slab, stopped by the metal warmer. Fabric uses
an illustrative displaced pose; hinge offsets and cloth physics are not simulated.
"""
import math
import numpy as np
from detail_geometry import mesh


def triangles(api,items):
    result=[]
    for e in items:
        p,_,idx=mesh(e) if e.get('detail') else api.cylinder_geometry(32) if e['shape']=='cylinder' else api.cube_geometry()
        p=np.asarray(p).reshape(-1,3)*e['size'];a=e.get('rotation',0);c,s=math.cos(a),math.sin(a)
        p=p@np.array([[c,0,-s],[0,1,0],[s,0,c]])+e['position']
        result.append(p[np.asarray(idx).reshape(-1,3)])
    return np.concatenate(result) if result else np.empty((0,3,3))


def intersects(tris,pivot,bounds,degrees,margin=.001):
    """Triangle/OBB SAT: conservative 1 mm buffer around the moving door slab."""
    if not len(tris):return False
    a=math.radians(degrees);c,s=math.cos(a),math.sin(a)
    p=tris-np.asarray(pivot)
    # Inverse of the positive Y rotation used by the live viewer.
    p=p@np.array([[c,0,s],[0,1,0],[-s,0,c]])
    lo=np.asarray(bounds[0]);hi=np.asarray(bounds[1]);center=(lo+hi)/2;half=(hi-lo)/2+margin
    p=p-center
    keep=np.all((p.max(axis=1)>=-half)&(p.min(axis=1)<=half),axis=1)
    p=p[keep]
    if not len(p):return False
    edges=np.roll(p,-1,axis=1)-p
    axes=[np.cross(edges[:,0],edges[:,1])]
    axes.extend(np.cross(edges[:,i],axis) for i in range(3) for axis in np.eye(3))
    valid=np.ones(len(p),dtype=bool)
    for axis in axes:
        projection=np.einsum('nvi,ni->nv',p,axis);radius=np.abs(axis)@half
        valid&=(projection.min(axis=1)<=radius+1e-12)&(projection.max(axis=1)>=-radius-1e-12)
    return bool(valid.any())


def first_limit(tris,pivot,bounds):
    if intersects(tris,pivot,bounds,0):return 0.0
    for angle in np.arange(.5,90.001,.5):
        if intersects(tris,pivot,bounds,angle):
            low,high=angle-.5,angle
            for _ in range(16):
                mid=(low+high)/2
                if intersects(tris,pivot,bounds,mid):high=mid
                else:low=mid
            return max(0,math.floor(low*100)/100)
    return 90.0


def build(api):
    elements=[api.resolved(e) for e in api.ELEMENTS]
    faces=[e for e in elements if e['name'].startswith('BathTallCabinetFacade') or e['name'].startswith('BathTallCabinet_Handle')]
    metal=triangles(api,[e for e in elements if e['name'].startswith('BathTowelWarmer')])
    cloth=triangles(api,[e for e in elements if e['name'].startswith('BathTowelDrape')])
    all_tris=np.concatenate([metal,cloth]);groups=[]
    for upper in (False,True):
        members=[e for e in faces if (e['position'][1]>2.27)==upper]
        lo=[min(e['position'][i]-e['size'][i]/2 for e in members) for i in range(3)]
        hi=[max(e['position'][i]+e['size'][i]/2 for e in members) for i in range(3)]
        pivot=[lo[0],0,lo[2]]
        bounds=[[lo[i]-pivot[i] for i in range(3)],[hi[i]-pivot[i] for i in range(3)]]
        fabric_contact=first_limit(all_tris,pivot,bounds);bare=first_limit(metal,pivot,bounds)
        limit=bare  # Cloth is movable; the rigid warmer is the opening stop.
        names={e['name'] for e in members}
        for e in api.ELEMENTS:
            if e['name'] in names:
                e['cabinetMotion']=dict(pivot=pivot,angle=math.radians(limit),bareAngle=math.radians(bare),group='upper' if upper else 'main')
        groups.append(dict(group='upper' if upper else 'main',limitDegrees=limit,bareDegrees=bare,fabricContactDegrees=fabric_contact,pivot=pivot,bounds=bounds))
    main=groups[0];angle=math.radians(main['limitDegrees']);normal=np.array([-math.sin(angle),0,-math.cos(angle)])
    for e in api.ELEMENTS:
        if not e['name'].startswith('BathTowelDrape'):continue
        r=api.resolved(e);a=r.get('rotation',0);c,s=math.cos(a),math.sin(a)
        local=[normal[0]*c-normal[2]*s,0,normal[0]*s+normal[2]*c]
        offset=float(normal@(np.asarray(r['position'])-main['pivot']))-.004
        e['towelPress']=dict(normal=local,offset=offset)
    api.CABINET_MOTION=dict(groups=groups,hingeSide='wall',towelSizeMm=[700,1400],gatheredPairWidthMm=470,clearanceMm=1,
        note='Ограничитель — жёсткий сушитель. Полотенца условно отводятся и приминаются фасадом; это не физический расчёт ткани. Петли и монтажные допуски не выбраны.')
