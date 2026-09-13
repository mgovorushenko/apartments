"""Local finish-junction, doorway, bedding and hardware corrections, 12 September."""
import math

def put(api,e,**kw):
    e['finished']={**api.resolved(e),**kw};e['finished'].pop('finished',None)

def prepare_door(api):
    # 60 mm casing currently intersects the perpendicular study return.
    # Move the complete 945 mm rough opening 65 mm toward the sofa. Its width
    # is traced (not dimensioned in the PDF); all dimensioned room datums stay.
    shift=-.065
    for e in api.ELEMENTS:
        name=e['name']
        if name.startswith(('Door_Study','DoorJamb_Study','DoorHead_Study','Wall_StudyDoor','WallFinish_StudyDoor','FinishBeige_StudyLintel')) or 'Floor_StudyThreshold' in name:
            for r in (e,e.get('finished')):
                if not r:continue
                if 'position' in r:r['position']=[r['position'][0]+shift,*r['position'][1:]]
                if 'closed' in r:r['closed']={**r['closed'],'position':[r['closed']['position'][0]+shift,*r['closed']['position'][1:]]}
            if 'hinge' in e:e['hinge']=[e['hinge'][0]+shift,e['hinge'][1]]
        if name.startswith(('Wall_BedroomStudy','WallFinish_StudyNorth')):
            for r in (e,e.get('finished')):
                if not r:continue
                r['position']=[r['position'][0]+shift/2,*r['position'][1:]]
                r['size']=[r['size'][0]+shift,*r['size'][1:]]
    # New small hinge-side pier, entirely within the former opening.
    api.add_box('Wall_StudyHingePier','rough_wall',5.72+shift/2,5.67,-shift,.08,2.1,category='wall')
    for z,mat in [(5.6225,'wall_beige'),(5.7175,'wall_bluegray')]:
        api.add_box('StudyHingePierFinish',mat,5.72+shift/2,z,-shift,.015,2.082,base=.018,category='finish_wall')

def build(api):
    def node(prefix):return next(e for e in api.ELEMENTS if e['name'].startswith(prefix))
    def box(name,mat,p,s,detail=None,category='furniture'):
        api.add_box(name,mat,p[0],p[2],s[0],s[2],s[1],base=p[1]-s[1]/2,category=category)
        e=api.ELEMENTS[-1];e['noEdges']=True
        if detail:e['detail']=detail
        return e
    # Preserve the pet bed and remove only the animal.
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not (e['name'].startswith('Dog') and not e['name'].startswith('DogBed'))]
    # Cover spans the mattress with draped sides and foot, plus two flat pillows.
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith(('Bed_Cover','Bed_Throw','Bed_AccentPillow','Bed_CenterPillow'))]
    mat=api.resolved(node('Bed_Mattress_'));x,y,z=mat['position'];w,h,d=mat['size'];top=y+h/2
    for e in api.ELEMENTS:
        if e['name'].startswith('Bed_Pillow_'):
            r=api.resolved(e);put(api,e,position=[r['position'][0],top+.055,z-d/2+.26],size=[.72,.11,.43],detail=dict(type='pillow',power=5))
    box('Bed_Cover','bedroom_ivory',[x,top+.026,z+.16],[w+.08,.052,d-.28],dict(type='pillow',power=8))
    for sign in (-1,1):
        box('Bed_CoverDrape','bedroom_ivory',[x+sign*(w/2+.023),top-.13,z+.16],[.04,.31,d-.28],dict(type='curtain',folds=7),)
    box('Bed_CoverFoot','bedroom_ivory',[x,top-.13,z+d/2+.01],[w+.08,.31,.045],dict(type='curtain',folds=9))
    box('Bed_Throw','bedroom_navy',[x,top+.058,z+d/2-.31],[w+.075,.035,.44],dict(type='pillow',power=8))
    # Fill the complete return behind the kettle up to the long splash.
    splash_node=next((e for e in api.ELEMENTS if e['name'].startswith('KitchenBacksplashReturn')),None)
    if splash_node:
        splash=api.resolved(splash_node)
        lo=splash['position'][0]-splash['size'][0]/2;hi=9.074
        put(api,splash_node,position=[(lo+hi)/2,*splash['position'][1:]],size=[hi-lo,*splash['size'][1:]])
    # Hardware follows each leaf's two transforms; it is hidden in rough mode.
    api.MATERIALS['door_handle_satin']=dict(color=[.48,.49,.48,1],roughness=.32,metallic=.7)
    for door in list(api.ELEMENTS):
        if door['category']!='door' or not door['name'].startswith('Door_'):continue
        r=api.resolved(door);width,_,depth=r['size'];room=door['name'].split('_')[1]
        for side in (-1,1):
            for part,lx,ly,lz,s in [
                ('Rose',width/2-.085,1.015,side*(depth/2+.006),[.052,.052,.012]),
                ('Stem',width/2-.085,1.015,side*(depth/2+.025),[.018,.018,.04]),
                ('Lever',width/2-.135,1.015,side*(depth/2+.047),[.115,.018,.020]),
            ]:
                def pose(p,a):return [p[0]+lx*math.cos(a)+lz*math.sin(a),ly,p[2]-lx*math.sin(a)+lz*math.cos(a)]
                a=r.get('rotation',0);p=pose(r['position'],a)
                e=box('DoorHandle_'+room+'_'+part,'door_handle_satin',p,s,dict(type='rounded',radius=.005,steps=2),'door_hardware')
                e.update(rotation=a,closed=dict(position=pose(r['closed']['position'],r['closed']['rotation']),rotation=r['closed']['rotation']))
    miter_finishes(api)

def miter_finishes(api):
    """Join perpendicular finish strips along a shared diagonal in plan.

    Underlying survey blocks stay unchanged. Same geometry is exported and
    rendered. No extra corner cap/z-fighting or recess between exposed faces.
    """
    layers=[]
    for e in api.ELEMENTS:
        r=api.resolved(e);name=e['name']
        if not name.startswith(('WallFinish_','FinishBeige_','TileBacking_')):continue
        axis=0 if r['size'][0]<r['size'][2] else 2;along=2-axis
        sign=r.get('surface',{}).get('sign',-1 if any(t in name for t in ('East','South','BedroomDoor')) else 1)
        if 'StudyDoor' in name:sign=1
        p=r['position'];s=r['size'];at=p[axis]-sign*s[axis]/2
        polygon=[[p[0]-s[0]/2,p[2]-s[2]/2],[p[0]+s[0]/2,p[2]-s[2]/2],[p[0]+s[0]/2,p[2]+s[2]/2],[p[0]-s[0]/2,p[2]+s[2]/2]]
        layers.append(dict(e=e,r=r,axis=axis,along=along,sign=sign,at=at,out=at+sign*s[axis],lo=p[along]-s[along]/2,hi=p[along]+s[along]/2,poly=polygon,changed=False))
    count=0
    for i,a in enumerate(layers):
        for b in layers[i+1:]:
            if a['axis']==b['axis']:continue
            if abs(a['r']['position'][1]-b['r']['position'][1])>.001 or abs(a['r']['size'][1]-b['r']['size'][1])>.001:continue
            if min(abs(a['at']-b[k]) for k in ('lo','hi'))>.002 or min(abs(b['at']-a[k]) for k in ('lo','hi'))>.002:continue
            for face,other in ((a,b),(b,a)):
                axis=face['axis']//2;along=face['along']//2
                for v in face['poly']:
                    if abs(v[axis]-face['out'])<.0001 and abs(v[along]-other['at'])<.002:
                        v[along]=other['out'];face['changed']=True
            count+=1
    for face in layers:
        if not face['changed']:continue
        r=face['r'];p=list(r['position']);s=list(r['size'])
        for axis,k in ((0,0),(2,1)):
            lo=min(v[k] for v in face['poly']);hi=max(v[k] for v in face['poly'])
            p[axis]=(lo+hi)/2;s[axis]=hi-lo
        outline=[[(v[0]-p[0])/s[0],(v[1]-p[2])/s[2]] for v in face['poly']]
        put(api,face['e'],position=p,size=s,detail=dict(type='miter',outline=outline),noEdges=True)
    api.FINISH_MITER_COUNT=count
