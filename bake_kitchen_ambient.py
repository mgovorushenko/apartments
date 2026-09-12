"""Bake a small static contact-occlusion atlas for the kitchen pilot.

128² samples per receiver, 32 cosine-weighted rays, 0.85 m reach. Proxy boxes
approximate furniture occlusion; this is not a photometric/global-light bake.
Doors are excluded so opening them cannot leave an obsolete door shadow.
The viewer reads this once as R8 texture; no ray tracing occurs while navigating.
"""
import base64
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROOT=Path(__file__).resolve().parent
SIZE=128
PLANES=[
    dict(origin=[5.90,.019,4.10],u=[3.19,0,0],v=[0,0,4.69],normal=[0,1,0]),
    dict(origin=[9.058,0,4.10],u=[0,0,4.69],v=[0,2.76,0],normal=[-1,0,0]),
    dict(origin=[5.945,0,5.60],u=[0,0,3.19],v=[0,2.76,0],normal=[1,0,0]),
    dict(origin=[7.17,0,4.197],u=[1.92,0,0],v=[0,2.76,0],normal=[0,0,1]),
    dict(origin=[-.55,.019,-.05],u=[9.9,0,0],v=[0,0,9.40],normal=[0,1,0]),
]


def bake():
    import generate_model as m
    m.build_scene()
    prefixes=('KitchenSofa','Furniture_DiningChair','Furniture_DiningTable_top',
              'Furniture_DiningTable_pedestal','Furniture_CoffeeTable_top',
              'Furniture_CoffeeTable_pedestal','Fridge_001','FreezerBase_001',
              'KettleCorner_001','SinkUnit_001','Dishwasher_001','OvenUnit_001',
              'EndUnit_001','TVConsole_00','KitchenUpper','Bed_Frame','Bed_Mattress',
              'BedsideLeft_001','BedsideRight_001','BedroomWardrobe_001',
              'EntryWardrobeCase','HallWardrobeCase','LaundryStorageCase','LaundryWardrobe',
              'Washer_001','Dryer_001','BathTallCabinetCase','BathroomVanity_001',
              'ToiletWallHungBody','BathBase','BathSouth','BathNorth','BathWest','BathEast',
              'StudySofa','StudyOpenShelfSide','StudyOpenShelfBoard','ComputerDesk_001','DeskLeg',
              'Piano_001','PianoLowerBody','DogBedBase','EntryCoatBench')
    blockers=[]
    for raw in m.ELEMENTS:
        e=m.resolved(raw)
        if e.get('rawOnly'):continue
        if e['category']=='wall' or e['name'].startswith(prefixes) and 'Handle' not in e['name']:
            blockers.append(e)
    center=np.array([e['position'] for e in blockers]);half=np.array([e['size'] for e in blockers])/2
    angle=np.array([e.get('rotation',0) for e in blockers]);c=np.cos(angle);s=np.sin(angle)
    atlas=np.ones((SIZE*4,SIZE*2),dtype=np.uint8)*255
    for plane_id,plane in enumerate(PLANES):
        resolution=SIZE*2 if plane_id==4 else SIZE
        uv=(np.arange(resolution)+.5)/resolution;xx,yy=np.meshgrid(uv,uv)
        points=np.array(plane['origin'])+xx.reshape(-1,1)*plane['u']+yy.reshape(-1,1)*plane['v']
        normal=np.array(plane['normal']);points+=normal*.007
        tangent=np.array(plane['u']);tangent=tangent/np.linalg.norm(tangent);bitangent=np.cross(normal,tangent)
        result=np.zeros(len(points))
        for ray in range(32):
            radius=math.sqrt((ray+.5)/32);azimuth=ray*2.399963229728653
            direction=tangent*(radius*math.cos(azimuth))+bitangent*(radius*math.sin(azimuth))+normal*math.sqrt(1-radius*radius)
            for start in range(0,len(points),2048):
                ro=points[start:start+2048,None,:]-center[None,:,:]
                o=np.stack((ro[...,0]*c-ro[...,2]*s,ro[...,1],ro[...,0]*s+ro[...,2]*c),axis=-1)
                d=np.stack((direction[0]*c-direction[2]*s,np.full_like(c,direction[1]),direction[0]*s+direction[2]*c),axis=-1)
                safe=np.where(np.abs(d)>1e-8,d,1e-8)
                t0=(-half-o)/safe;t1=(half-o)/safe
                enter=np.max(np.minimum(t0,t1),axis=-1);leave=np.min(np.maximum(t0,t1),axis=-1)
                distance=np.min(np.where((leave>np.maximum(enter,.001))&(enter<.85),np.maximum(enter,0),.85),axis=1)
                result[start:start+len(distance)]+=np.maximum(0,1-distance/.85)**1.3/32
        shade=(255*(1-.58*result)).reshape(resolution,resolution).astype('uint8')
        shade=np.asarray(Image.fromarray(shade).filter(ImageFilter.GaussianBlur(.7)))
        if plane_id==4:atlas[SIZE*2:,:]=shade
        else:
            row,col=divmod(plane_id,2);atlas[row*SIZE:(row+1)*SIZE,col*SIZE:(col+1)*SIZE]=shade
    output=dict(width=SIZE*2,height=SIZE*4,planes=PLANES,pixels=base64.b64encode(atlas.tobytes()).decode(),
                note='Static apartment-floor + kitchen-wall contact occlusion; proxy furniture, doors excluded; not photometric.')
    (ROOT/'kitchen-ambient.json').write_text(json.dumps(output,separators=(',',':'))+'\n')
    Image.fromarray(atlas).save(ROOT/'renders'/'kitchen-ambient-atlas.png')
    print('Baked apartment ambient atlas: 256 × 512 R8, 32 rays/sample; range',int(atlas.min()),int(atlas.max()))


if __name__=='__main__':bake()
