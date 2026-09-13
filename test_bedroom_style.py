"""Bedroom-only render palette, one coverlet, paired white cylindrical lights."""
import copy
import math
import generate_model as m
import finish_review
finish_review.build=lambda api:None  # Isolate the earlier stage; current full scene has dedicated regression coverage.
import bedroom_style
import detail_refinement
detail_refinement.build=lambda api:None  # Isolate the original bedroom stage.
from detail_geometry import mesh

build=bedroom_style.build;bedroom_style.build=lambda api:None
m.build_scene()
before={e['name']:copy.deepcopy(m.resolved(e)) for e in m.ELEMENTS}
catalog=copy.deepcopy(m.FURNITURE_CATALOG);lights=copy.deepcopy(m.SCENE_LIGHTS)
bedroom_style.build=build;m.build_scene()
after={e['name']:m.resolved(e) for e in m.ELEMENTS}
def node(prefix):return next(e for n,e in after.items() if n.startswith(prefix))
for name,e in before.items():
    if e['category'] in ('wall','floor','window','door','ceiling','finish_wall','finish_floor'):
        for k in ('position','size','rotation','detail'):assert after[name].get(k)==e.get(k),(name,k)
    if name.startswith(('Study','ComputerDesk','Monitor','DeskLeg','Piano','Guitar','Kitchen','Bath','Entry','Hall','TV')):
        assert after[name]==e,name
current={e['id']:e for e in m.FURNITURE_CATALOG}
for item in catalog:
    if item['id'] in ('bed','bedside-left','bedside-right','bedroom-wardrobe'):
        assert current[item['id']]['dimensionsMm'][:2]==item['dimensionsMm'][:2],item['id']
assert not any(n.startswith(('Bed_Pillow','Bed_Throw','Bed_HeadboardSlat','Bed_HeadboardRail')) for n in after)
cover=node('Bed_Cover_')
assert cover['material']=='bedroom_render_navy' and cover['detail']['type']=='coverlet'
assert sum(n.startswith('Bed_Cover') for n in after)==1
p,n,indices=mesh(cover)
assert all(math.isfinite(v) for v in p+n) and max(abs(v) for v in p)<=.500001
assert len(indices)//3<4000
assert all(after[e['name']]['position']==e['position'] for e in before.values() if e['name'].startswith('BedroomWardrobe'))
for e in after.values():
    if e['name'].startswith('BedroomWardrobe') and not any(k in e['name'] for k in ('Recess','Plinth')):
        assert e['material']=='bedroom_render_white'
    if e['name'].startswith(('BedsideLeft','BedsideRight')) and '_Light' not in e['name'] and '_Pull' not in e['name']:
        assert e['material']=='bedroom_render_oak'
assert len(m.SCENE_LIGHTS)==len(lights)
for old,new in zip(lights,m.SCENE_LIGHTS):
    if not old['fixture'].startswith('sconce-bedside'):assert new==old
    else:
        assert new['power']==old['power'] and new['position'][0]==old['position'][0]
for side in ('BedsideLeft','BedsideRight'):
    shell=node(side+'_LightShade');assert shell['detail']['type']=='lathe'
    assert shell['material']=='bedroom_render_white'
    assert shell['size']==[.11,.145,.11]
    assert node(side+'_LightSwitch')['lightingId']=='sconce-'+side.lower()
print('Passed: bedroom render palette, preserved shell/PDF furniture footprints, one navy cover, smooth headboard, milk-white sliding fronts, two cylinder lights on existing circuits.')
