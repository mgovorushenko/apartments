"""Plan registration, independent fixture counts and preservation of furniture."""
from collections import Counter
import math
import generate_model as m
import scene_lighting
from lighting_plan import position,inverse,SPOTS

build=scene_lighting.build
scene_lighting.build=lambda api:setattr(api,'SCENE_LIGHTS',[])
m.build_scene();before={e['name']:m.resolved(e) for e in m.ELEMENTS}
scene_lighting.build=build
m.build_scene();after={e['name']:m.resolved(e) for e in m.ELEMENTS}
assert Counter(r['kind'] for r in m.LIGHTING_LAYOUT)=={'spot':40,'central':1,'sconce':4,'backlight':3}
assert Counter(r['room'] for r in m.LIGHTING_LAYOUT if r['kind']=='spot')=={
 'Kitchen':11,'Central':5,'Entry':4,'Laundry':2,'Bedroom':8,'Study':4,'Bath':6}
assert len(m.SCENE_LIGHTS)==57 and len(m.SCENE_LIGHTS)<64
for row in m.LIGHTING_LAYOUT:
 assert row['elements'] and all(n in after for n in row['elements'])
 assert any(l['fixture']==row['id'] for l in m.SCENE_LIGHTS),row['id']
 if row['kind'] not in ('spot','central'):continue
 x,_,z=row['position'];u,v=inverse(x,z)
 assert max(abs(a-b) for a,b in zip([u,v],row['sourcePixel']))<1e-8
 for name in row['elements']:
  e=after[name];assert abs(e['position'][0]-x)<1e-9 and abs(e['position'][2]-z)<1e-9
  assert e['position'][1]+e['size'][1]/2<=2.75
 for e in after.values():
  if e['category']!='wall':continue
  a=e.get('rotation',0);dx=x-e['position'][0];dz=z-e['position'][2]
  local=[dx*math.cos(a)-dz*math.sin(a),row['position'][1]-e['position'][1],dx*math.sin(a)+dz*math.cos(a)]
  assert not all(abs(q)<s/2-.001 for q,s in zip(local,e['size'])),(row['id'],e['name'])
ignore=('KitchenCeilingLight','RoomCeilingLight','BathCeilingLight','KitchenSconce','BedsideLeft_Light','BedsideRight_Light')
for name,e in before.items():
 if name.startswith(ignore):continue
 assert {k:v for k,v in after[name].items() if k!='lightingId'}=={k:v for k,v in e.items() if k!='lightingId'},('unrelated element changed',name)
assert not any(n.startswith(('KitchenCeilingLight','RoomCeilingLight','BathCeilingLight')) for n in after)
assert len([n for n in after if n.startswith('PlanSpot_') and '_Diffuser_' in n])==40
assert len([n for n in after if n.startswith('EntryMirror_LED')])==4
print('Passed: 40 separately registered spots, central light, 4 sconces, 3 backlights / 57 light samples; no missing sources, wall collisions or unrelated geometry edits.')
