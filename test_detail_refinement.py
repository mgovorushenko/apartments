"""Current scene: 10 requested joinery/decor corrections and unchanged plan."""
import copy
import math
import generate_model as m
import finish_review
finish_review.build=lambda api:None  # Isolate the earlier stage; current full scene has dedicated regression coverage.
import detail_refinement
from detail_geometry import mesh

build=detail_refinement.build;detail_refinement.build=lambda api:None
m.build_scene();before={e['name']:copy.deepcopy(m.resolved(e)) for e in m.ELEMENTS}
lights=copy.deepcopy(m.SCENE_LIGHTS)
detail_refinement.build=build;m.build_scene()
after={e['name']:m.resolved(e) for e in m.ELEMENTS}
def node(prefix):return next(e for n,e in after.items() if n.startswith(prefix))
def edge(e,a,sign):return e['position'][a]+sign*e['size'][a]/2
floor=m.FINISH_SETTINGS['dry_floor']
for n,e in after.items():
    if n.startswith('Furniture_DiningChair') and '_leg_' in n:
        seat=node(n.split('_leg_')[0]+'_seat_')
        assert abs(edge(e,1,-1)-floor)<1e-8
        assert edge(e,1,1)>edge(seat,1,-1)
    if e['category'] in ('wall','door','window','floor','ceiling'):
        assert e==before[n],n
    if e.get('detail'):
        p,normal,indices=mesh(e)
        assert all(math.isfinite(v) for v in p+normal),n
        assert max(abs(v) for v in p)<=.500001,n
assert abs(edge(node('Bed_Frame_'),1,-1)-floor)<1e-8
assert edge(node('Bed_Frame_'),1,1)==edge(before['Bed_Frame_001'],1,1)
assert m.SKIRTING_MITER_COUNT>=20
for n,e in after.items():
    if not n.startswith('Skirting_') or not e.get('detail'):continue
    poly=e['detail']['outline'];diag=0
    for a,b in zip(poly,poly[1:]+poly[:1]):
        dx=(a[0]-b[0])*e['size'][0];dz=(a[1]-b[1])*e['size'][2]
        if abs(dx)>1e-7 and abs(dz)>1e-7:
            assert abs(abs(dx)-abs(dz))<1e-7,n;diag+=1
    assert diag,n
step=node('StudyReturnStepFinish');assert step['material']=='study_sage'
assert abs(edge(step,1,-1)-floor)<1e-8
facades=[e for n,e in after.items() if n.startswith('LaundryUnifiedFacade')]
assert len(facades)==4 and len({edge(e,0,-1) for e in facades})==1
assert sorted(round(e['size'][1],3) for e in facades)==[.734,.734,1.824,1.824]
assert not any(n.startswith(('LaundryStorage_Handle','LaundryUpperStorage_Handle','LaundryApplianceFacade')) for n in after)
for prefix in ('KitchenSconce','StudySconce'):
    shade=node(prefix+'_Shade');assert shade['material']=='bedroom_render_white'
    assert shade['size']==[.11,.145,.11] and shade['detail']['type']=='lathe'
assert len(lights)==len(m.SCENE_LIGHTS)
for record in m.LIGHTING_LAYOUT:
    assert all(n in after for n in record['elements']),record['id']
photos=[e for e in after.values() if e.get('artwork')]
assert len(photos)==3 and len({tuple(e['artwork']['region']) for e in photos})==3
for e in photos:
    p,_,_=m.cube_geometry();uv=m.artwork_uv(e,p)
    x,y,w,h=e['artwork']['region']
    assert all(x-1e-9<=u<=x+w+1e-9 for u in uv[::2])
    assert all(y-1e-9<=v<=y+h+1e-9 for v in uv[1::2])
assert not any(n.startswith('BedroomArtSouth') for n in after)
assert node('GuitarBody')['material']=='dark' and node('GuitarHead')['material']=='dark'
vase=node('KitchenCoffeeDecor_Vase');table=node('Furniture_DiningTable_top')
assert abs(edge(vase,1,-1)-edge(table,1,1))<1e-8
assert abs(vase['position'][0]-table['position'][0])<.1
assert sum(n.startswith('EntryCoatShoeLace') for n in after)==16
assert sum(n.startswith('EntryCoatButton') for n in after)==10
print('Passed: connected chair legs, grounded bed, 45° skirting, study step, aligned laundry fronts, matching sconces, three distinct artworks, detailed clothes/shoes, black guitar and relocated plant.')
