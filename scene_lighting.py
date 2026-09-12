"""Fixtures registered to the user's lighting plan; illustrative evening light."""
from lighting_plan import SPOTS,SCONCES,CENTRAL,SUPPLIES,X_ANCHORS,Z_ANCHORS,position


def build(api):
    api.SCENE_LIGHTS=[];api.LIGHTING_LAYOUT=[]
    ceiling=2.8-api.FINISH_SETTINGS['ceiling_drop']
    api.MATERIALS['room_light']=dict(color=[1,.94,.85,1],roughness=.5,metallic=0,pattern=4)
    api.MATERIALS['bedroom_lamp']['pattern']=4
    # Replace every former illustrative ceiling fixture, including kitchen/hall.
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith(
        ('KitchenCeilingLight','RoomCeilingLight','BathCeilingLight'))]
    def node(prefix):return next(e for e in api.ELEMENTS if e['name'].startswith(prefix))
    def put(e,**changes):
        e['finished']={**api.resolved(e),**changes};e['finished'].pop('finished',None)
    def light(p,power,label,color=(1,.94,.85),fixture=None):
        api.SCENE_LIGHTS.append(dict(position=list(p),power=power,color=list(color),label=label,fixture=fixture))
    def record(ident,kind,room,pixel,p,elements):
        api.LIGHTING_LAYOUT.append(dict(id=ident,kind=kind,room=room,sourcePixel=list(pixel),position=list(p),elements=elements,
            placement='Пропорционально схеме; отметки высоты и габариты светильников условные'))
        for e in api.ELEMENTS:
            if e['name'] in elements:e['lightingId']=ident
    def disc(name,mat,x,z,diam,h,base):
        api.add_cylinder(name,mat,x,z,diam,h,base=base)
        e=api.ELEMENTS[-1];e.update(position=[x,base+h/2,z],noEdges=True)
        return e
    def box(name,mat,p,s):
        api.add_box(name,mat,p[0],p[2],s[0],s[2],s[1],base=p[1]-s[1]/2)
        e=api.ELEMENTS[-1];e.update(position=list(p),size=list(s),noEdges=True)
        return e
    for room,pixels in SPOTS.items():
        for i,pixel in enumerate(pixels,1):
            x,z=position(pixel);ident=f'spot-{room.lower()}-{i:02}';prefix=f'PlanSpot_{room}_{i:02}'
            trim=disc(prefix+'_Trim','door_ivory',x,z,.105,.009,ceiling-.012)
            diffuser=disc(prefix+'_Diffuser','room_light',x,z,.076,.003,ceiling-.015)
            p=[x,ceiling-.040,z];light(p,.52 if room!='Bath' else .38,ident,fixture=ident)
            record(ident,'spot',room,pixel,p,[trim['name'],diffuser['name']])
    # One low-profile central fixture; diameter is provisional.
    x,z=position(CENTRAL);ident='study-central'
    trim=disc('PlanCentral_Study_Trim','door_ivory',x,z,.48,.065,ceiling-.07)
    diffuser=disc('PlanCentral_Study_Diffuser','room_light',x,z,.445,.006,ceiling-.076)
    p=[x,ceiling-.10,z];light(p,1.5,'Центральный свет кабинета',fixture=ident)
    record(ident,'central','Study',CENTRAL,p,[trim['name'],diffuser['name']])
    # Keep the selected sconce designs/heights; horizontal locations from plan.
    pixel=SCONCES['Kitchen'];_,z=position(pixel);old=api.resolved(node('KitchenSconce_Shade_'))
    for e in api.ELEMENTS:
        if e['name'].startswith('KitchenSconce'):
            r=api.resolved(e);p=list(r['position']);p[2]+=z-old['position'][2];put(e,position=p)
    p=[old['position'][0]+.10,old['position'][1],z];light(p,.32,'Бра у стола',fixture='sconce-kitchen')
    record('sconce-kitchen','sconce','Kitchen',pixel,p,[e['name'] for e in api.ELEMENTS if e['name'].startswith('KitchenSconce')])
    for prefix in ('BedsideLeft','BedsideRight'):
        pixel=SCONCES[prefix];x,_=position(pixel);original=api.resolved(node(prefix+'_LightBackplate_'))
        for e in api.ELEMENTS:
            if e['name'].startswith(prefix+'_Light'):
                r=api.resolved(e);p=list(r['position']);p[0]+=x-original['position'][0];put(e,position=p)
        shade=api.resolved(node(prefix+'_LightDiffuser_'));p=list(shade['position']);p[1]-=.025
        ident='sconce-'+prefix.lower();light(p,.22,prefix,fixture=ident)
        record(ident,'sconce','Bedroom',pixel,p,[e['name'] for e in api.ELEMENTS if e['name'].startswith(prefix+'_Light')])
    pixel=SCONCES['Study'];x,_=position(pixel);z=5.725;y=1.60
    plate=box('StudySconce_Plate','kitchen_ivory',[x,y,z+.013],[.10,.10,.025])
    arm=box('StudySconce_Arm','kitchen_ivory',[x,y,z+.065],[.024,.024,.08])
    shade=box('StudySconce_Shade','kitchen_opal',[x,y,z+.160],[.18,.18,.16]);shade['detail']=dict(type='pillow',power=2)
    p=[x,y,z+.26];light(p,.32,'Бра кабинета',fixture='sconce-study')
    record('sconce-study','sconce','Study',pixel,p,[e['name'] for e in (plate,arm,shade)])
    # Existing bath mirror stays aligned with the approved basin.
    mirror=api.resolved(node('BathroomMirror_'));x,y,z=mirror['position'];w,h,d=mirror['size']
    for dy,dz in ((h/2,0),(-h/2,0),(0,d/2),(0,-d/2)):
        light((x-.02,y+dy,z+dz),.14,'Подсветка зеркала',fixture='bath-mirror-led')
    record('bath-mirror-led','backlight','Bath',SUPPLIES['bath-mirror'],[x,y,z],
           [e['name'] for e in api.ELEMENTS if e['name'].startswith('BathMirrorLED')])
    # Entry mirror on the bathroom outer wall, clear of the laundry cabinet.
    x,_=position(SUPPLIES['entry-mirror']);z=1.225;y=1.50;w=.65;h=1.05
    mirror=box('EntryMirror_Glass','bath_mirror',[x,y,z-.018],[w,h,.012]);parts=[mirror['name']]
    for sign in (-1,1):
        parts.append(box('EntryMirror_LED','room_light',[x+sign*(w/2+.004),y,z-.014],[.008,h+.016,.012])['name'])
        parts.append(box('EntryMirror_LED','room_light',[x,y+sign*(h/2+.004),z-.014],[w,.008,.012])['name'])
        light([x+sign*w/3,y,z-.04],.21,'Подсветка зеркала прихожей',fixture='entry-mirror-led')
    record('entry-mirror-led','backlight','Entry',SUPPLIES['entry-mirror'],[x,y,z-.018],parts)
    # Physical L-shaped undercabinet strips; supply arrows are not luminaires.
    for raw in api.ELEMENTS:
        if not raw['name'].startswith('KitchenLED'):continue
        r=api.resolved(raw);x,y,z=r['position'];sx,_,sz=r['size'];count=4 if sz>sx else 2
        for i in range(count):
            t=(i+.5)/count-.5
            light([x+t*sx,y-.024,z+t*sz],.18,'Рабочая подсветка кухни',fixture='kitchen-led')
    record('kitchen-led','backlight','Kitchen',SUPPLIES['kitchen-led'],[8.746,1.509,5.60],
           [e['name'] for e in api.ELEMENTS if e['name'].startswith('KitchenLED')])
    api.LIGHTING_REFERENCE=dict(source='Освещение.png',referenceSize=[1630,1536],xAnchors=X_ANCHORS,zAnchors=Z_ANCHORS,
        note='40 отдельных спотов, 1 центральный светильник, 4 бра, 3 системы подсветки. Координаты по пропорциям, без размерных привязок. Размеры приборов, высоты бра, мощности/температура — предварительная визуализация, не светотехнический расчёт.')
    assert len(api.SCENE_LIGHTS)<=64
