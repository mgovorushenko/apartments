"""Full current scene verification, including deliberate overrides of PDF depth."""
import copy
import math
import generate_model as m
import finish_review
from detail_geometry import mesh
build=finish_review.build;finish_review.build=lambda api:None
m.build_scene();before={e['name']:copy.deepcopy(m.resolved(e)) for e in m.ELEMENTS};lights=copy.deepcopy(m.SCENE_LIGHTS)
finish_review.build=build;m.build_scene();after={e['name']:m.resolved(e) for e in m.ELEMENTS}
def node(prefix):return next(e for n,e in after.items() if n.startswith(prefix))
def edge(e,a,sign):return e['position'][a]+sign*e['size'][a]/2
def near(a,b):assert abs(a-b)<1e-7,(a,b)
for n,e in after.items():
    assert e['material'] in m.MATERIALS,n
    assert all(math.isfinite(v) and v>0 for v in e['size']),n
    if e.get('detail'):
        p,normal,indices=mesh(e)
        assert all(math.isfinite(v) for v in p+normal),n
        assert max(abs(v) for v in p)<=.50001,n
    if e['category']=='wall':assert e==before[n],n
    if e['category']=='furniture' and m.MATERIALS[e['material']].get('pattern')==1:
        assert e['material']=='kitchen_oak',n
assert node('EntryMirrorCornerFinish')['material']=='wall_beige'
near(edge(node('EntryMirrorCornerFinish'),2,1),edge(node('FinishBeige_BathOuterWest_'),2,-1))
assert node('EntryWardrobeSlidingDoor')['material']=='kitchen_oak'
assert node('Kettle_001')['material']=='white'
for prefix in ('BedsideLeft_Light','BedsideRight_Light','KitchenSconce_','StudySconce_'):
    shade=node(prefix+'Shade');diff=node(prefix+'Diffuser')
    assert edge(diff,1,-1)>edge(shade,1,-1)+.009
    assert diff['size'][0]<shade['size'][0]*.9
assert len(lights)==len(m.SCENE_LIGHTS)
for old,new in zip(lights,m.SCENE_LIGHTS):
    near(new['power'],old['power']*(1.65 if old['fixture'].startswith('sconce-') else 1))
assert len([n for n in after if n.startswith('PianoWhiteKey')])==52
assert len([n for n in after if n.startswith('PianoBlackKey')])==36
assert len([n for n in after if n.startswith('PianoPedal_')])==3
assert len(node('GuitarBody')['detail']['rings'])>90
assert node('ComputerDesk')['size'][2]==.8
near(edge(node('ComputerDesk'),2,1),edge(before['ComputerDesk_001'],2,1))
assert next(e for e in m.FURNITURE_CATALOG if e['id']=='desk')['dimensionsMm']==[1400,800,780]
assert len([n for n in after if n.startswith('Furniture_Study_Caster')])==10
assert node('Furniture_Study_BackMesh')['material']=='review_mesh'
assert len([n for n in after if n.startswith('PetFeedingBowl')])==2
assert all(edge(e,1,1)>.32 and e['material']=='polish_steel' for n,e in after.items() if n.startswith('PetFeedingBowl'))
assert node('EntryMemoCork') and node('EntryMemoPhoto')
assert len([n for n in after if n.startswith('BathShelf_Base')])==2
assert all(e['size'][2]==.42 for n,e in after.items() if n.startswith('BathShelf_Base'))
assert node('BathShelf_Base')['position'][0]<7.5 and node('ShowerRiser')['position'][0]>9
assert node('TVConsole_001')['material']=='kitchen_oak'
assert len([n for n in after if n.startswith('TVConsole_Facade')])==3
assert all(e['material']=='kitchen_oak' for n,e in after.items() if 'Worktop' in n and before.get(n,{}).get('material')=='kitchen_stone')
assert node('KitchenBacksplashLong')['material']=='kitchen_stone'
assert node('LaundryUnifiedPull')['material']=='door_handle_satin' and node('LaundryUnifiedPull')['size'][0]>.02
for n,e in after.items():
    if n.startswith('WindowSill_'):assert e['material']=='stone_gray_1'
    if n.startswith('InteriorReveal'):assert e['material'] in ('wall_beige','study_sage','bedroom_render_blue')
assert all(r['degrees']==90 for r in m.DOOR_OPENING_LIMITS if any(t in r['name'] for t in ('Study','Bedroom')))
for prefix,wp,axis in [('BedroomOutdoorBasket','Window_BedroomWest_glass',2),('KitchenOutdoorBasket','Window_KitchenSouth_glass',0)]:
    members=[e for n,e in after.items() if n.startswith(prefix)]
    def half(e):return (abs(math.cos(e.get('rotation',0)))*e['size'][axis]+abs(math.sin(e.get('rotation',0)))*e['size'][2-axis])/2
    near(max(e['position'][axis]+half(e) for e in members),edge(node(wp),axis,1))
assert len([n for n in after if n.startswith('ExteriorWallWhiteTop')])>=10
planks=[e for n,e in after.items() if n.startswith('FloorPlank_')]
assert len(planks)>150
hall_mirrors=[e for n,e in after.items() if n.startswith('HallWardrobeSlidingDoor')]
assert len(hall_mirrors)==2 and all(e['material']=='bath_mirror' for e in hall_mirrors)
assert all(not e.get('noEdges',False) for e in planks), 'Individual board boundaries must remain visible'
for i in range(3):
    assert m.MATERIALS['kitchen_floor_'+str(i)] == m.MATERIALS['bedroom_render_floor_'+str(i)]
assert len({e['material'] for e in planks if abs(e['position'][0]-planks[0]['position'][0])<1e-6})>1, 'End-to-end boards need separate tones'
for r in [e for n,e in after.items() if n.startswith('Finish_Floor') and e['material'].startswith('kitchen_floor')]:
    assert any(edge(e,0,-1)>=edge(r,0,-1)-1e-7 and edge(e,0,1)<=edge(r,0,1)+1e-7 and edge(e,2,-1)>=edge(r,2,-1)-1e-7 and edge(e,2,1)<=edge(r,2,1)+1e-7 for e in planks),r['name']
near(edge(node('Curtain_KitchenSouth_LeftPanel'),0,-1),5.935)
near(edge(node('Curtain_KitchenSouth_RightPanel'),0,1),9.045)
print('Passed: coordinated oak, all dry-floor boards, 1400×800 desk, ergonomic chair, 88-key piano, smooth guitar, raised bowls, memo board, aligned baskets, recessed bright sconces, shelves, door limits and preserved surveyed walls.')
