"""Static joinery, soft goods and curated wall art — September 13 local revision."""
import math
import base64
from pathlib import Path
from PIL import Image


def build(api):
    def node(prefix):return next(e for e in api.ELEMENTS if e['name'].startswith(prefix))
    def put(e,**kw):
        e['finished']={**api.resolved(e),**kw};e['finished'].pop('finished',None)
    def box(name,mat,p,s,detail=None,category='furniture'):
        api.add_box(name,mat,p[0],p[2],s[0],s[2],s[1],base=p[1]-s[1]/2,category=category)
        e=api.ELEMENTS[-1];e.update(position=list(p),size=list(s),noEdges=True)
        if detail:e['detail']=detail
        return e
    def rounded(name,mat,p,s,r=.003):return box(name,mat,p,s,dict(type='rounded',radius=r,steps=2))
    def rod(name,mat,a,b,r=.003):
        p=[(a[i]+b[i])/2 for i in range(3)];s=[abs(a[i]-b[i])+r*2 for i in range(3)]
        return box(name,mat,p,s,dict(type='rod',radius=r,start=[(a[i]-p[i])/s[i] for i in range(3)],end=[(b[i]-p[i])/s[i] for i in range(3)]))
    floor=api.FINISH_SETTINGS['dry_floor']
    for e in api.ELEMENTS:
        n=e['name'];r=api.resolved(e);p=list(r['position']);s=list(r['size'])
        if n.startswith('Furniture_DiningChair') and '_leg_' in n:
            seat=api.resolved(node(n.split('_leg_')[0]+'_seat_'))
            top=seat['position'][1]-seat['size'][1]/2+.008
            p[1]=(floor+top)/2;s[1]=top-floor
            put(e,position=p,size=s)
        if n.startswith('Bed_Frame_'):
            top=p[1]+s[1]/2;p[1]=(floor+top)/2;s[1]=top-floor
            put(e,position=p,size=s,detail=dict(type='rounded',radius=.006,steps=2))
        if n.startswith(('GuitarBody','GuitarHead','GuitarNeck','GuitarBridge')):put(e,material='dark')

    # Move the complete vase/branches assembly, preserving contact with tabletop.
    vase=api.resolved(node('KitchenCoffeeDecor_Vase'))
    table=api.resolved(node('Furniture_DiningTable_top'))
    target=[table['position'][0]-.08,table['position'][1]+table['size'][1]/2+vase['size'][1]/2,table['position'][2]+.08]
    delta=[target[i]-vase['position'][i] for i in range(3)]
    for e in api.ELEMENTS:
        if e['name'].startswith('KitchenCoffeeDecor'):
            r=api.resolved(e);put(e,position=[r['position'][i]+delta[i] for i in range(3)])

    # Finish the 90 mm structural step on the study side, including its skirting.
    returnwall=api.resolved(node('Wall_StudyEastReturn_'));east=api.resolved(node('Wall_StudyEast_'))
    x0=returnwall['position'][0]-returnwall['size'][0]/2-.015
    x1=east['position'][0]-east['size'][0]/2
    z=returnwall['position'][2]+returnwall['size'][2]/2
    box('StudyReturnStepFinish','study_sage',[(x0+x1)/2,(floor+2.753)/2,z+.0075],[x1-x0,2.753-floor,.015],category='finish_wall')
    box('Skirting_StudyReturnStep','door_ivory',[(x0+x1)/2,floor+.02,z+.019],[x1-x0,.04,.008],category='finish_wall')

    # All laundry fronts share a plane and a common transom height.
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not (
        e['name'].startswith(('LaundryStorageFacade','LaundryUpperStorageFacade','LaundryApplianceFacade'))
        or (e['name'].startswith(('LaundryStorage','LaundryUpperStorage')) and '_Handle_' in e['name']))]
    for side,(lo,hi) in enumerate(((.027,.595),(.605,1.215))):
        for tier,(bottom,top) in enumerate(((floor+.064,1.906),(1.912,2.646))):
            rounded('LaundryUnifiedFacade','kitchen_ivory',[8.4231,(bottom+top)/2,(lo+hi)/2],[.018,top-bottom,hi-lo],.001)
            zhandle=hi-.045 if side==0 else lo+.045
            yhandle=1.11 if tier==0 else 2.07
            # Narrow dark finger recess; no protruding mismatched bars.
            rounded('LaundryUnifiedPull','kitchen_joint',[8.4135,yhandle,zhandle],[.0012,.18,.012],.0004)

    # Reuse the bedroom fixture construction and its existing light circuit.
    source=[e for e in api.ELEMENTS if e['name'].startswith('BedsideLeft_Light')]
    plate=api.resolved(node('BedsideLeft_LightBackplate_'));origin=plate['position']
    for prefix,angle,anchor,ident in (
        ('KitchenSconce',math.pi/2,api.resolved(node('KitchenSconce_Plate_'))['position'],'sconce-kitchen'),
        ('StudySconce',0,api.resolved(node('StudySconce_Plate_'))['position'],'sconce-study')):
        api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith(prefix)]
        members=[];c=math.cos(angle);s=math.sin(angle)
        for e in source:
            r=api.resolved(e);q=[r['position'][i]-origin[i] for i in range(3)]
            p=[anchor[0]+q[0]*c+q[2]*s,anchor[1]+q[1],anchor[2]-q[0]*s+q[2]*c]
            label=e['name'].split('_Light')[1].rsplit('_',1)[0].replace('Backplate','Plate')
            part=box(prefix+'_'+label,r['material'],p,r['size'],r.get('detail'))
            part.update(rotation=angle,lightingId=ident);members.append(part)
        diffuser=next(e for e in members if 'Diffuser' in e['name']);p=list(diffuser['position']);p[1]-=.026
        for light in api.SCENE_LIGHTS:
            if light['fixture']==ident:light['position']=p
        for record in api.LIGHTING_LAYOUT:
            if record['id']==ident:record.update(position=p,elements=[e['name'] for e in members])

    # Cloth volumes with shaped shoulders, curved seams and small closures.
    for e in list(api.ELEMENTS):
        r=api.resolved(e);n=e['name'];p=r['position'];s=r['size']
        if n.startswith('EntryCoatJacketBody'):
            put(e,detail=dict(type='rounded',radius=.022,steps=3))
            front=p[0]+s[0]/2+.002;bottom=p[1]-s[1]/2
            for side in (-1,1):
                rod('EntryCoatHemSeam',r['material'],[front,bottom+.016,p[2]+side*.08],[front,bottom+.021,p[2]],.0015)
                rounded('EntryCoatPocketFlap',r['material'],[front+.003,bottom+.23,p[2]+side*.065],[.012,.025,.058],.005)
            for j in range(5):
                box('EntryCoatButton','dark',[front+.006,bottom+.12+j*.10,p[2]],[.008,.010,.010],dict(type='pillow',power=2))
        elif n.startswith(('EntryCoatSleeve','EntryCoatShoulder','EntryCoatCollar')):
            put(e,detail=dict(type='pillow',power=3))
        elif n.startswith('EntryCoatShoeUpper'):
            put(e,detail=dict(type='pillow',power=3))
            rounded('EntryCoatShoeHeel',r['material'],[p[0]-.088,p[1]+.022,p[2]],[.068,.075,.059],.012)
            box('EntryCoatShoeOpening','dark',[p[0]-.083,p[1]+.059,p[2]],[.044,.003,.040],dict(type='pillow',power=3))
            for j in range(4):
                rod('EntryCoatShoeLace','door_ivory',[p[0]-.035+j*.018,p[1]+.025,p[2]-.018],[p[0]-.025+j*.018,p[1]+.027,p[2]+.018],.0014)
        elif n.startswith('EntryCoatShoeSole'):put(e,detail=dict(type='rounded',radius=.007,steps=2))

    skirting(api,put)
    wall_art(api,box)


def skirting(api,put):
    """Snap ends to casings, then share a 45-degree diagonal at each L junction."""
    def edge(r,a,sign):return r['position'][a]+sign*r['size'][a]/2
    trims=[api.resolved(e) for e in api.ELEMENTS if e['name'].startswith('DoorCasing_') and '_Top_' not in e['name']]
    strips=[]
    for e in api.ELEMENTS:
        if not e['name'].startswith('Skirting_'):continue
        r=api.resolved(e);p=list(r['position']);s=list(r['size']);along=0 if s[0]>s[2] else 2;normal=2-along
        lo,hi=edge(r,along,-1),edge(r,along,1);locked=set()
        for end in (-1,1):
            at=lo if end<0 else hi;candidates=[]
            for t in trims:
                if min(edge(r,normal,1),edge(t,normal,1))-max(edge(r,normal,-1),edge(t,normal,-1))<-.012:continue
                target=edge(t,along,-end)
                if abs(target-at)<.065 and (target<hi-.004 if end<0 else target>lo+.004):candidates.append(target)
            if candidates:
                target=min(candidates,key=lambda v:abs(v-at))
                if end<0:lo=target
                else:hi=target
                locked.add(end)
        p[along]=(lo+hi)/2;s[along]=hi-lo
        poly=[[p[0]-s[0]/2,p[2]-s[2]/2],[p[0]+s[0]/2,p[2]-s[2]/2],[p[0]+s[0]/2,p[2]+s[2]/2],[p[0]-s[0]/2,p[2]+s[2]/2]]
        strips.append(dict(e=e,p=p,s=s,along=along,poly=poly,locked=locked))
    count=0
    for i,a in enumerate(strips):
        for b in strips[i+1:]:
            if a['along']==b['along']:continue
            h,v=(a,b) if a['along']==0 else (b,a)
            ix,iz=v['p'][0],h['p'][2]
            eh=-1 if ix<h['p'][0] else 1;ev=-1 if iz<v['p'][2] else 1
            if eh in h['locked'] or ev in v['locked']:continue
            if abs(h['p'][0]+eh*h['s'][0]/2-ix)>.042 or abs(v['p'][2]+ev*v['s'][2]/2-iz)>.042:continue
            slope=eh/ev
            for q in h['poly']:
                if abs(q[0]-(h['p'][0]+eh*h['s'][0]/2))<1e-6:q[0]=ix+slope*(q[1]-iz)
            for q in v['poly']:
                if abs(q[1]-(v['p'][2]+ev*v['s'][2]/2))<1e-6:q[1]=iz+(q[0]-ix)/slope
            count+=1
    for a in strips:
        p=a['p'];s=a['s']
        for axis,k in ((0,0),(2,1)):
            lo=min(q[k] for q in a['poly']);hi=max(q[k] for q in a['poly']);p[axis]=(lo+hi)/2;s[axis]=hi-lo
        outline=[[(q[0]-p[0])/s[0],(q[1]-p[2])/s[2]] for q in a['poly']]
        diagonal=any(abs(u[0]-v[0])>1e-6 and abs(u[1]-v[1])>1e-6 for u,v in zip(outline,outline[1:]+outline[:1]))
        put(a['e'],position=p,size=s,detail=dict(type='miter',outline=outline) if diagonal else None,noEdges=True)
    api.SKIRTING_MITER_COUNT=count


def wall_art(api,box):
    assets=Path(__file__).with_name('assets')
    im=Image.open(assets/'artwork-atlas.png').convert('RGB')
    api.ARTWORK=dict(width=im.width,height=im.height,pixels=base64.b64encode(im.tobytes()).decode(),source='assets/artwork-atlas.png')
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith('BedroomArt')]
    for e in api.ELEMENTS:
        if e.get('artwork'):e['artwork']={**e['artwork'],'region':[.002,.002,.496,.496]}
    def frame(name,x,y,z,w,h,tile,ratio):
        box(name+'_Backing','bedroom_ivory',[x,y,z],[w,h,.016])
        for sign in (-1,1):
            box(name+'_Frame','study_oak',[x+sign*(w/2-.009),y,z+.010],[.018,h,.026])
            box(name+'_Frame','study_oak',[x,y+sign*(h/2-.009),z+.010],[w-.036,.018,.026])
        photo=box(name+'_Photo','photo_print',[x,y,z+.019],[w-.045,h-.045,.001])
        photo['artwork']=dict(axis=2,along=0,sign=1,ratio=ratio,region=tile)
    # Calm seascape centred on the headboard; one focal point instead of scattered frames.
    frame('BedroomArtHeadboard',2.05,1.91,2.732,1.08,.70,[.502,.002,.496,.496],1174/750)
    # Mountain landscape balanced against the sconce on the left of the study sofa.
    frame('StudyArtLandscape',3.68,1.79,5.739,.98,.62,[.002,.502,.496,.496],3993/2387)
