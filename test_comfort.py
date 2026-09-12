"""User overrides after the PDF revision: furniture placement and dry-room skirting."""
import math
import generate_model as model

model.build_scene()
items=[model.resolved(e) for e in model.ELEMENTS]
def node(prefix):return next(e for e in items if e['name'].startswith(prefix))
def near(a,b):assert abs(a-b)<1e-5,(a,b)
def edges(e,axis):return [e['position'][axis]+s*e['size'][axis]/2 for s in (-1,1)]
assert not any(e['name'].startswith(('BedroomVanity','Furniture_BedroomReadingChair','PetBowl')) for e in items)
catalog={e['id']:e for e in model.FURNITURE_CATALOG}
assert 'bedroom-vanity' not in catalog and 'bedroom-chair' not in catalog
assert {'dog-bed','pet-feeding'}<=catalog.keys()
near(node('TV_')['position'][2],node('KitchenAC_')['position'][2])
table=node('Furniture_DiningTable_top_')
near(table['position'][0],6.675);near(table['size'][0],.9)
wall=edges(node('FinishBeige_KitchenWest_'),0)[1]
near(edges(table,0)[0]-wall,.30)
for i in (1,3,4):
    seat=node(f'Furniture_DiningChair{i}_seat_')
    near(math.hypot(*(seat['position'][a]-table['position'][a] for a in (0,2))),.49)
    # Rotated chair geometry stays on the room side of the west partition.
    for e in items:
        if e.get('inspectId')!=f'chair-{i}':continue
        a=e['rotation'];r=abs(math.cos(a))*e['size'][0]/2+abs(math.sin(a))*e['size'][2]/2
        assert e['position'][0]-r>wall
for e in items:
    if e['name'].startswith('PetFeeding'):
        assert 4.77<edges(e,0)[0]<edges(e,0)[1]<5.2
        assert 3.7<edges(e,2)[0]<edges(e,2)[1]<4.50
        assert e['category']=='furniture'
    if e['name'].startswith('Dog'):
        assert e['category']=='furniture'
        assert .1<edges(e,0)[0]<edges(e,0)[1]<1.4
        assert 4.7<edges(e,2)[0]<edges(e,2)[1]<5.6
for e in [e for e in items if e['name'].startswith('PetFeedingInset_')]:
    rim=next(r for r in items if r['name'].startswith('PetFeedingRim_') and r['position'][2]==e['position'][2])
    assert edges(e,1)[1]>edges(rim,1)[1],'water/food must remain visible above capped rim primitive'
skirting=[e for e in items if e['name'].startswith('Skirting_')]
assert len(skirting)>30
for e in skirting:
    near(e['size'][1],.04);near(min(e['size'][0],e['size'][2]),.008)
    near(edges(e,1)[0],model.FINISH_SETTINGS['dry_floor'])
    assert e['category']=='finish_wall'
    assert not (7.275<e['position'][0]<9.075 and 1.335<e['position'][2]<4.045),'no skirting in bathroom'
for room in ('Bedroom','Study','Entry','Kitchen','BathOuter'):
    assert any(room in e['name'] for e in skirting),room
print(f'Passed: bedroom pet corner, relocated bowls, aligned TV, tucked chairs and table, {len(skirting)} dry-room skirting segments.')
