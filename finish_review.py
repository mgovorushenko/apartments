"""Coordinated material/ergonomics review, applied only to the local model."""
import math
import copy


def build(api):
    def node(prefix):return next(e for e in api.ELEMENTS if e['name'].startswith(prefix))
    def put(e,**kw):
        e['finished']={**api.resolved(e),**kw};e['finished'].pop('finished',None)
    def box(name,mat,p,s,detail=None,category='furniture'):
        api.add_box(name,mat,p[0],p[2],s[0],s[2],s[1],base=p[1]-s[1]/2,category=category)
        e=api.ELEMENTS[-1];e.update(position=list(p),size=list(s),noEdges=True)
        if detail:e['detail']=detail
        return e
    def rounded(name,mat,p,s,r=.004):return box(name,mat,p,s,dict(type='rounded',radius=r,steps=3))
    def rod(name,mat,a,b,r=.005):
        p=[(a[i]+b[i])/2 for i in range(3)];s=[abs(a[i]-b[i])+2*r for i in range(3)]
        return box(name,mat,p,s,dict(type='rod',radius=r,start=[(a[i]-p[i])/s[i] for i in range(3)],end=[(b[i]-p[i])/s[i] for i in range(3)]))
    floor=api.FINISH_SETTINGS['dry_floor'];ceiling=2.8-api.FINISH_SETTINGS['ceiling_drop']
    api.MATERIALS['review_cork']=dict(color=[.57,.40,.24,1],roughness=1,metallic=0,pattern=3)
    api.MATERIALS['review_mesh']=dict(color=[.23,.25,.25,1],roughness=.95,metallic=0,pattern=12)
    for name in ('KitchenRug','BedroomRug','StudyRug'):
        for e in api.ELEMENTS:
            if e['name'].startswith(name):
                r=api.resolved(e);key='rug_review_'+r['material']
                api.MATERIALS[key]={**api.MATERIALS[r['material']],'pattern':12}
                put(e,material=key)
    for e in list(api.ELEMENTS):
        r=api.resolved(e);n=e['name'];mat=r['material']
        if r['category']=='furniture' and (api.MATERIALS[mat].get('pattern')==1 or
                (n.startswith('EntryWardrobe') and not any(t in n for t in ('Recess','Track','Handle','Joint','Plinth')))):
            put(e,material='kitchen_oak')
        if 'Worktop' in n and mat=='kitchen_stone':put(e,material='kitchen_oak')
        if n.startswith('HallWardrobeSlidingDoor'):
            put(e,material='bath_mirror')
        if n in ('Kettle_001','Kettle_Lid_001') or n.startswith('Kettle_LidGrip'):put(e,material='white')
        if n.startswith('StudySofa_Accent'):
            s=list(r['size']);s[0]=s[1]=.45;s[2]=.15;put(e,size=s,position=[r['position'][0],.78,r['position'][2]])
        if n.startswith('WindowSill_'):put(e,material='stone_gray_1')
        if n.startswith(('InteriorReveal','InteriorWindowPaint')):
            mat='bedroom_render_blue' if 'Bedroom' in n else 'study_sage' if 'Study' in n else 'wall_beige'
            put(e,material=mat)
        if n.startswith('LaundryUnifiedPull'):
            p=list(r['position']);p[0]=8.399
            put(e,position=p,size=[.024,.18,.014],material='door_handle_satin',detail=dict(type='rounded',radius=.004,steps=3))
            for dy in (-.071,.071):rounded('LaundryPullMount','door_handle_satin',[8.417,p[1]+dy,p[2]],[.02,.012,.014],.003)
        if n in ('TVConsole_001','TVConsole_002','TVConsole_003'):
            p=list(r['position']);s=list(r['size']);index=int(n.rsplit('_',1)[1]);s[2]-=.004 if index==2 else .002
            if index!=2:p[2]+=-.001 if index==1 else .001
            front=p[0]-s[0]/2;s[0]-=.018;p[0]+=.009
            put(e,material='kitchen_oak',position=p,size=s)
            rounded('TVConsole_Facade','kitchen_ivory',[front+.009,p[1],p[2]],[.018,s[1]-.004,s[2]-.002],.001)
        if r['category']=='wall' and mat=='facade_terracotta':
            p=list(r['position']);p[1]+=r['size'][1]/2+.0005
            box('ExteriorWallWhiteTop','wall_white',p,[r['size'][0],.001,r['size'][2]],category='finish_wall')

    # Exposed 80 mm end of the bathroom north wall, right of the entry mirror.
    west=api.resolved(node('FinishBeige_BathOuterWest_'));thick=west['size'][0]
    box('EntryMirrorCornerFinish','wall_beige',[west['position'][0],(floor+ceiling+.003)/2,1.2725],[thick,ceiling+.003-floor,.095],
        dict(type='miter',outline=[[-.5,-.5],[.5,-.5+.015/.095],[.5,.5],[-.5,.5]]),category='finish_wall')
    north=node('FinishBeige_BathOuterNorth_');r=api.resolved(north);p=list(r['position']);s=list(r['size']);p[0]-=thick/2;s[0]+=thick
    put(north,position=p,size=s,detail=dict(type='miter',outline=[[-.5,-.5],[.5,-.5],[.5,.5],[-.5+thick/s[0],.5]]))
    # Enlarge shoes as coherent pairs, including the previously added laces.
    for e in api.ELEMENTS:
        if not e['name'].startswith('EntryCoatShoe'):continue
        r=api.resolved(e);p=list(r['position']);s=list(r['size']);z=p[2]
        pair=.235 if z<.4 else .585;old=.19 if z<.235 else .28 if z<.4 else .54 if z<.585 else .63
        new=pair+(-.057 if old<pair else .057)
        p[2]=new+(z-old)*1.5;s[2]*=1.5;put(e,position=p,size=s)

    # Desk remains against the same wall; only its depth and front legs advance.
    desk=api.resolved(node('ComputerDesk_'));back=desk['position'][2]+desk['size'][2]/2
    p=list(desk['position']);s=list(desk['size']);p[2]=back-.40;s[2]=.80
    put(node('ComputerDesk_'),position=p,size=s)
    for e in api.ELEMENTS:
        if e['name'].startswith('DeskLeg'):
            r=api.resolved(e);q=list(r['position']);q[2]=back-(back-q[2])*(.8/.6);put(e,position=q)
    chair(api,box,rounded,rod,desk['position'][0],7.62,floor)
    piano(api,box,rounded,rod)
    # Smooth the acoustic silhouette using a monotone cubic radius profile.
    guitar=node('GuitarBody');r=api.resolved(guitar)
    old=[[0,-.5],[.23,-.485],[.4,-.43],[.485,-.32],[.5,-.20],[.46,-.08],[.33,.06],[.285,.15],[.31,.22],[.36,.31],[.355,.39],[.25,.465],[0,.5]]
    rings=[]
    for i in range(len(old)-1):
        a,b=old[i],old[i+1]
        for j in range(8):
            t=j/8;dy=b[1]-a[1];prev=old[max(0,i-1)];nxt=old[min(len(old)-1,i+2)]
            ma=(b[0]-prev[0])/(b[1]-prev[1]);mb=(nxt[0]-a[0])/(nxt[1]-a[1])
            radius=(2*t**3-3*t*t+1)*a[0]+(t**3-2*t*t+t)*dy*ma+(-2*t**3+3*t*t)*b[0]+(t**3-t*t)*dy*mb
            rings.append([min(.5,max(0,radius)),a[1]+dy*t])
    rings.append(old[-1]);put(guitar,material='dark',detail=dict(type='lathe',rings=rings,segments=64))

    bowls(api,box,rounded,rod,floor)
    # Cork board over the bowls; small prints are placeholders, no personal photos.
    rounded('EntryMemoBoard','kitchen_oak',[4.813,1.47,4.12],[.026,.48,.62],.008)
    rounded('EntryMemoCork','review_cork',[4.829,1.47,4.12],[.007,.45,.59],.005)
    for j,(z,y) in enumerate(((3.96,1.53),(4.15,1.42),(4.29,1.56))):
        box('EntryMemoNote','bedroom_ivory',[4.834,y,z],[.001,.13,.105])
        rounded('EntryMemoPin','door_handle_satin',[4.84,y+.05,z],[.010,.012,.012],.005)
        if j!=1:
            photo=box('EntryMemoPhoto','photo_print',[4.835,y,z],[.001,.098,.085])
            photo['artwork']=dict(axis=0,along=2,sign=1,region=[.002,.002,.496,.496])
    # Recess the luminous disks inside each shade and strengthen existing sources.
    for prefix in ('BedsideLeft_Light','BedsideRight_Light','KitchenSconce_','StudySconce_'):
        shade=api.resolved(node(prefix+'Shade'));diff=node(prefix+'Diffuser');r=api.resolved(diff)
        p=list(shade['position']);p[1]-=shade['size'][1]/2-.012
        put(diff,position=p,size=[.086,.003,.086])
    for light in api.SCENE_LIGHTS:
        if light['fixture'].startswith('sconce-'):light['power']*=1.65
    baskets(api,put)
    # The curtains occupy the whole finished south wall, with a continuous rail.
    x0,x1=5.935,9.045
    for e in api.ELEMENTS:
        if not e['name'].startswith('Curtain_KitchenSouth'):continue
        r=api.resolved(e);p=list(r['position']);s=list(r['size'])
        if 'LeftPanel' in e['name']:s[0]=.66;p[0]=x0+.33
        elif 'RightPanel' in e['name']:s[0]=.66;p[0]=x1-.33
        else:
            lo,hi=6.20415,8.3482
            p[0]=x0+(p[0]-lo)/(hi-lo)*(x1-x0);s[0]*=(x1-x0)/(hi-lo)
        if 'Tulle' in e['name']:p[0]=(x0+x1)/2;s[0]=x1-x0
        put(e,position=p,size=s)
    floorboards(api,box,put)
    # Two white folded-metal trays on the west wall, opposite the shower.
    for y in (1.45,1.80):
        rounded('BathShelf_Base','white',[7.34,y,1.70],[.12,.006,.42],.003)
        rounded('BathShelf_Back','white',[7.283,y+.035,1.70],[.006,.076,.42],.003)
        box('BathShelf_Lip','white',[7.397,y+.022,1.70],[.006,.06,.42],dict(type='pillow',power=4))
        for sign in (-1,1):rounded('BathShelf_End','white',[7.34,y+.022,1.70+sign*.207],[.12,.05,.006],.003)
    # Updated palette-specific prints; keep the approved locations and frames.
    for e in api.ELEMENTS:
        if e.get('artwork') and e['name'].startswith('BedroomArt'):e['artwork']['ratio']=2342/2250
        if e.get('artwork') and e['name'].startswith('StudyArt'):e['artwork']['ratio']=1800/1297
    reduce_door_opening(api,put)


def floorboards(api,box,put):
    # Restore the approved bedroom oak and its visible individual board edges.
    # Keep the same material family throughout all dry rooms.
    for i in range(3):
        api.MATERIALS['kitchen_floor_'+str(i)] = dict(api.MATERIALS['bedroom_render_floor_'+str(i)])
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith('FloorPlank_')]
    for e in list(api.ELEMENTS):
        r=api.resolved(e)
        if not e['name'].startswith('Finish_Floor_') or not r['material'].startswith('kitchen_floor'):continue
        p=r['position'];s=r['size'];x0,x1=p[0]-s[0]/2,p[0]+s[0]/2;z0,z1=p[2]-s[2]/2,p[2]+s[2]/2
        for ix in range(math.floor(x0/.20),math.ceil(x1/.20)):
            a=max(x0,ix*.20+.0009);b=min(x1,(ix+1)*.20-.0009);offset=(ix%3)*.4
            for iz in range(math.floor((z0-offset)/1.20),math.ceil((z1-offset)/1.20)):
                c=max(z0,iz*1.20+offset+.0009);d=min(z1,(iz+1)*1.20+offset-.0009)
                if b-a<.002 or d-c<.002:continue
                plank=box('FloorPlank','kitchen_floor_'+str((ix*7+iz*5)%3),
                    [(a+b)/2,api.FINISH_SETTINGS['dry_floor']-.0002,(c+d)/2],
                    [b-a,.0004,d-c],category='finish_floor')
                plank['noEdges']=False


def chair(api,box,rounded,rod,x,z,floor):
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith('Furniture_Study')]
    prefix='Furniture_Study_'
    def r(name,mat,p,s,radius=.008):return rounded(prefix+name,mat,p,s,radius)
    r('SeatShell','dark',[x,.457,z],[.49,.035,.46],.015)
    box(prefix+'seat','study_charcoal',[x,.49,z],[.48,.085,.45],dict(type='pillow',power=5))
    r('BackFrame','dark',[x,.865,z-.224],[.49,.58,.065],.024)
    box(prefix+'BackMesh','review_mesh',[x,.87,z-.184],[.436,.522,.016],dict(type='bow',radius=.004))
    r('Lumbar','dark',[x,.715,z-.21],[.32,.07,.05],.025)
    rod(prefix+'GasLift','door_handle_satin',[x,floor+.08,z],[x,.42,z],.027)
    for side in (-1,1):
        rod(prefix+'ArmSupport','dark',[x+side*.26,.45,z-.04],[x+side*.26,.66,z-.04],.016)
        r('Armrest','dark',[x+side*.26,.675,z],[.064,.032,.24],.014)
    for i in range(5):
        a=i*math.tau/5;cx=x+.30*math.cos(a);cz=z+.30*math.sin(a)
        rod(prefix+'BaseSpoke','dark',[x,.12,z],[cx,.078,cz],.018)
        for side in (-1,1):box(prefix+'Caster','dark',[cx+side*.016,floor+.028,cz],[.023,.056,.056],dict(type='pillow',power=3))
    rod(prefix+'HeightLever','dark',[x+.06,.405,z],[x+.24,.405,z],.008)


def piano(api,box,rounded,rod):
    old=api.resolved(next(e for e in api.ELEMENTS if e['name']=='Piano_001'))
    z=old['position'][2];floor=api.FINISH_SETTINGS['dry_floor'];back=old['position'][0]+old['size'][0]/2;front=back-.45
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith('Piano')]
    def r(name,p,s,mat='dark',radius=.005):return rounded('Piano'+name,mat,p,s,radius)
    r('_001',[(front+back)/2,.77,z],[.45,.14,1.4])
    for sign in (-1,1):r('SideLeg',[(front+back)/2,(floor+.75)/2,z+sign*.676],[.43,.75-floor,.048])
    r('RearBrace',[back-.025,.37,z],[.04,.22,1.31])
    r('KeyboardWell',[front+.11,.843,z],[.20,.012,1.27])
    pitch=1.24/52;white_centers=[]
    for i in range(52):
        kz=z-.62+(i+.5)*pitch;white_centers.append(kz)
        r('WhiteKey',[front+.105,.853,kz],[.185,.016,pitch-.0012],'white',.001)
    # A0..C8: black keys after A, C, D, F, G (not B or E).
    for i in range(51):
        if i%7 in (0,2,3,5,6):r('BlackKey',[front+.151,.867,(white_centers[i]+white_centers[i+1])/2],[.10,.022,pitch*.57],'dark',.002)
    for sign in (-1,1):
        for j in range(7):r('SpeakerSlot',[back-.065,.843,z+sign*.50+j*.012],[.065,.002,.003],'study_pc_seam',.0005)
    r('ControlPanel',[back-.065,.844,z],[.10,.006,.32],'study_pc_seam',.002)
    r('Display',[back-.068,.850,z-.035],[.052,.003,.068],'study_screen',.001)
    for j in range(5):r('Button',[back-.067,.851,z+.035+j*.022],[.020,.006,.010],'door_handle_satin',.002)
    r('MusicRest',[back-.034,.975,z],[.016,.23,.52],'dark',.005)
    r('MusicLedge',[back-.052,.869,z],[.055,.013,.54],'dark',.003)
    r('PedalBoard',[back-.13,floor+.055,z],[.18,.05,.36])
    for sign in (-1,0,1):r('Pedal',[back-.23,floor+.065,z+sign*.085],[.12,.018,.035],'door_handle_satin',.006)


def bowls(api,box,rounded,rod,floor):
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith('PetFeeding')]
    y=floor+.29
    for x in (4.82,5.10):
        rod('PetFeedingStand','door_handle_satin',[x,y,3.80],[x,y,4.44],.007)
        for z in (3.82,4.42):rod('PetFeedingLeg','door_handle_satin',[x,floor+.007,z],[x,y,z],.007)
    for z in (3.80,4.44):rod('PetFeedingCross','door_handle_satin',[4.82,y,z],[5.10,y,z],.007)
    for z in (3.96,4.28):
        box('PetFeedingBowl','polish_steel',[4.96,y-.018,z],[.25,.08,.25],dict(type='lathe',segments=48,rings=[[0,-.5],[.31,-.5],[.38,-.40],[.49,.44],[.50,.49],[.47,.50],[.445,.38],[.335,-.34],[0,-.34]]))
        for i in range(24):
            a=i*math.tau/24;b=(i+1)*math.tau/24
            rod('PetFeedingSupportRing','door_handle_satin',[4.96+.117*math.cos(a),y-.007,z+.117*math.sin(a)],[4.96+.117*math.cos(b),y-.007,z+.117*math.sin(b)],.004)


def baskets(api,put):
    # Copy the correctly proportioned kitchen assembly and rotate it for west facade.
    kitchen=[copy.deepcopy(api.resolved(e)) for e in api.ELEMENTS if e['name'].startswith('KitchenOutdoorBasket')]
    tray=next(e for e in kitchen if '_Tray_' in e['name']);origin=tray['position']
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith('BedroomOutdoorBasket')]
    for r in kitchen:
        q=[r['position'][i]-origin[i] for i in range(3)]
        e=copy.deepcopy(r);e.pop('finished',None);e['name']=r['name'].replace('KitchenOutdoorBasket','BedroomOutdoorBasket')
        e['position']=[-.835-q[2],r['position'][1],4.2+q[0]];e['rotation']=r.get('rotation',0)-math.pi/2
        e.pop('inspectId',None);api.ELEMENTS.append(e)
    for prefix,wp,axis in [('KitchenOutdoorBasket','Window_KitchenSouth_glass',0),('BedroomOutdoorBasket','Window_BedroomWest_glass',2)]:
        win=api.resolved(next(e for e in api.ELEMENTS if e['name'].startswith(wp)))
        members=[e for e in api.ELEMENTS if e['name'].startswith(prefix)]
        def extent(r):
            c=abs(math.cos(r.get('rotation',0)));s=abs(math.sin(r.get('rotation',0)))
            return (r['size'][axis]*c+r['size'][2-axis]*s)/2
        edge=max(api.resolved(e)['position'][axis]+extent(api.resolved(e)) for e in members)
        delta=win['position'][axis]+win['size'][axis]/2-edge
        for e in members:
            r=api.resolved(e);p=list(r['position']);p[axis]+=delta;put(e,position=p)


def reduce_door_opening(api,put):
    for room in ('Bedroom','Study'):
        door=next(e for e in api.ELEMENTS if e['name'].startswith('Door_'+room+'_'));r=api.resolved(door)
        cp=r['closed']['position'];ca=r['closed']['rotation'];old=r.get('rotation',0)
        delta=(old-ca+math.pi)%(2*math.pi)-math.pi;sign=1 if delta>0 else -1
        hinge=[cp[0]-math.cos(ca)*r['size'][0]/2-math.sin(ca)*sign*(r['size'][2]/2+.008),cp[2]+math.sin(ca)*r['size'][0]/2-math.cos(ca)*sign*(r['size'][2]/2+.008)]
        angle=sign*math.radians(90);dx=cp[0]-hinge[0];dz=cp[2]-hinge[1]
        p=[hinge[0]+dx*math.cos(angle)+dz*math.sin(angle),cp[1],hinge[1]-dx*math.sin(angle)+dz*math.cos(angle)]
        change=ca+angle-old
        for e in api.ELEMENTS:
            if not e['name'].startswith(('Door_'+room+'_','DoorHandle_'+room+'_')):continue
            q=api.resolved(e);dx=q['position'][0]-r['position'][0];dz=q['position'][2]-r['position'][2]
            put(e,position=[p[0]+dx*math.cos(change)+dz*math.sin(change),q['position'][1],p[2]-dx*math.sin(change)+dz*math.cos(change)],rotation=q.get('rotation',0)+change)
        for row in api.DOOR_OPENING_LIMITS:
            if row['name']==door['name']:row.update(degrees=90,obstacle='консервативное ограничение по чистовой стене')
