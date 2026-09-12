"""Reference styling must not copy generated geometry into the measured shell."""
import copy
import generate_model as m
import render_style
import scene_lighting

# This test isolates styling; plan lighting depends on the styled sconces.
def no_plan_lighting(api):
    api.SCENE_LIGHTS=[];api.LIGHTING_LAYOUT=[];api.LIGHTING_REFERENCE={}
scene_lighting.build=no_plan_lighting

style=render_style.build
render_style.build=lambda api:None
m.build_scene()
before={e['name']:copy.deepcopy(m.resolved(e)) for e in m.ELEMENTS}
render_style.build=style
m.build_scene()
after={e['name']:m.resolved(e) for e in m.ELEMENTS}
for name,e in before.items():
    if e['category'] in ('wall','door','floor','window','ceiling','finish_wall','finish_floor'):
        for prop in ('position','size','rotation','shape'):
            assert after[name].get(prop)==e.get(prop),(name,prop)
    if name.startswith(('Bed_','Bedroom','Study','ComputerDesk','Piano','BathTallCabinet')):
        for prop in ('position','size','rotation','material'):
            assert after[name].get(prop)==e.get(prop),(name,prop)
catalog={e['id']:e for e in m.FURNITURE_CATALOG}
for ident,dims in {'table':[900,900],'tv-console':[1500,350],'hall-wardrobe':[1350,600],
                   'entry-wardrobe':[1800,600],'kitchen-sofa':[1500,900],
                   'sink-unit':[600,600],'end-unit':[450,600]}.items():
    assert catalog[ident]['dimensionsMm'][:2]==dims,(ident,catalog[ident])
for e in after.values():
    if e['name'].startswith(('KitchenSofa','KitchenRug')):
        assert e['position'][1]-e['size'][1]/2>=m.FINISH_SETTINGS['dry_floor']-1e-6
    if e['name'].startswith('KitchenUpper') and '_Handle' not in e['name']:
        assert e['material']=='kitchen_ivory'
        assert abs(e['position'][1]+e['size'][1]/2-2.75)<1e-6
assert after['MicrowaveBody_001']['position'][0]<before['MicrowaveBody_001']['position'][0]
assert not any(n.startswith(('KitchenSinkInterior','HallWardrobeFacadePanel','EntryWardrobeFacadePanel')) for n in after)
assert sum(n.startswith('TVConsole_') and '_Handle' not in n for n in after)==3
assert after['KitchenSinkBowl_001']['position'][1]<.908
assert after['SinkUnit_001']['position'][1]+after['SinkUnit_001']['size'][1]/2<.718
assert {'kitchen-light','kitchen-art','kitchen-rug','kitchen-lighting'}<=catalog.keys()
assert len(m.scene_data()['elements'])==len(after)
print('Passed: immutable shell/doors/openings, unchanged bedroom/study/bath, approved furniture widths, flat fronts, hollow sink, light/decor groups.')
