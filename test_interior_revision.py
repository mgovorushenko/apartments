"""Regression checks for the 14-point local interior review."""
import math
import generate_model as m
from detail_geometry import mesh
m.build_scene();items=[m.resolved(e) for e in m.ELEMENTS]
def node(prefix):return next(e for e in items if e['name'].startswith(prefix))
def edge(e,a,s):return e['position'][a]+s*e['size'][a]/2
assert not any(e['name'].startswith('Dog') and not e['name'].startswith('DogBed') for e in items)
assert len([e for e in items if e['name'].startswith('DogBed')])==2
assert not any(e['name'].startswith('Bed_Pillow_') for e in items)
assert node('Bed_Cover_')['detail']['type']=='coverlet'
assert not any(e['name'].startswith(('Bed_AccentPillow','Bed_CenterPillow')) for e in items)
assert node('Bed_Cover_')['size'][0]>node('Bed_Mattress_')['size'][0]
assert edge(node('KitchenBacksplashReturn'),0,1)>=edge(node('KitchenBacksplashLong'),0,-1)
assert m.FINISH_MITER_COUNT>=24
for e in items:
    if e['category']=='finish_wall' and (e.get('detail') or {}).get('type')=='miter':
        p,n,indices=mesh(e)
        assert len(indices)==36 and max(abs(v) for v in p)<=.500001
        # Every corner stitch has a diagonal edge in its plan polygon.
        poly=e['detail']['outline']
        assert any(abs(a[0]-b[0])>1e-5 and abs(a[1]-b[1])>1e-5 for a,b in zip(poly,poly[1:]+poly[:1]))
wall=node('Wall_StudyEastReturn');trim=node('DoorCasing_Study_B_Right')
assert edge(trim,0,1)<edge(wall,0,-1)-.015
for e in items:
    if not e['name'].startswith('DoorCasing_Study'):continue
    for wall in items:
        if wall['category']=='wall':assert not all(min(edge(e,a,1),edge(wall,a,1))-max(edge(e,a,-1),edge(wall,a,-1))>1e-6 for a in range(3))
handles=[e for e in items if e['category']=='door_hardware']
assert len(handles)==24
for e in handles:
    room=e['name'].split('_')[1];leaf=node('Door_'+room+'_')
    for closed in (False,True):
        h={**e,**e['closed']} if closed else e
        d={**leaf,**leaf['closed']} if closed else leaf
        assert h['rotation']==d['rotation']
        dx,dz=h['position'][0]-d['position'][0],h['position'][2]-d['position'][2]
        a=d['rotation'];normal=dx*math.sin(a)+dz*math.cos(a)
        assert abs(normal)>d['size'][2]/2
        assert abs(h['position'][1]-1.015)<1e-5
assert all(abs(l['power']-.65*1.65)<1e-8 for l in m.SCENE_LIGHTS if l['fixture'].startswith('sconce-bedside'))
print('Passed: 24+ miter corners, clear study casings, continuous splash, two pillows and cover, empty pet bed, hardware on both sides of all leaves.')
