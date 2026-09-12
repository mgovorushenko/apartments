"""Reference 04 styling on approved geometry; never transfer generated walls.

All coordinates are final metres, after the PDF warp and finish build-up.
Surface codes: 1 oak, 2 woven textile, 3 stone, 4 luminous diffuser.
"""
import math


def build(api):
    floor=api.FINISH_SETTINGS['dry_floor']
    def mat(name,rgb,pattern=0,roughness=.8,metallic=0):
        api.MATERIALS[name]=dict(color=[*rgb,1],roughness=roughness,
                                metallic=metallic,pattern=pattern)
    mat('kitchen_ivory',(.87,.845,.79),roughness=.73)
    mat('kitchen_joint',(.55,.51,.44))
    mat('kitchen_oak',(.76,.63,.46),1)
    mat('kitchen_stone',(.82,.79,.72),3)
    mat('kitchen_fabric',(.76,.73,.66),2)
    mat('kitchen_sofa_sage',(.77,.745,.695),2)  # Light warm greige, matching the render.
    mat('kitchen_art_paper',(.88,.855,.79))
    mat('kitchen_art_sand',(.72,.64,.51))
    mat('kitchen_art_sage',(.47,.54,.47))
    mat('kitchen_art_blue',(.39,.48,.53))
    mat('kitchen_opal',(1,.97,.90),4,roughness=.68)
    mat('kitchen_seat',(.85,.82,.75),2)
    mat('kitchen_rug',(.83,.79,.69),2)
    mat('kitchen_rug_border',(.73,.68,.58),2)
    mat('kitchen_olive',(.39,.43,.30),2)
    mat('kitchen_linen',(.73,.70,.64),2)
    mat('kitchen_light',(1,.93,.77),4)
    mat('kitchen_brass',(.65,.52,.32),roughness=.35,metallic=.6)
    mat('kitchen_steel',(.68,.70,.68),roughness=.28,metallic=.8)
    mat('kitchen_sink_inner',(.42,.46,.45),roughness=.3,metallic=.7)
    for i,factor in enumerate((.985,1,1.015)):
        mat('kitchen_floor_'+str(i),tuple(c*factor for c in (.80,.70,.56)),1)
    api.MATERIALS['wall_beige']['color']=[.89,.86,.80,1]

    def put(e,**changes):
        # Preserve raw data and transform once: these are finished-only overrides.
        e['finished']={**api.resolved(e),**changes}
        e['finished'].pop('finished',None)
    def node(prefix):
        return next(e for e in api.ELEMENTS if e['name'].startswith(prefix))
    def box(name,material,x,z,w,d,h,base,category='furniture',rotation=0):
        api.add_box(name,material,x,z,w,d,h,base=base,category=category,rotation=rotation)
        e=api.ELEMENTS[-1];e['noEdges']=True
        return e
    def disc(name,material,x,z,diam,h,base):
        api.add_cylinder(name,material,x,z,diam,h,base=base)
        e=api.ELEMENTS[-1];e['noEdges']=True
        return e

    cases=('FreezerBase','KettleCorner','SinkUnit','Dishwasher','OvenUnit','EndUnit','KitchenUpper','TVConsole')
    hall=('EntryWardrobe','HallWardrobe','LaundryStorage','LaundryUpperStorage','LaundryWardrobe')
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not (
        e['name'].startswith(hall) and 'FacadePanel' in e['name'])]
    for e in list(api.ELEMENTS):
        n=e['name'];r=api.resolved(e);p=list(r['position']);s=list(r['size'])
        if n.startswith(cases):
            material='kitchen_stone' if 'Worktop' in n else ('kitchen_joint' if 'Handle' in n else 'kitchen_ivory')
            put(e,material=material,noEdges=True)
            # Slim integrated pulls replace handles at arbitrary mid-facade heights.
            if 'Handle' in n:
                body_name=n.split('_Handle')[0]+'_001'
                if n.startswith('TVConsole'):continue
                body=api.resolved(next(a for a in api.ELEMENTS if a['name']==body_name))
                axis=2 if n.startswith(('FreezerBase','KitchenUpperFridge','KitchenUpperFreezer','KitchenUpperCornerReturn')) else 0
                p[1]=body['position'][1]+(-1 if n.startswith('KitchenUpper') else 1)*(body['size'][1]/2-.012)
                s[1]=.008;s[axis]=.006
                put(e,position=p,size=s)
        if n.startswith(hall):
            put(e,material=('kitchen_brass' if 'Handle' in n else 'kitchen_joint' if any(k in n for k in ('Reveal','EndJoint','Plinth')) else 'kitchen_ivory'),noEdges=True)
        if n.startswith('KitchenSofa'):put(e,material='kitchen_sofa_sage',noEdges=True,bevel=.025)
        if n.startswith('TV_'):
            p[1]+=.12
            put(e,position=p)
        if n.startswith('Furniture_Dining'):
            put(e,material='kitchen_seat' if '_seat_' in n else 'kitchen_oak',noEdges=True)
            if '_seat_' in n:put(e,bevel=.028)
            if '_back_' in n:
                s[1]=.22;p[1]=floor+.77
                put(e,position=p,size=s,bevel=.025)
            if '_leg_' in n:put(e,shape='cylinder')
        if n.startswith('Furniture_CoffeeTable'):put(e,material='kitchen_oak',noEdges=True)
        if n.startswith('Curtain_KitchenSouth') and 'Panel' in n:put(e,material='kitchen_linen',noEdges=True)
        if r['category']=='finish_floor' and r['material'].startswith('floor_pale_oak') and p[0]>4.72:
            tone=r['material'][-1] if r['material'][-1].isdigit() else '1'
            put(e,material='kitchen_floor_'+tone,noEdges=True)
        if n.startswith('Microwave'):put(e,noEdges=True)

    # 700 mm allocation is the niche, not the selected appliance width.
    # Illustrative 600 mm freestanding fridge: 18 mm cheeks + 32 mm side gaps.
    for e in api.ELEMENTS:
        if e['name'].startswith('Fridge'):
            r=api.resolved(e);p=list(r['position']);s=list(r['size'])
            p[0]=7.525+(p[0]-7.525)*6/7;s[0]*=6/7
            put(e,position=p,size=s)
    for x in (7.184,7.866):
        e=box('KitchenFridgeNiche_Side','kitchen_ivory',x,4.475,.018,.600,2.75-floor,floor)
        e['detail']=dict(type='rounded',radius=.001,steps=1)

    # Hall carcass footprints, wall positions and openings are untouched.
    # Uniform upper baseline including concealed hood, up to finished ceiling.
    for e in list(api.ELEMENTS):
        n=e['name'];r=api.resolved(e)
        if n.startswith('KitchenUpper') and '_Handle' not in n:
            bottom=2.118 if 'Fridge' in n else 1.518
            put(e,position=[r['position'][0],(bottom+2.75)/2,r['position'][2]],size=[r['size'][0],2.75-bottom,r['size'][2]])
            r=api.resolved(e);south=any(t in n for t in ('Fridge','Freezer','CornerReturn'))
            axis=2 if south else 0;along=0 if south else 2;sign=1 if south else -1
            # Flush facade joints remain legible with edge outlines disabled.
            q=list(r['position']);q[axis]+=sign*(r['size'][axis]/2+.0006)
            for side in (-1,1):
                v=q.copy();v[along]+=side*(r['size'][along]/2-.001)
                ss=[.002,r['size'][1]-.003,.002]
                box('KitchenFrontJoint','kitchen_joint',v[0],v[2],ss[0],ss[2],ss[1],bottom+.0015)
    hood=node('Hood_');r=api.resolved(hood)
    put(hood,position=[8.91,1.508,r['position'][2]],size=[.28,.02,r['size'][2]],noEdges=True)
    handle=node('KitchenUpperHood_Handle');r=api.resolved(handle)
    put(handle,position=[r['position'][0],1.530,r['position'][2]])

    # Continuous stone splash, lower plinth and discreet drawer seams.
    box('KitchenBacksplashLong','kitchen_stone',9.065,5.60,.018,2.85,.61,.908)
    box('KitchenBacksplashReturn','kitchen_stone',8.175,4.186,.60,.018,.61,.908)
    for prefix in ('KettleCorner','SinkUnit','Dishwasher','OvenUnit','EndUnit','FreezerBase'):
        r=api.resolved(node(prefix+'_001'));x,y,z=r['position'];w,h,d=r['size'];south=prefix=='FreezerBase'
        box(prefix+'StylePlinth','kitchen_joint',x if south else x-w/2-.0006,z+d/2+.0006 if south else z,w if south else .001,.001 if south else d,.085,floor)
        if prefix not in ('OvenUnit',):
            box(prefix+'StyleDrawerJoint','kitchen_joint',x if south else x-w/2-.001,z+d/2+.001 if south else z,w-.008 if south else .002,.002 if south else d-.008,.003,.73)
    # TV console remains 3 x 500 mm and abuts kitchen; now wall-hung.
    for e in api.ELEMENTS:
        if e['name'].startswith('TVConsole'):
            r=api.resolved(e);p=list(r['position']);p[1]+=.23
            put(e,position=p,noEdges=True)
            if 'Handle' in e['name']:put(e,material='kitchen_ivory')
    for z in (7.525,8.025):box('TVConsoleStyleJoint','kitchen_joint',8.724,z,.001,.002,.45,floor+.235)

    # A real opening in the worktop, not a black plate over a solid top.
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith(('KitchenSink','KitchenTap','SinkUnit_Worktop'))]
    cx,cz=8.775,5.075;inner_x,inner_z=.40,.45;outer_x,outer_z=.44,.49;y=.908
    for dx in (-1,1):
        box('SinkUnit_WorktopSide','kitchen_stone',cx+dx*(outer_x/2+(.6-outer_x)/4),cz,(.6-outer_x)/2,.6,.04,.868)
    for dz in (-1,1):
        box('SinkUnit_WorktopEnd','kitchen_stone',cx,cz+dz*(outer_z/2+(.6-outer_z)/4),outer_x,(.6-outer_z)/2,.04,.868)
    # The cabinet's top is recessed below the bowl so it does not fill the hole.
    source=node('SinkUnit_001');r=api.resolved(source)
    put(source,position=[r['position'][0],floor+.325,r['position'][2]],size=[.6,.65,.6])
    box('SinkUnit_FrontPanel','kitchen_ivory',8.474,cz,.002,.60,.765,floor+.085)
    for dx in (-1,1):
        box('KitchenSinkRim','kitchen_steel',cx+dx*(inner_x/2+.01),cz,.02,outer_z,.008,y)
        box('KitchenSinkSide','kitchen_steel',cx+dx*inner_x/2,cz,.008,inner_z,.19,y-.19)
    for dz in (-1,1):
        box('KitchenSinkRim','kitchen_steel',cx,cz+dz*(inner_z/2+.01),inner_x,.02,.008,y)
        box('KitchenSinkSide','kitchen_steel',cx,cz+dz*inner_z/2,inner_x,.008,.19,y-.19)
    box('KitchenSinkBowl','kitchen_sink_inner',cx,cz,inner_x,inner_z,.008,y-.19)
    disc('KitchenSinkDrain','metal',cx,cz,.065,.003,y-.181)
    disc('KitchenTapStem','kitchen_steel',9.022,5.075,.025,.29,y)
    box('KitchenTapSpout','kitchen_steel',8.958,5.075,.145,.024,.025,y+.277)
    disc('KitchenTapOutlet','kitchen_steel',8.892,5.075,.027,.04,y+.245)
    box('KitchenTapLever','kitchen_steel',9.02,5.13,.022,.08,.012,y+.13)

    # Microwave stays within the 600 mm freezer return, shifted 40 mm left.
    for e in api.ELEMENTS:
        if e['name'].startswith('Microwave'):
            r=api.resolved(e);p=list(r['position']);p[0]-=.04;put(e,position=p)
    box('MicrowaveControlPanel','white',8.343,4.756,.072,.008,.25,.943)
    box('MicrowaveDisplay','dark',8.343,4.761,.052,.003,.033,1.10)
    box('MicrowaveControl','metal',8.344,4.764,.028,.008,.03,1.005)
    box('MicrowaveHandle','metal',8.276,4.766,.012,.016,.18,.975)
    r=api.resolved(node('Kettle_001'));kx,ky,kz=r['position']
    disc('Kettle_Lid','dark',kx,kz,.16,.017,1.158)
    box('Kettle_Handle','dark',kx+.135,kz,.022,.026,.18,.95)
    for yy in (.95,1.11):box('Kettle_HandleReturn','dark',kx+.10,kz,.085,.027,.02,yy)
    box('Kettle_Spout','kitchen_steel',kx-.115,kz,.07,.034,.05,1.085)

    # Pedestal table with fluted oak base; keep Ø900 and chair positions.
    e=node('Furniture_DiningTable_pedestal_');r=api.resolved(e)
    put(e,size=[.36,r['size'][1],.36])
    for i in range(32):
        a=i*math.tau/32
        disc('Furniture_DiningTable_Flute','kitchen_oak',6.675+.183*math.cos(a),6.175+.183*math.sin(a),.015,.67,floor+.018)
    e=node('Furniture_DiningTable_top_');r=api.resolved(e)
    put(e,position=[r['position'][0],r['position'][1]+.02,r['position'][2]],size=[.9,.04,.9])
    for e in api.ELEMENTS:
        if e['name'].startswith('Furniture_CoffeeTable_pedestal'):
            r=api.resolved(e);put(e,size=[.48,r['size'][1],.48])
    # Backrest posts below shortened oak chair backrests.
    for i in range(1,5):
        r=api.resolved(node(f'Furniture_DiningChair{i}_back_'));a=r['rotation'];x,_,z=r['position']
        for side in (-1,1):
            disc(f'Furniture_DiningChair{i}_Post','kitchen_oak',x+side*.16*math.cos(a),z-side*.16*math.sin(a),.025,.20,floor+.51)
    # Remove the northeast chair in the working aisle; keep the sofa-side pair.
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith('Furniture_DiningChair2_')]
    # Upholstered sofa pads within its unchanged 1500 x 900 footprint.
    for z in (7.42,8.13):
        e=box('KitchenSofa_BackPad','kitchen_sofa_sage',6.15,z,.19,.62,.42,.45);e['bevel']=.055
    e=box('KitchenSofa_AccentPillow','kitchen_olive',6.25,8.13,.16,.40,.37,.57);e['bevel']=.06
    for z in (7.13,8.42):
        for x in (6.08,6.67):disc('KitchenSofa_Leg','kitchen_oak',x,z,.043,.10,floor)
    box('KitchenRug_Border','kitchen_rug_border',7.325,7.77,1.75,1.43,.006,floor+.001)
    box('KitchenRug_Weave','kitchen_rug',7.325,7.77,1.70,1.38,.002,floor+.007)

    # Wall-mounted light aligned with table, clear of study doorway.
    plate=box('KitchenSconce_Plate','kitchen_ivory',5.959,6.175,.025,.10,.10,1.46)
    plate['detail']=dict(type='pillow',power=2)
    box('KitchenSconce_Arm','kitchen_ivory',6.00,6.175,.08,.024,.024,1.498)
    shade=box('KitchenSconce_Shade','kitchen_opal',6.085,6.175,.16,.18,.18,1.42)
    shade['detail']=dict(type='pillow',power=2)
    # Horizontal oak-framed abstract landscape, centred on the 1500 mm sofa.
    box('KitchenArt_Frame','kitchen_oak',5.963,7.775,.030,1.00,.55,1.20)
    box('KitchenArt_Paper','kitchen_art_paper',5.981,7.775,.006,.966,.516,1.217)
    for name,material,z,w,h,base in (
        ('Dune','kitchen_art_sand',7.78,.86,.22,1.275),
        ('Hill','kitchen_art_sage',7.58,.46,.18,1.26),
        ('Horizon','kitchen_art_blue',7.98,.37,.075,1.26),
        ('Sun','kitchen_art_sand',8.055,.10,.10,1.55),
    ):
        patch=box('KitchenArt_'+name,material,5.986+(base<1.27)*.002,z,.002,w,h,base)
        patch['detail']=dict(type='pillow',power=2)
    # Under-upper diffusers and flush ceiling downlights, no hanging lamps.
    box('KitchenLED_Long','kitchen_light',8.746,5.60,.018,2.80,.006,1.506)
    box('KitchenLED_Return','kitchen_light',8.31,4.50,.77,.018,.006,1.506)
    for x,z in ((7.72,5.25),(7.72,6.5),(7.72,7.75),(6.7,4.0),(6.65,2.15),(7.0,.6)):
        disc('KitchenCeilingLight_Trim','door_ivory',x,z,.115,.009,2.738)
        disc('KitchenCeilingLight_Diffuser','kitchen_light',x,z,.087,.003,2.735)
    # Sparse decor remaining in the approved image, no plants in hall/on dining table.
    def plant(prefix,x,z,y,scale=.7):
        disc(prefix+'Vase','ceramic',x,z,.15*scale,.19*scale,y)
        for i in range(7):
            a=i*math.tau/7
            box(prefix+'Stem','green',x+.045*scale*math.cos(a),z+.045*scale*math.sin(a),.006,.006,.24*scale,y+.13*scale)
            leaf=disc(prefix+'Leaf','green',x+.10*scale*math.cos(a),z+.10*scale*math.sin(a),.11*scale,.012,y+(.26+.03*(i%3))*scale)
            leaf['size'][2]=.035*scale;leaf['rotation']=a
    plant('KitchenCoffeeDecor_',7.48,7.89,.458)
    plant('KitchenTVDecor_',8.87,8.35,.708,.7)
    plant('KitchenCounterDecor_',8.96,6.86,.908,.7)
    box('KitchenCoffeeBook','kitchen_seat',7.58,7.74,.18,.13,.022,.458)
    disc('KitchenDiningFruitBowl','ceramic',6.675,6.175,.16,.035,.788)
    for dx,dz in ((-.035,0),(.025,.023),(.027,-.025)):
        disc('KitchenDiningFruit','kitchen_olive',6.675+dx,6.175+dz,.055,.05,.817)
