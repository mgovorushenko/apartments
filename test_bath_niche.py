"""Every cabinet component stays within the finished niche, including hardware."""
import generate_model as model

model.build_scene()
items=[model.resolved(e) for e in model.ELEMENTS]
def node(prefix):return next(e for e in items if e['name'].startswith(prefix))
def edge(e,a,s):return e['position'][a]+s*e['size'][a]/2
limits={0:(edge(node('Tile_BathWestLower_'),0,1),edge(node('Tile_VentSide_'),0,-1)),
        2:(edge(node('Tile_VentFront_'),2,-1),edge(node('Tile_BathSouth_'),2,-1)),
        1:(model.FINISH_SETTINGS['wet_floor'],2.8-model.FINISH_SETTINGS['ceiling_drop'])}
cabinet=[e for e in items if e['name'].startswith('BathTallCabinet')]
assert cabinet
for axis,(lo,hi) in limits.items():
    assert abs(min(edge(e,axis,-1) for e in cabinet)-lo)<1e-8
    assert abs(max(edge(e,axis,1) for e in cabinet)-hi)<1e-8
    for e in cabinet:
        assert edge(e,axis,-1)>=lo-1e-8 and edge(e,axis,1)<=hi+1e-8,(e['name'],axis)
assert len([e for e in cabinet if '_Handle_Recess_' in e['name']])==2
assert not any('_Handle_Grip_' in e['name'] or '_Handle_Mount_' in e['name'] for e in cabinet)
catalog=next(e for e in model.FURNITURE_CATALOG if e['id']=='bath-cabinet')
assert catalog['dimensionsMm']==[round((limits[a][1]-limits[a][0])*1000) for a in (0,2,1)]
print('Passed: exact finished-niche bounds, no peripheral gaps, no projecting panels or handles:',catalog['dimensionsMm'],'mm')
