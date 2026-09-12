"""Layer/clearance regression tests; no browser and no construction certification."""
import math
import generate_model as model
from finishes import SETTINGS, resolved

model.build_scene()
if getattr(model,'PDF_REFERENCE',False):
    from test_pdf_finishes import checks
    checks(model)
    raise SystemExit(0)
def node(name):
    return next(e for e in model.ELEMENTS if e['name'].startswith(name+'_'))
def top(e):return e['position'][1]+e['size'][1]/2
def edge(e,axis,sign):return e['position'][axis]+sign*e['size'][axis]/2
def close(a,b):assert abs(a-b)<1e-5,(a,b)

dry=SETTINGS['screed']+SETTINGS['laminate_underlay']
wet=SETTINGS['screed']+SETTINGS['tile_adhesive']
ceiling=2.8-SETTINGS['ceiling_drop']
p=SETTINGS['plaster_wallpaper']
for suffix in ('HallEntry','HallMiddle','Utility','KitchenUpper','KitchenMain'):
    assert node('Finish_Floor_'+suffix)['material']=='floor_pale_oak'
    close(top(node('Finish_Floor_'+suffix))+.0004,dry)
close(top(node('Finish_Floor_Bathroom'))+.0004,wet)
assert node('Finish_Floor_Bathroom')['material']=='stone_gray'
assert node('Tile_BathFeature')['material'].startswith('tile_wood_')
assert node('Tile_BathEast')['material'].startswith('stone_gray_')
for e in model.ELEMENTS:
    r=resolved(e)
    assert all(math.isfinite(v) and v>0 for v in r['size']),r
    if r['category']=='furniture' and 'OutdoorBasket' not in r['name']:
        assert top(r)<=ceiling+1e-5,(r['name'],top(r))
    if e['category']=='door':
        assert e['material']=='door_ivory'
        close(edge(r,1,-1),dry+.005)
        close(top(r),e['size'][1]-p)
        close(r['size'][0],e['size'][0]-2*p)
    if e['name'].startswith('KitchenUpper') and '_Handle_' not in e['name']:
        assert e['material']==node('FreezerBase')['material']
    if e['name'].startswith('Furniture_DiningChair'):assert e['material']=='oak_light'
    if e['name'].startswith('KitchenSofa'):assert e['material']=='sofa_olive'
    if e['category']=='ceiling':
        close(edge(e,1,-1),2.8 if e['rawOnly'] else ceiling)

# Survey remains the source of truth; dimensions below are raw-room dimensions.
assert node('Floor_Bedroom')['size']==[4.72,.06,2.94]
close(edge(node('WallFinish_BedroomNorth'),2,1),2.7+p)
close(edge(node('WallFinish_BedroomSouth'),2,-1),5.64-p)
close(resolved(node('Curtain_BedroomWest_Track'))['size'][2],2.94-2*p)
close(top(resolved(node('BathTallCabinet'))),ceiling)
close(edge(resolved(node('BathTallCabinet')),1,-1),wet)
wardrobe=resolved(node('EntryWardrobe'))
close(edge(wardrobe,2,-1),p)
close(edge(wardrobe,2,1),2.62-p)
for name in ('Washer','Dryer'):
    appliance=resolved(node(name))
    assert appliance['size']==node(name)['size']
    assert edge(appliance,2,1)<edge(resolved(node('LaundryWardrobeSouthSide')),2,-1)
    assert edge(appliance,2,-1)>edge(resolved(node('LaundryWardrobeDivider')),2,1)
for name in ('ComputerDesk','DiningTable','Bed_Frame'):
    assert resolved(node(name))['size']==node(name)['size']
    close(resolved(node(name))['position'][1]-node(name)['position'][1],dry)
print('Finish layers, clear heights, wardrobe/appliance fit, materials and unchanged survey dimensions passed.')
