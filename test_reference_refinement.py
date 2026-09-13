"""Reference palette, refrigerator surround and recognisable closed-lid WC."""
import generate_model as m
m.build_scene()
items=[m.resolved(e) for e in m.ELEMENTS]
def node(prefix):return next(e for e in items if e['name'].startswith(prefix))
def edge(e,a,s):return e['position'][a]+s*e['size'][a]/2
def near(a,b):assert abs(a-b)<1e-6,(a,b)
fridge=node('Fridge_001');near(fridge['size'][0],.60)
sides=sorted([e for e in items if e['name'].startswith('KitchenFridgeNiche_Side')],key=lambda e:e['position'][0])
assert len(sides)==2
near(edge(sides[0],0,-1),7.175);near(edge(sides[1],0,1),7.875)
near(edge(fridge,0,-1)-edge(sides[0],0,1),.032)
near(edge(sides[1],0,-1)-edge(fridge,0,1),.032)
for i,side in enumerate(sides):
 assert side['material']==('kitchen_oak' if i==0 else 'kitchen_ivory')
 near(edge(side,1,1),2.75)
near(edge(sides[1],0,1),edge(node('FreezerBase_001'),0,-1))
assert node('BathroomVanity_001')['material']==node('BathTallCabinetFacadePanel_')['material']=='kitchen_oak'
assert node('ToiletBowl_')['detail']['type']=='lathe'
assert node('ToiletSeatOpening_')['material']=='ceramic'
near(node('ToiletBowl_')['position'][2],node('ToiletInstallationEnclosure_')['position'][2])
assert edge(node('ToiletBowl_'),1,-1)>.17
assert edge(node('ToiletSeatOpening_'),1,-1)>edge(node('ToiletBowl_'),1,1)
print('Passed: 600 mm freestanding fridge / 700 mm surround, two 18 mm cheeks and 32 mm provisional gaps; shared bathroom oak; tapered suspended WC with separate white lid.')
