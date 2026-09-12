"""White wall cores, terracotta exterior skins, real-depth window profiles and tucked chairs."""
import math

def build(api):
    api.MATERIALS['wall_white']=dict(color=[.97,.965,.95,1],roughness=.9,metallic=0)
    api.MATERIALS['facade_terracotta']=dict(color=[.62,.30,.20,1],roughness=.95,metallic=0)
    api.MATERIALS['window_white']=dict(color=[.96,.96,.94,1],roughness=.5,metallic=0)
    api.MATERIALS['glass']['color']=[.72,.85,.89,.13]
    def put(e,**kw):e['finished']={**e.get('finished',{}),**kw}
    exterior={
      'Wall_WestEntry':(0,-1),'Wall_NorthEntry':(2,-1),'Wall_EntryLintel':(2,-1),
      'Wall_EastExterior':(0,1),'Wall_BedroomNorth':(2,-1),
      'Wall_BedroomWest':(0,-1),'BedroomWest_':(0,-1),
      'Wall_BedroomSouthExterior':(2,1),'Wall_StudyWest':(0,-1),'StudyWest_':(0,-1),
      'Wall_South':(2,1),'StudySouth_':(2,1),'KitchenSouth_':(2,1)}
    for e in list(api.ELEMENTS):
        r=api.resolved(e)
        if e['category']=='wall':
            put(e,material='wall_white')
            for prefix,(axis,sign) in exterior.items():
                if not e['name'].startswith(prefix):continue
                p=list(r['position']);s=list(r['size']);p[axis]+=sign*(s[axis]/2+.0015);s[axis]=.003
                api.add_box('Facade_'+e['name'],'facade_terracotta',p[0],p[2],s[0],s[2],s[1],base=p[1]-s[1]/2,category='finish_wall')
                break
        if e['category']=='window':
            axis=0 if 'West_' in e['name'] else 2
            p=list(r['position']);s=list(r['size']);s[axis]=.006 if '_glass_' in e['name'] else .07
            e.update(position=p,size=s,material='glass' if '_glass_' in e['name'] else 'window_white')
            e.pop('finished',None)
            if '_glass_' in e['name']:
                # Sill spans from the frame to 40 mm inside the finished wall.
                sign=1 if axis==0 else -1;sp=list(p);ss=list(s);ss[axis]=.535/2+.04;ss[1]=.025
                sp[axis]+=sign*(ss[axis]/2-.035);sp[1]=.84
                ss[2 if axis==0 else 0]+=.07
                api.add_box('WindowSill_'+e['name'],'window_white',sp[0],sp[2],ss[0],ss[2],ss[1],base=sp[1]-ss[1]/2,category='window')
    table=api.resolved(next(e for e in api.ELEMENTS if e['name'].startswith('Furniture_DiningTable_top')))
    cx,_,cz=table['position']
    # Three seats at 120-degree intervals, radius reduced from 566 to 490 mm.
    for ident,theta in [(1,math.pi),(3,math.pi/3),(4,-math.pi/3)]:
        prefix=f'Furniture_DiningChair{ident}_'
        old=api.resolved(next(e for e in api.ELEMENTS if e['name'].startswith(prefix+'seat_')))
        target=[cx+.49*math.cos(theta),cz+.49*math.sin(theta)]
        angle=math.atan2(target[0]-cx,target[1]-cz);delta=angle-old.get('rotation',0)
        for e in api.ELEMENTS:
            if not e['name'].startswith(prefix):continue
            r=api.resolved(e);dx=r['position'][0]-old['position'][0];dz=r['position'][2]-old['position'][2]
            put(e,position=[target[0]+dx*math.cos(delta)+dz*math.sin(delta),r['position'][1],target[1]-dx*math.sin(delta)+dz*math.cos(delta)],rotation=r.get('rotation',0)+delta)
