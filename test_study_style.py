"""Study style isolation, desk fit and static accessory geometry."""
import copy
import generate_model as m
import finish_review
finish_review.build=lambda api:None  # Isolate the earlier stage; current full scene has dedicated regression coverage.
import study_style
import detail_refinement
detail_refinement.build=lambda api:None  # Later whole-home fixture reuse tested separately.
from detail_geometry import mesh

build = study_style.build
study_style.build = lambda api: None
m.build_scene()
before = {e['name']: copy.deepcopy(m.resolved(e)) for e in m.ELEMENTS}
lights = copy.deepcopy(m.SCENE_LIGHTS)
study_style.build = build
m.build_scene()
after = {e['name']: m.resolved(e) for e in m.ELEMENTS}
def node(prefix): return next(e for n, e in after.items() if n.startswith(prefix))
for name, e in before.items():
    if e['category'] in ('wall','floor','window','door','ceiling','finish_wall','finish_floor'):
        for key in ('position','size','rotation','detail'):
            assert after[name].get(key) == e.get(key), (name,key)
    if name.startswith(('Kitchen','Bath','Bed_','Bedroom','Piano','Guitar','TV','Entry','Hall')):
        assert after[name] == e, name
assert m.SCENE_LIGHTS == lights
assert not any(n.startswith('Curtain_Study') for n in after)
assert sum(n.startswith('StudyBlind_') and '_Fabric_' in n for n in after) == 2
assert node('StudySconce_Plate')['material'] == 'kitchen_ivory'
assert all(e['material']=='study_sage' for e in after.values()
           if e['name'].startswith('WallFinish_Study'))
desk = node('ComputerDesk_'); cx, cy, cz = desk['position']; sx, sy, sz = desk['size']
assert desk['size'] == before[desk['name']]['size']
assert desk['position'] == before[desk['name']]['position']
assert desk['material'] == 'study_white' and desk['detail']['type'] == 'desktop'
top = cy+sy/2
for e in after.values():
    if e['name'].startswith(('StudyPC_', 'Monitor1', 'Monitor2', 'StudyKeyboard_', 'StudyMouse')):
        x,y,z = e['position']; w,h,d = e['size']
        assert x-w/2 >= cx-sx/2-1e-8 and x+w/2 <= cx+sx/2+1e-8, e['name']
        assert z-d/2 >= cz-sz/2-1e-8 and z+d/2 <= cz+sz/2+1e-8, e['name']
        assert y-h/2 >= top-1e-8, e['name']
        assert e.get('inspectId'), e['name']
pc = node('StudyPC_Case')
assert pc['position'][0]+pc['size'][0]/2 < min(node('Monitor1_')['position'][0]-.27,node('Monitor2_')['position'][0]-.27)
assert sum(n.startswith('StudyKeyboard_Key') for n in after) == 63
assert node('StudyMouse_Body')['position'][0] < node('StudyKeyboard_Base')['position'][0]
rug = node('StudyRug'); chair = node('Furniture_Study_seat')
assert rug['position'][2]+rug['size'][2]/2 < chair['position'][2]-chair['size'][2]/2
p,n,indices = mesh(desk)
assert max(abs(v) for v in p) <= .500001
assert len(indices) < 900
print('Passed: study-only materials; exact shell/PDF desk; two blinds; rug clear of chair; PC on seated right; equipment fits desktop; 63 keycaps; no new lights.')
