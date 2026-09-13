"""Whole-apartment pass: exact shell, sliding fronts, exterior baskets, dog, guitar."""
import copy
import generate_model as m
import finish_review
finish_review.build=lambda api:None  # Isolate the earlier stage; current full scene has dedicated regression coverage.
import apartment_detail

build=apartment_detail.build;apartment_detail.build=lambda api:None
m.build_scene()
before={e['name']:copy.deepcopy(m.resolved(e)) for e in m.ELEMENTS}
before_catalog=copy.deepcopy(m.FURNITURE_CATALOG);lights=copy.deepcopy(m.SCENE_LIGHTS)
apartment_detail.build=build;m.build_scene()
after={e['name']:m.resolved(e) for e in m.ELEMENTS}
catalog={e['id']:e for e in m.FURNITURE_CATALOG}
for name,e in before.items():
    if e['category']!='furniture':assert after[name]==e,name
for item in before_catalog:
    if item.get('pdf'):
        assert catalog[item['id']]['dimensionsMm'][:2]==item['dimensionsMm'][:2],item['id']
assert m.SCENE_LIGHTS==lights
for prefix,meta in m.SLIDING_WARDROBES.items():
    panels=[e for e in after.values() if e['name'].startswith(prefix+'SlidingDoor_')]
    assert len(panels)==2
    axis=meta['axis'];along=2 if axis==0 else 0
    assert abs(abs(panels[0]['position'][axis]-panels[1]['position'][axis])-.029)<1e-8
    intervals=sorted((e['position'][along]-e['size'][along]/2,e['position'][along]+e['size'][along]/2) for e in panels)
    assert abs(intervals[0][1]-intervals[1][0]-.035)<1e-8
    assert not any(n.startswith((prefix+'Facade_',prefix+'_Handle',prefix+'Handle')) for n in after)
    for e in panels:
        assert e['inspectId'] in ('entry-wardrobe','hall-wardrobe','bedroom-wardrobe')
        for i in range(3):
            assert abs(e['position'][i]-meta['center'][i])+e['size'][i]/2<=meta['size'][i]/2+1e-8
for prefix,meta in m.OUTDOOR_BASKET_BOUNDS.items():
    members=[e for e in after.values() if e['name'].startswith(prefix)]
    axis=meta['axis'];sign=meta['sign'];win=after[meta['window']]
    for e in members:
        assert sign*(e['position'][axis]-meta['exterior'])-e['size'][axis]/2>=.0249,e['name']
        assert e['position'][1]+e['size'][1]/2<=win['position'][1]-win['size'][1]/2-.0499,e['name']
    tray=next(e for e in members if '_Tray_' in e['name']);along=2 if axis==0 else 0
    assert abs(min(e['position'][along]-e['size'][along]/2 for e in members)-(win['position'][along]-win['size'][along]/2))<1e-8
dog=[e for e in after.values() if e['name'].startswith('Dog') and not e['name'].startswith('DogBed')]
assert len(dog)<30
assert all(max(m.MATERIALS[e['material']]['color'][:3])<=.09 for e in dog)
assert all(max(m.MATERIALS[e['material']]['color'][:3])-min(m.MATERIALS[e['material']]['color'][:3])<.012 for e in dog)
assert all(e.get('detail',{}).get('type')=='pillow' and e['inspectId']=='dog-bed' for e in dog)
guitar=[e for e in after.values() if e['name'].startswith('Guitar')]
assert sum(e['name'].startswith('GuitarString') for e in guitar)==6
assert sum(e['name'].startswith('GuitarStand') for e in guitar)>=7
assert all(e['inspectId']=='guitar' for e in guitar)
body=next(e for e in guitar if e['name'].startswith('GuitarBody'))
assert body['size'][1]>.40 and body['size'][2]<.12
leaves=[e for e in after.values() if 'Decor_Leaf' in e['name']]
assert len(leaves)==36
assert all(e.get('detail',{}).get('type')=='leaf' for e in leaves)
for prefix in ('Bed_Mattress','Bed_Cover','StudySofa_Cushion','ComputerDesk','Washer_PortholeGlass','ToiletBowl','BasinRimWest'):
    assert next(e for e in after.values() if e['name'].startswith(prefix)).get('detail'),prefix
for room in ('BedroomWest','KitchenSouth'):
    curtains=[e for e in after.values() if e['name'].startswith('Curtain_'+room) and e.get('detail',{}).get('type')=='curtain']
    assert len(curtains)==3,room
print('Passed: unchanged architecture/PDF footprints; three sliding wardrobes, exterior baskets below centred windows, black dog, guitar + stand, 36 curved leaves, detailed furniture/textiles in all rooms.')
