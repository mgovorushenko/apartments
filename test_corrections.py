"""Regression checks for enclosure alignment, clear doorway and furniture orientation."""
import math
import generate_model as model

model.build_scene()
elements=[model.resolved(e) for e in model.ELEMENTS]
def node(prefix):return next(e for e in elements if e['name'].startswith(prefix))
def near(a,b):assert abs(a-b)<1e-6,(a,b)

center=node('ToiletInstallationEnclosure_')['position'][2]
for prefix in ('ToiletWallHungBody_','ToiletBowl_','ToiletSeatOpening_','ToiletFlushPlate_'):
    near(node(prefix)['position'][2],center)

# Sample the clear central 80% of the study doorway through the full wall depth.
# Architectural solids must not occupy any of these points below the lintel.
door=node('Door_Study_')
cx,_,cz=door['closed']['position']
for sx in (-.4,-.2,0,.2,.4):
    for dz in (-.10,-.08,-.06,-.04,-.02,0,.02):
        for y in (.10,1,2):
            point=(cx+sx*door['size'][0],y,cz+dz)
            for e in elements:
                if e['category'] not in ('wall','finish_wall'):continue
                assert not all(abs(point[i]-e['position'][i])<e['size'][i]/2-1e-7 for i in range(3)),e['name']

table=node('Furniture_DiningTable_top_')['position']
for i in (1,3,4):
    seat=node(f'Furniture_DiningChair{i}_seat_')
    back=node(f'Furniture_DiningChair{i}_back_')
    # The chair's back must be on the side away from the centre of the table.
    dot=sum((back['position'][a]-seat['position'][a])*(table[a]-seat['position'][a]) for a in (0,2))
    # A centred, inward-facing chair has antiparallel back and table vectors.
    length=math.hypot(*(back['position'][a]-seat['position'][a] for a in (0,2)))*math.hypot(*(table[a]-seat['position'][a] for a in (0,2)))
    assert dot/length<-.999,(i,dot/length)
    dimensions=next(o['dimensionsMm'] for o in model.FURNITURE_CATALOG if o['id']==f'chair-{i}')
    assert dimensions[0]==420 and 420<=dimensions[1]<=430,dimensions

entry=node('Door_Entry_')
cx,cy,cz=entry['closed']['position']
assert entry['position'][2]<cz-.4,'entry must open outwards (negative Z)'
assert entry['position'][2]-entry['size'][0]/2<-.9
near(entry['closed']['rotation'],-math.pi)
assert abs(entry['rotation']-math.pi/2)<1e-6
for original in model.ELEMENTS:
    if original['name'].startswith('Door_Entry_'):
        assert original['position'][2]<original['closed']['position'][2]-.4
print('Passed: centred toilet and flush plate; clear study doorway; 3 inward chairs; outward entry door in rough and finished modes.')
