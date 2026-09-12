"""Current PDF revision: finish layers and material consistency."""
from finishes import SETTINGS

def checks(model):
    dry=SETTINGS['screed']+SETTINGS['laminate_underlay']
    wet=SETTINGS['screed']+SETTINGS['tile_adhesive']
    ceiling=2.8-SETTINGS['ceiling_drop']
    def near(a,b):assert abs(a-b)<.00001,(a,b)
    for original in model.ELEMENTS:
        e=model.resolved(original);name=e['name']
        top=e['position'][1]+e['size'][1]/2
        if e['category']=='furniture':assert top<=ceiling+.00001,name
        if name.startswith('Finish_Floor_'):
            expected=wet if ('Bathroom' in name or 'BathThreshold' in name) else dry
            near(top+.0004,expected)
            if any(s in name for s in ('Hall','Kitchen','Utility')):assert e['material'].startswith('kitchen_floor_')
        if e['category']=='door':assert e['material']=='door_ivory'
        if name.startswith('KitchenUpper') and '_Handle_' not in name:assert e['material']=='kitchen_ivory'
        if name.startswith('Furniture_DiningChair'):assert e['material']==('kitchen_seat' if '_seat_' in name else 'kitchen_oak')
        if name.startswith('KitchenSofa'):assert e['material'] in ('kitchen_fabric','kitchen_seat','kitchen_olive','kitchen_oak','kitchen_stitch','kitchen_sofa_sage')
        if name.startswith('BathTallCabinet_001'):near(top,ceiling)
        if e['category']=='ceiling':near(e['position'][1]-e['size'][1]/2,2.8 if e['rawOnly'] else ceiling)
    print('Current PDF revision: finish elevations, ceiling fit and materials passed. Thicknesses remain provisional.')

if __name__=='__main__':
    import generate_model as model
    model.build_scene();checks(model)
