"""The exposed north face of the study pier is finished, without filling the door."""
import generate_model as model

model.build_scene()
items=[model.resolved(e) for e in model.ELEMENTS]
def node(prefix):return next(e for e in items if e['name'].startswith(prefix))
def edge(e,a,s):return e['position'][a]+s*e['size'][a]/2
def near(a,b):assert abs(a-b)<1e-5,(a,b)
wall=node('Wall_StudyEastReturn_')
finish=node('FinishBeige_HallStudyReturnEnd_')
assert finish['category']=='finish_wall' and finish['material']=='wall_beige'
near(edge(finish,0,-1),edge(wall,0,-1))
near(edge(finish,0,1),edge(wall,0,1))
near(edge(finish,2,1),edge(wall,2,-1))
near(edge(finish,1,-1),model.FINISH_SETTINGS['dry_floor'])
near(edge(finish,1,1),2.8-model.FINISH_SETTINGS['ceiling_drop'])
assert finish['size'][2]>.014
assert edge(finish,0,-1)>=edge(node('DoorHead_Study_'),0,1)-1e-5
skirt=node('Skirting_FinishBeige_HallStudyReturnEnd_')
assert skirt['material']=='door_ivory'
assert edge(skirt,0,-1)>edge(finish,0,-1),'skirting is cut back to door casing'
near(edge(skirt,0,1),edge(finish,0,1))
print('Passed: study pier north face covered floor-to-ceiling; opening clear; skirting meets casing.')
