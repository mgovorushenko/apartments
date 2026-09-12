"""Kitchen/living pilot: detailed furniture inside the approved layout.

No architecture, nominal body dimensions, lights, or other rooms are moved.
Mesh shapes are illustrative, not selected manufacturer products.
"""
import math


def build(api):
    def put(e,**changes):
        e['finished']={**api.resolved(e),**changes};e['finished'].pop('finished',None)
    def node(prefix):return next(e for e in api.ELEMENTS if e['name'].startswith(prefix))
    def material(name,rgb,roughness=.75,metallic=0,pattern=0):
        api.MATERIALS[name]=dict(color=[*rgb,1],roughness=roughness,metallic=metallic,pattern=pattern)
    material('kitchen_stitch',(.57,.54,.48),pattern=2)
    material('kitchen_appliance_glass',(.085,.105,.115),.17,.25)
    material('kitchen_brushed',(.66,.69,.69),.3,.8)
    material('kitchen_glass_mark',(.34,.36,.35),.4)
    material('kitchen_leaf',(.28,.35,.21),.87)
    def box(name,mat,p,s,radius=.005):
        api.add_box(name,mat,p[0],p[2],s[0],s[2],s[1],base=p[1]-s[1]/2)
        e=api.ELEMENTS[-1];e.update(noEdges=True,detail=dict(type='rounded',radius=radius))
        return e
    def lathe(e,rings,segments=48):put(e,detail=dict(type='lathe',rings=rings,segments=segments),noEdges=True)
    for e in list(api.ELEMENTS):
        n=e['name'];r=api.resolved(e)
        if n.startswith(('KitchenSofa','Furniture_Dining','Furniture_CoffeeTable','Fridge','Microwave','OvenDoor','TVConsole')):
            put(e,noEdges=True)
        if n.startswith('KitchenSofa') and r['shape']=='box':
            if any(t in n for t in ('Cushion','BackPad','Pillow')):
                put(e,detail=dict(type='pillow',power=4 if 'Pillow' in n else 6))
            else:put(e,detail=dict(type='rounded',radius=.035))
        if n.startswith('Furniture_DiningChair'):
            if '_seat_' in n:put(e,detail=dict(type='pillow',power=6))
            if '_back_' in n:put(e,detail=dict(type='bow',radius=.018))
            if '_leg_' in n:lathe(e,[[0,-.5],[.34,-.5],[.40,-.47],[.5,.48],[.46,.5],[0,.5]],20)
        if n.startswith(('Furniture_DiningTable_top','Furniture_CoffeeTable_top')):
            lathe(e,[[0,-.5],[.47,-.5],[.49,-.40],[.5,-.15],[.5,.15],[.493,.4],[.48,.5],[0,.5]],64)
        if n.startswith('Furniture_CoffeeTable_pedestal'):
            lathe(e,[[0,-.5],[.47,-.5],[.5,-.45],[.5,.45],[.47,.5],[0,.5]])
        if n.startswith(('Fridge_001','MicrowaveBody','TVConsole_')) and 'Handle' not in n:
            put(e,detail=dict(type='rounded',radius=.006))
        if n.startswith(('KitchenUpper','FreezerBase','KettleCorner','SinkUnit','Dishwasher','OvenUnit','EndUnit')) and r['shape']=='box' and 'Handle' not in n and min(r['size'])>.02:
            put(e,detail=dict(type='rounded',radius=.0015))
        if n.startswith(('Cooktop_','OvenDoor_','MicrowaveWindow','TV_Screen')):
            put(e,material='kitchen_appliance_glass',noEdges=True)
        if n.startswith('HobRing'):
            put(e,material='kitchen_glass_mark',size=[r['size'][0],.0008,r['size'][2]],position=[r['position'][0],.9306,r['position'][2]])
            lathe(e,[[.46,-.5],[.5,-.5],[.5,.5],[.46,.5],[.46,-.5]],40)
        if n.startswith('KitchenDiningFruit_'):
            put(e,detail=dict(type='pillow',power=2))
        if n.startswith('KitchenDiningFruitBowl'):
            lathe(e,[[0,-.5],[.3,-.5],[.4,-.35],[.5,.4],[.49,.5],[.46,.5],[.36,-.2],[0,-.27]])
        if n.startswith(('KitchenCoffeeDecor','KitchenTVDecor','KitchenCounterDecor')):
            if 'Vase' in n:lathe(e,[[0,-.5],[.3,-.5],[.45,-.4],[.5,-.15],[.46,.18],[.29,.38],[.28,.5],[.23,.5],[.23,.33]])
            if 'Leaf' in n:put(e,material='kitchen_leaf',detail=dict(type='pillow',power=2))
    # Two seat cushions preserve the original seat envelope and the 1500 × 900 body.
    e=node('KitchenSofa_Cushion');r=api.resolved(e);z=r['position'][2];d=r['size'][2]
    left=[r['position'][0],r['position'][1],z-d/4-.002]
    size=[r['size'][0],r['size'][1],d/2-.004]
    put(e,position=left,size=size)
    other=box('KitchenSofa_SeatPad',r['material'],[left[0],left[1],z+d/4+.002],size)
    other['detail']=dict(type='pillow',power=6)
    # Piping on the visible front of each seat, contained by the body footprint.
    for zz in (left[2],z+d/4+.002):
        box('KitchenSofa_SeatSeam','kitchen_stitch',[6.766,.508,zz],[.003,.003,d/2-.08],.001)
    # Appliance faces: fridge compartment division, oven glass/control strip/pull.
    box('Fridge_CompartmentJoint','kitchen_joint',[7.525,.70,4.7752],[.581,.004,.001],.0004)
    box('Fridge_LowerPull','kitchen_brushed',[7.69,.68,4.779],[.18,.012,.006],.002)
    box('OvenDoor_ControlPanel','kitchen_appliance_glass',[8.467,.79,6.275],[.008,.11,.49],.003)
    box('OvenDoor_Glass','kitchen_appliance_glass',[8.467,.454,6.275],[.007,.34,.35],.003)
    box('OvenDoor_Pull','kitchen_brushed',[8.448,.69,6.275],[.028,.018,.38],.005)
    for zz in (6.10,6.45):
        box('OvenDoor_Dial','kitchen_brushed',[8.447,.79,zz],[.03,.032,.032],.012)
    box('OvenDoor_Display','kitchen_glass_mark',[8.461,.794,6.275],[.003,.022,.09],.002)
    # Replace the rigid strips by two continuous gathered textile panels and tulle.
    # Bounds derive from the existing curtain, preserving its track/window position.
    for group,folds in (('LeftPanel',5),('RightPanel',5),('Tulle',14)):
        members=[e for e in api.ELEMENTS if e['name'].startswith('Curtain_KitchenSouth_'+group)]
        resolved=[api.resolved(e) for e in members]
        lo=[min(e['position'][i]-e['size'][i]/2 for e in resolved) for i in range(3)]
        hi=[max(e['position'][i]+e['size'][i]/2 for e in resolved) for i in range(3)]
        api.ELEMENTS[:]=[e for e in api.ELEMENTS if e not in members]
        p=[(lo[i]+hi[i])/2 for i in range(3)];s=[hi[i]-lo[i] for i in range(3)]
        # 60 mm gathered depth; centre and clear bottom unchanged.
        s[2]=.060 if group!='Tulle' else .023
        e=box('Curtain_KitchenSouth_'+group,resolved[0]['material'],p,s)
        e['detail']=dict(type='curtain',folds=folds)
    # No additional lamps or animated effects. Daylight remains inexpensive.
