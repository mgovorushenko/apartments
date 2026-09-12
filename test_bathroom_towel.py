"""Geometric clearances only; no electrical installation certification."""
import generate_model as m
import bathroom_towel
import math

build = bathroom_towel.build
bathroom_towel.build = lambda api: None
m.build_scene()
before = {e['name']:m.resolved(e) for e in m.ELEMENTS}
bathroom_towel.build = build
m.build_scene()
items = [m.resolved(e) for e in m.ELEMENTS]
for e in items:
    if e['name'] in before:
        old = before[e['name']]
        for key in ('position','size','rotation','material','shape'):
            assert e[key] == old[key], (e['name'],key)

def node(prefix):return next(e for e in items if e['name'].startswith(prefix))
def edge(e,a,s):
    angle=e.get('rotation',0)
    extent=e['size'][1]/2 if a==1 else (abs(math.cos(angle))*e['size'][a]+abs(math.sin(angle))*e['size'][2 if a==0 else 0])/2
    return e['position'][a]+s*extent
rail=[e for e in items if e['name'].startswith('BathTowelWarmer')]
towel=[e for e in items if e['name'].startswith('BathTowelDrape')]
def bound(parts,a,s):return (min if s<0 else max)(edge(e,a,s) for e in parts)
casing=node('DoorCasing_Bathroom_B_Right_')
cab=[e for e in items if e['name'].startswith('BathTallCabinet')]
assert len(towel)==4
assert all(e.get('detail',{}).get('type')=='towel' for e in towel)
assert len([e for e in rail if 'Upright' in e['name']])==3
assert abs(bound(rail,1,-1)-m.FINISH_SETTINGS['wet_floor']-.55)<.0001
assert abs(bound(rail,1,1)-bound(rail,1,-1)-1.20)<.0001
left_gap=bound(rail,2,-1)-edge(casing,2,1)
right_gap=bound(cab,2,-1)-bound(rail,2,1)
assert abs(left_gap-right_gap)<1e-8
assert abs(bound(towel,2,1)-bound(towel,2,-1)-.47)<1e-8
assert abs(bound(towel,2,-1)-edge(casing,2,1)-(bound(cab,2,-1)-bound(towel,2,1)))<1e-8
assert casing['size'][2]==.06 and casing['size'][0]==.01
# The fully closed main façade now overlaps the towels vertically: the sweep
# solver must restrict it, rather than assuming a permanently clear opening.
facades=[e for e in cab if 'Facade' in e['name'] or '_Handle_' in e['name']]
assert any(edge(e,1,-1)<bound(towel,1,-1) and edge(e,1,1)>bound(towel,1,1) for e in facades)
assert len([e for e in cab if 'OpenShelf' in e['name']])==4
assert not any('Reveal' in e['name'] or 'EndJoint' in e['name'] for e in cab)
gap=bound(cab,2,-1)-bound(rail+towel,2,1)
assert gap>.012,gap
# Exclude collisions against every existing solid box (touching wall is allowed).
for e in rail+towel:
    for other in before.values():
        if other.get('rawOnly') or other.get('rotation',0) or other['shape']!='box':continue
        if other['category']=='door':continue
        overlap=[min(edge(e,a,1),edge(other,a,1))-max(edge(e,a,-1),edge(other,a,-1)) for a in range(3)]
        assert min(overlap)<.00011,(e['name'],other['name'],overlap)
card=next(c for c in m.FURNITURE_CATALOG if c['id']=='bath-towel-warmer')
assert card['dimensionsMm']==[185,100,1200],card
assert card['source'] is None
assert all(e['category']=='furniture' for e in rail+towel)
assert m.CABINET_MOTION['towelSizeMm']==[700,1400]
print('Passed: centred 185 x 100 x 1200 warmer; nominal 700 x 1400 towels / 470 mm gathered envelope; side clearances',round(gap*1000,2),'mm. Cabinet opening requires collision limit.')
