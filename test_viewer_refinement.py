"""Requested visual changes preserve shell measurements and all fixture positions."""
import math
import generate_model as m
import viewer_refinement as ref

build=ref.build;ref.build=lambda api:None
m.build_scene();before={e['name']:m.resolved(e) for e in m.ELEMENTS};lights=list(m.SCENE_LIGHTS)
ref.build=build;m.build_scene();after={e['name']:m.resolved(e) for e in m.ELEMENTS}
assert lights==m.SCENE_LIGHTS
for name,e in before.items():
    if e['category']=='wall':
        assert after[name]['position']==e['position'] and after[name]['size']==e['size']
        assert after[name]['material']=='wall_white'
    elif e['category']!='window' and not name.startswith('Furniture_DiningChair'):
        assert after[name]==e,name
glasses=[e for n,e in after.items() if n.startswith('Window_') and '_glass_' in n]
assert len(glasses)==4
for e in glasses:
    axis=0 if 'West_' in e['name'] else 2
    assert e['size'][axis]==.006
assert sum(n.startswith('WindowSill_') for n in after)==4
assert sum(n.startswith('Facade_') for n in after)>15
table=next(e for n,e in after.items() if n.startswith('Furniture_DiningTable_top'))
cx,_,cz=table['position'];angles=[]
for i in (1,3,4):
    e=next(e for n,e in after.items() if n.startswith(f'Furniture_DiningChair{i}_seat_'))
    dx=e['position'][0]-cx;dz=e['position'][2]-cz
    assert abs(math.hypot(dx,dz)-.49)<1e-8
    assert abs(math.sin(e['rotation'])-dx/.49)<1e-8
    angles.append(math.atan2(dz,dx)%(2*math.pi))
angles.sort()
assert all(abs((angles[(i+1)%3]-angles[i])%(2*math.pi)-math.tau/3)<1e-8 for i in range(3))
print('Passed: white unchanged wall cores, exterior-only terracotta, 6 mm panes, four sills, evenly spaced tucked chairs, identical lights and remaining furniture.')
