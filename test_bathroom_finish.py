"""Tile sizes in final metres, deliberate cut pieces, preserved openings/fixtures."""
import math
import generate_model as m
import finish_review
finish_review.build=lambda api:None  # Isolate the earlier stage; current full scene has dedicated regression coverage.
import bathroom_finish
import model_polish
model_polish.build=lambda api:None  # Test this build stage before the later whole-model review.

build=bathroom_finish.build
bathroom_finish.build=lambda api:None
m.build_scene()
before={e['name']:m.resolved(e) for e in m.ELEMENTS}
bathroom_finish.build=build
m.build_scene()
after={e['name']:m.resolved(e) for e in m.ELEMENTS}
for n,e in before.items():
    if e['category'] in ('wall','door','floor','window','ceiling') or n.startswith(('BathTallCabinet','BathTowelWarmer','ToiletBowl','ToiletWallHung','ToiletFlushPlate')):
        for k in ('position','size','rotation'):assert after[n].get(k)==e.get(k),(n,k)
assert m.TILE_LAYOUT
for tile in m.TILE_LAYOUT:
    a,b,c,d=tile['bounds'];fw,fh=[v/1000 for v in tile['formatMm']]
    assert 0<b-a<=fw+.00001 and 0<d-c<=fh+.00001,tile
    assert tile['jointMm']==2
    e=after[tile['name']]
    assert e['noEdges']
    if e['name'].startswith('BathInstallationTileTop'):
        assert tile['formatMm']==[1200,600]
    elif tile['axis']==1:
        assert tile['formatMm']==[600,600]
        assert abs(e['position'][1]+e['size'][1]/2-m.FINISH_SETTINGS['wet_floor'])<1e-8
    elif tile['staggerMm']:
        assert tile['formatMm']==[200,1200]
    else:assert tile['formatMm']==[600,1200]
reference=m.TILE_REFERENCE
starter=reference['starterBounds']
floor_tiles=[t for t in m.TILE_LAYOUT if t['name'].startswith('FloorTile')]
assert len([t for t in floor_tiles if all(abs(a-b)<1e-9 for a,b in zip(t['bounds'],starter))])==1,'full starter at installation/vent corner'
assert abs(starter[1]-starter[0]-.60)<1e-9 and abs(starter[3]-starter[2]-.60)<1e-9
enclosure=before['ToiletInstallationEnclosure_001']
assert abs(reference['corner'][0]-(enclosure['position'][0]-enclosure['size'][0]/2))<1e-9
vent=next(e for n,e in before.items() if n.startswith('Tile_VentFront_'))
assert abs(reference['corner'][1]-(vent['position'][2]-vent['size'][2]/2))<1e-9
assert all(abs(reference['corner'][i]-.002-starter[1+2*i])<1e-9 for i in range(2))
for tile in floor_tiles:
 a,b,c,d=tile['bounds'];ix,iz=tile['gridCell'];ox,oz=reference['gridOrigin']
 assert ox+ix*.602-1e-9<=a<b<=ox+ix*.602+.600+1e-9
 assert oz+iz*.602-1e-9<=c<d<=oz+iz*.602+.600+1e-9
 for other in floor_tiles:
  if other is tile:continue
  aa,bb,cc,dd=other['bounds']
  assert min(b,bb)-max(a,aa)<1e-9 or min(d,dd)-max(c,cc)<1e-9,'floor overlaps'
grey=[t for t in m.TILE_LAYOUT if t['axis']!=1 and not t['staggerMm']]
assert any(abs(t['bounds'][1]-t['bounds'][0]-.60)<1e-9 and abs(t['bounds'][3]-t['bounds'][2]-1.20)<1e-9 for t in grey)
for t in grey:
 a,b,c,d=t['bounds'];origin=reference['gridOrigin'][1 if t['axis']==0 else 0]
 # Each whole horizontal piece and row sits on the single floor-derived grid.
 if abs(b-a-.60)<1e-9:assert abs((a-origin)/.602-round((a-origin)/.602))<1e-8
 if abs(d-c-1.20)<1e-9:assert abs((c-m.FINISH_SETTINGS['wet_floor']-.002)/1.202-round((c-m.FINISH_SETTINGS['wet_floor']-.002)/1.202))<1e-8
wood=[t for t in m.TILE_LAYOUT if t['staggerMm']]
ys={round(t['bounds'][3],3) for t in wood if t['bounds'][3]<2.7}
assert any(abs(y-1.220)<.002 for y in ys) and any(abs(y-.420)<.002 for y in ys),ys
assert len([n for n in after if n.startswith('PlanSpot_Bath_') and '_Diffuser' in n])==6
assert len([n for n in after if n.startswith('BathMirrorLED')])==4
assert any(n.startswith('BathApronTile') for n in after)
assert any(n.startswith('BathInstallationTileTop') for n in after)
installation_tiles=[t for t in m.TILE_LAYOUT if t['name'].startswith('BathInstallationTile') and t['axis']!=1]
assert installation_tiles
for t in installation_tiles:
 assert abs(t['bounds'][2]-m.FINISH_SETTINGS['wet_floor']-.002)<1e-9
 assert abs(t['bounds'][3]-t['bounds'][2]-1.20)<1e-9,'one uncut vertical tile, no extra strip'
cap_top=max(e['position'][1]+e['size'][1]/2 for n,e in after.items() if n.startswith('BathInstallationTileTop'))
assert abs(cap_top-m.FINISH_SETTINGS['wet_floor']-1.203)<1e-9
core=after['ToiletInstallationEnclosure_001']
assert abs(core['position'][1]+core['size'][1]/2-installation_tiles[0]['bounds'][3])<1e-9
assert after['BathroomMirror_001']['position'][0]<before['BathroomMirror_001']['position'][0]
assert len(m.SCENE_LIGHTS)<=64
assert all(math.isfinite(v) for l in m.SCENE_LIGHTS for v in l['position']+[l['power']])
assert len([l for l in m.SCENE_LIGHTS if l['label']=='Подсветка зеркала'])==4
print('Passed:',len(m.TILE_LAYOUT),'tile pieces; vertical 600x1200 walls, full 600x600 starter, 602 mm grid and 400 mm wood stagger; preserved shell/niche, mirror + 6 plan spots;',len(m.SCENE_LIGHTS),'light samples.')
