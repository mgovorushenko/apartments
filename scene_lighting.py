"""Illustrative point/area-light samples for realtime day/evening comparison."""


def build(api):
    api.SCENE_LIGHTS=[]
    ceiling=2.8-api.FINISH_SETTINGS['ceiling_drop']
    api.MATERIALS['room_light']=dict(color=[1,.92,.79,1],roughness=.5,metallic=0,pattern=4)
    api.MATERIALS['bedroom_lamp']['pattern']=4
    for x,z in ((1.35,4.10),(3.40,4.10),(3.35,6.45),(3.35,7.95)):
        api.add_cylinder('RoomCeilingLight_Trim','door_ivory',x,z,.30,.035,base=ceiling-.04)
        api.ELEMENTS[-1]['noEdges']=True
        api.add_cylinder('RoomCeilingLight_Diffuser','room_light',x,z,.265,.004,base=ceiling-.044)
        api.ELEMENTS[-1]['noEdges']=True
    def light(position,power,color=(1,.90,.76),label=''):
        api.SCENE_LIGHTS.append(dict(position=list(position),power=power,color=list(color),label=label))
    for raw in api.ELEMENTS:
        e=api.resolved(raw);n=e['name'];x,y,z=e['position']
        if n.startswith(('KitchenCeilingLight_Diffuser','RoomCeilingLight_Diffuser','BathCeilingLight_Diffuser')):
            bath=n.startswith('Bath');room=n.startswith('Room')
            light((x,y-.025,z),.75 if bath else 1.65 if room else .95,(1,.94,.85) if bath else (1,.90,.76),n)
        if n.startswith(('BedsideLeft_LightDiffuser','BedsideRight_LightDiffuser')):light((x,y-.025,z),.22,label=n)
    # Four low-power area-light samples around mirror; never inside the wall.
    mirror=api.resolved(next(e for e in api.ELEMENTS if e['name'].startswith('BathroomMirror_')))
    x,y,z=mirror['position'];w,h,d=mirror['size']
    for dy,dz in ((h/2,0),(-h/2,0),(0,d/2),(0,-d/2)):
        light((x-.02,y+dy,z+dz),.14,(1,.95,.86),'Подсветка зеркала')
    for z in (4.65,5.45,6.25,6.9):light((8.88,1.49,z),.18,label='Рабочая подсветка кухни')
    light((6.185,1.51,6.175),.32,(1,.94,.84),label='Бра у стола')
    assert len(api.SCENE_LIGHTS)<=32
