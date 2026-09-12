"""Casings on both sides of all three interior doors; openings remain clear."""
import generate_model as model

model.build_scene()
elements=[model.resolved(e) for e in model.ELEMENTS]
trims=[e for e in elements if e['name'].startswith('DoorCasing_')]
assert len(trims)==18
def edge(e,axis,sign):return e['position'][axis]+sign*e['size'][axis]/2
def near(a,b):assert abs(a-b)<.00011,(a,b)
for room in ('Bedroom','Study','Bathroom'):
    head=next(e for e in elements if e['name'].startswith('DoorHead_'+room+'_'))
    normal=0 if head['size'][0]<head['size'][2] else 2
    along=2 if normal==0 else 0
    jambs=sorted([e for e in elements if e['name'].startswith('DoorJamb_'+room+'_')],key=lambda e:e['position'][along])
    lo,hi=edge(jambs[0],along,1),edge(jambs[1],along,-1)
    for side,sign in [('A',-1),('B',1)]:
        parts={part:next(e for e in trims if e['name'].startswith(f'DoorCasing_{room}_{side}_{part}_')) for part in ('Left','Right','Top')}
        near(edge(parts['Left'],along,1),lo);near(edge(parts['Right'],along,-1),hi)
        near(edge(parts['Top'],1,-1),edge(head,1,-1))
        for part,e in parts.items():
            assert e['category']=='finish_wall' and e['material']=='door_ivory'
            near(e['size'][normal],.01)
            near(e['size'][1 if part=='Top' else along],.06)
            layer=model.FINISH_SETTINGS['tile_adhesive' if room=='Bathroom' and sign==1 else 'plaster_wallpaper']
            near(edge(e,normal,-sign),edge(head,normal,sign)+sign*layer)
            if part!='Top':
                near(edge(e,1,-1),model.FINISH_SETTINGS['wet_floor' if room=='Bathroom' and sign==1 else 'dry_floor'])
for e in [e for e in elements if e['name'].startswith('Skirting_')]:
    for trim in trims:
        assert not all(min(edge(e,a,1),edge(trim,a,1))-max(edge(e,a,-1),edge(trim,a,-1))>1e-6 for a in (0,1,2)),(e['name'],trim['name'])
assert not any('Entry' in e['name'] for e in trims)
print('Passed: 18 casing pieces / 3 doors / both faces; 60 × 10 mm; openings and skirting junctions clear.')
