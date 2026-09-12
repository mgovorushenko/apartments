"""Pilot scope, bounded meshes, catalog dimensions and small static AO asset."""
import base64
import copy
import json
import math
from pathlib import Path
import generate_model as m
import kitchen_detail
from detail_geometry import mesh

build=kitchen_detail.build
kitchen_detail.build=lambda api:None
m.build_scene()
before={e['name']:copy.deepcopy(m.resolved(e)) for e in m.ELEMENTS}
before_catalog=copy.deepcopy(m.FURNITURE_CATALOG)
lights=copy.deepcopy(m.SCENE_LIGHTS)
kitchen_detail.build=build
m.build_scene()
after={e['name']:m.resolved(e) for e in m.ELEMENTS}
for name,e in before.items():
    if e['category']!='furniture' or name.startswith(('Bath','Toilet','Shower','Basin','Study','Bed','Entry','Hall','Laundry','ComputerDesk','Piano','Dog','PetFeeding')):
        assert after[name]==e,name
assert m.SCENE_LIGHTS==lights,'pilot must not add costly local lights'
catalog={o['id']:o for o in m.FURNITURE_CATALOG}
for o in before_catalog:
    if o['id'] in ('table','kitchen-sofa','tv-console','fridge','end-unit','sink-unit','dishwasher','oven','corner','freezer'):
        assert catalog[o['id']]['dimensionsMm'][:2]==o['dimensionsMm'][:2],o['id']
assert catalog['table']['dimensionsMm'][:2]==[900,900]
assert catalog['kitchen-sofa']['dimensionsMm'][:2]==[1500,900]
assert sum(n.startswith('Curtain_KitchenSouth_') and 'Track' not in n for n in after)==3
types=set();triangles=0
for e in after.values():
    if not e.get('detail'):continue
    types.add(e['detail']['type']);p,n,indices=mesh(e)
    assert len(p)==len(n) and len(p)%3==0
    assert all(math.isfinite(v) for v in p+n)
    assert max(abs(v) for v in p)<=.50001,(e['name'],max(abs(v) for v in p))
    assert all(0<=i<len(p)//3 for i in indices)
    for i in range(0,len(n),3):assert abs(math.hypot(*n[i:i+3])-1)<1e-7,e['name']
    triangles+=len(indices)//3
assert types=={'rounded','pillow','bow','lathe','curtain','rod','leaf','towel'}
assert triangles<230000,triangles
ambient=m.scene_data()['detailAmbient'];pixels=base64.b64decode(ambient['pixels'])
assert len(pixels)==ambient['width']*ambient['height']==131072
assert min(pixels)<160 and max(pixels)==255
root=Path(__file__).parent
assert len((root/'viewer-core.js').read_bytes())<100_000
print(f'Passed: kitchen pilot preserves other-room geometry, furniture widths, no extra lights, bounded meshes ({triangles} triangles), 3 kitchen panels, 128 KiB apartment AO atlas.')
