"""Regression checks for the 22-item whole-apartment local revision."""
import math
import copy
import base64
import generate_model as m
import finish_review
finish_review.build=lambda api:None  # Isolate the earlier stage; current full scene has dedicated regression coverage.
import model_polish
import detail_refinement
detail_refinement.build=lambda api:None  # Isolate the previous 22-item revision.
from detail_geometry import mesh

build=model_polish.build;model_polish.build=lambda api:None
m.build_scene();before={e['name']:copy.deepcopy(m.resolved(e)) for e in m.ELEMENTS}
model_polish.build=build;m.build_scene()
after={e['name']:m.resolved(e) for e in m.ELEMENTS}
def node(prefix):return next(e for n,e in after.items() if n.startswith(prefix))
def edge(e,axis,sign):return e['position'][axis]+sign*e['size'][axis]/2

for prefix in ('BedroomRadiator','StudyWestRadiator','StudySouthRadiator','KitchenRadiator'):
    assert sum(n.startswith(prefix+'_Rib') for n in after)>=20
    assert sum(n.startswith(prefix+'_TopVent') for n in after)>=20
    assert node(prefix+'_Thermostat')
assert len(m.DOOR_OPENING_LIMITS)==4
assert all(90<=r['degrees']<=180 for r in m.DOOR_OPENING_LIMITS)
assert next(r for r in m.DOOR_OPENING_LIMITS if 'Entry' in r['name'])['degrees']==180
assert all(not r['baseline'] for r in m.DOOR_OPENING_LIMITS)
for e in after.values():
    assert all(math.isfinite(x) and x>0 for x in e['size']),e['name']
    assert all(math.isfinite(x) for x in e['position']),e['name']
    if e.get('detail'):
        p,n,i=mesh(e);assert all(math.isfinite(v) for v in p+n),e['name']
        assert max(abs(v) for v in p)<=.50001,e['name']
assert node('Wall_StudyHingePier')['size'][1]==2.8
for e in after.values():
    if e['name'].startswith('StudyHingePierFinish'):assert edge(e,1,1)>=2.75
for n,e in before.items():
    if e['category']=='finish_wall' and not n.startswith('Facade_') and abs(edge(e,1,1)-2.75)<.004:
        assert edge(after[n],1,1)>2.75,n
    if e['category']=='wall' and not n.startswith('Wall_StudyHingePier'):
        assert after[n]['position']==e['position'] and after[n]['size']==e['size'],n
for e in after.values():
    if e['name'].startswith('Facade_'):
        core=e['name'][len('Facade_'):].rsplit('_',1)[0]
        assert after[core]['material']=='facade_terracotta'
assert m.MATERIALS['facade_terracotta']['pattern']==8
for prefix,wp,along in [('BedroomOutdoorBasket','Window_BedroomWest_glass',2),('KitchenOutdoorBasket','Window_KitchenSouth_glass',0)]:
    lo=min(edge(e,along,-1) for n,e in after.items() if n.startswith(prefix))
    assert abs(lo-edge(node(wp),along,-1))<1e-7
assert len([n for n in after if n.startswith('ExteriorSill_')])==4
assert all(e['material']=='exterior_graphite' for n,e in after.items() if n.startswith(('ExteriorFrame_','ExteriorSill_','ExteriorReveal')))
assert all(e['material']=='window_white' for n,e in after.items() if n.startswith('Window_') and '_frame_' in n)
top=node('FreezerWorktop_');mw=node('MicrowaveBody_')
assert top['material']=='kitchen_stone' and abs(edge(top,1,1)-edge(mw,1,-1))<.004
assert abs(mw['position'][0]-before[mw['name']]['position'][0]-.025)<1e-7
for i in (1,3,4):
    seat=node(f'Furniture_DiningChair{i}_seat_');cushion=node(f'Furniture_DiningChair{i}_SeatCushion')
    assert seat['material']=='kitchen_oak' and cushion['material']=='kitchen_seat'
    assert cushion['size'][0]<seat['size'][0] and cushion['size'][1]<.04
assert not any(n.startswith('KitchenSofa_AccentPillow') for n in after)
for prefix in ('SinkUnit','EndUnit','FreezerBase','KitchenUpperSink'):
    assert node(prefix+'_001')['material']=='kitchen_oak'
    assert node(prefix+'_IvoryFacade')['material']=='kitchen_ivory'
    assert node(prefix+'_001')['size']==before[prefix+'_001']['size']
assert sum(n.startswith('Kettle_HandleCurve') for n in after)==14
left=node('KitchenFridgeNiche_Side_001');right=node('KitchenFridgeNiche_Side_002')
assert left['material']=='kitchen_oak'
assert left['position']==before[left['name']]['position'] and left['size']==before[left['name']]['size']
assert node('Fridge_001')['position']==before['Fridge_001']['position']
assert node('Fridge_001')['size']==before['Fridge_001']['size']
upper=node('KitchenUpperFridge_001');facade=node('KitchenUpperFridge_IvoryFacade')
assert upper['size']==before[upper['name']]['size']
vertices,_,_=mesh(upper)
xs=[upper['position'][0]+x*upper['size'][0] for x in vertices[::3]]
assert min(xs)>edge(left,0,1)+.0009 and max(xs)<edge(right,0,-1)-.0009
assert edge(facade,0,-1)>edge(left,0,1)+.0019
assert edge(facade,0,1)<edge(right,0,-1)-.0019
assert not any(n.startswith('EntryCoatTopBasket') for n in after)
assert node('EntryRouter_Body') and node('EntryElectricalPanel_Door') and node('LaundryApplianceFacade')
assert node('KitchenAC_001')['detail']['radius']==.045
assert node('PetFeedingBowl')['material']=='polish_steel'
assert node('PetFeedingStandLeg')
for e in after.values():
    if e['category']=='finish_floor' and e['material']!='screed' and not any(t in e['name'] for t in ('Bath','FloorTile')):
        assert e['material'].startswith('kitchen_floor'),e['name']
assert edge(node('BathBase_'),2,1)<edge(node('BathApronBacking_'),2,-1)
photos=[e for e in after.values() if e.get('artwork')]
assert len(photos)==4
assert len(base64.b64decode(m.ARTWORK['pixels']))==m.ARTWORK['width']*m.ARTWORK['height']*3
assert not any(n.startswith('BedroomArt') and '_Art_' in n for n in after)
assert not any(n.startswith('KitchenArt_Dune') for n in after)
print('Passed: radiator details, maximum door clearances, continuous facade/reveals, ceiling junctions, kitchen/entry/pet details, unified dry floors, tub/apron clearance and raster artworks.')
