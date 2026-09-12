"""Readable cabinet geometry without changes to the approved carcass envelopes."""
import generate_model as model

model.build_scene()
items=[model.resolved(e) for e in model.ELEMENTS]
catalog={e['id']:e for e in model.FURNITURE_CATALOG}
def edge(e,axis,sign):return e['position'][axis]+sign*e['size'][axis]/2
def near(a,b):assert abs(a-b)<.00011,(a,b)
for prefix,source in model.CABINET_DETAIL_BOUNDS.items():
    assert not any(e['name']==prefix+'_001' for e in items)
    case=[e for e in items if e['name'].startswith(prefix+'Case_')]
    assert len(case)==6,(prefix,len(case))
    for a in range(3):
        near(min(edge(e,a,-1) for e in case),edge(source,a,-1))
        near(max(edge(e,a,1) for e in case),edge(source,a,1))
    facades=[e for e in items if e['name'].startswith(prefix+'Facade_')]
    assert len(facades)==({'EntryWardrobe':0,'HallWardrobe':0,'LaundryStorage':2,'LaundryUpperStorage':1,'BathTallCabinet':0}[prefix])
    if prefix in ('EntryWardrobe','HallWardrobe'):
        assert len([e for e in items if e['name'].startswith(prefix+'SlidingDoor_')])==2
    if prefix=='BathTallCabinet':
        assert len([e for e in items if e['name'].startswith(prefix+'FacadePanel_')])==2
    for e in items:
        if not e['name'].startswith(prefix):continue
        assert e['category']=='furniture' and e.get('inspectId') in catalog,e['name']
        assert edge(e,1,1)<=2.7501,e['name']
assert catalog['entry-wardrobe']['dimensionsMm'][:2]==[1800,600]
assert catalog['hall-wardrobe']['dimensionsMm'][:2]==[1350,600]
assert catalog['entry-shoes']['dimensionsMm']==[750,600,2500]
assert catalog['bath-cabinet']['dimensionsMm'][2]==2729
assert not any(e['name'].startswith('EntryShoe') for e in items)
for suffix in ('Rail_','Hanger_','JacketBody_','Sleeve_','Collar_','Pocket_','Bench_','ShoeUpper_','TopBasket_'):
    assert any(e['name'].startswith('EntryCoat'+suffix) for e in items),suffix
for e in [e for e in items if e['name'].startswith('EntryCoat')]:
    assert e.get('inspectId')=='entry-shoes'
    assert 5.5649<=edge(e,0,-1)<edge(e,0,1)<=6.1651
    assert .0349<=edge(e,2,-1)<edge(e,2,1)<=.7851
    assert edge(e,1,1)<=2.5181
print('Passed: 5 detailed cabinets retain carcass bounds; 750 × 600 coat alcove; grouped picking metadata; ceiling fit.')
