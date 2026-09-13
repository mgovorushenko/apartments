"""Approved kitchen composition: three chairs, lower opal sconce, art and TV."""
import generate_model as m
from lighting_plan import position,SCONCES

m.build_scene()
items=[m.resolved(e) for e in m.ELEMENTS]
def node(prefix):return next(e for e in items if e['name'].startswith(prefix))
def edge(e,axis,sign):return e['position'][axis]+sign*e['size'][axis]/2
def near(a,b):assert abs(a-b)<1e-6,(a,b)
seats=[e for e in items if e['name'].startswith('Furniture_DiningChair') and '_seat_' in e['name']]
assert len(seats)==3
assert not any(e['name'].startswith('Furniture_DiningChair2_') for e in items)
assert {o['id'] for o in m.FURNITURE_CATALOG if o['id'].startswith('chair-')}=={'chair-1','chair-3','chair-4'}
tv=node('TV_');ac=node('KitchenAC_')
near(tv['position'][1],1.228);near(tv['position'][2],ac['position'][2])
console=max(edge(e,1,1) for e in items if e['name'].startswith('TVConsole'))
assert .17<edge(tv,1,-1)-console<.20
assert edge(ac,1,-1)-edge(tv,1,1)>.6
shade=node('KitchenSconce_Shade');table=node('Furniture_DiningTable_top')
near(node('KitchenSconce_Plate')['position'][1],1.51);near(shade['position'][1],1.545);near(shade['position'][2],position(SCONCES['Kitchen'])[1])
assert shade['material']=='bedroom_render_white' and shade['detail']['type']=='lathe'
light=next(l for l in m.SCENE_LIGHTS if l['label']=='Бра у стола')
near(light['position'][1],shade['position'][1]-.096)
near(light['position'][0],shade['position'][0])
art=node('KitchenArt_Frame');sofa=node('KitchenSofa_Base');back=node('KitchenSofa_Back_')
near(art['position'][2],sofa['position'][2]);near(art['size'][2],1.0);near(art['size'][1],.55)
assert .20<edge(art,1,-1)-edge(back,1,1)<.25
for prefix in ('KitchenSofa_Base','KitchenSofa_Cushion','KitchenSofa_BackPad','KitchenSofa_SeatPad'):
 assert node(prefix)['material']=='kitchen_sofa_sage'
for prefix in ('KitchenUpperSink','FreezerBase','EndUnit'):
 assert node(prefix+'_001')['material']=='kitchen_oak'
 assert node(prefix+'_IvoryFacade')['material']=='kitchen_ivory'
assert node('TVConsole_001')['material']=='kitchen_oak'
assert node('TVConsole_Facade')['material']=='kitchen_ivory'
rgb=m.MATERIALS[node('KitchenSofa_Base')['material']]['color']
assert rgb[0]>rgb[1]>rgb[2] and min(rgb[:3])>.68
print('Passed: three chairs, 120 mm TV lift / 180 mm console gap, cylinder sconce anchored at 1.51 m, centred art, warm greige sofa and ivory cabinetry.')
