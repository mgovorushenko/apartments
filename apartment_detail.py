"""Whole-apartment detail and five explicit user corrections, 09 September.

Architecture and nominal furniture footprints remain the dimensional authority.
Sliding hardware, external basket elevation and product designs are schematic.
"""
import math


def build(api):
    def resolved(e):return api.resolved(e)
    def put(e,**changes):
        e['finished']={**resolved(e),**changes};e['finished'].pop('finished',None)
    def node(prefix):return next(e for e in api.ELEMENTS if e['name'].startswith(prefix))
    def material(name,rgb,pattern=0,roughness=.8,metallic=0):
        api.MATERIALS[name]=dict(color=[*rgb,1],pattern=pattern,roughness=roughness,metallic=metallic)
    material('dog_black',(.070,.073,.078),roughness=.50)
    material('dog_black_soft',(.082,.085,.090),roughness=.72)
    material('dog_nose_black',(.013,.016,.020),roughness=.34)
    material('plant_leaf_dark',(.16,.25,.115),roughness=.75)
    material('plant_leaf_light',(.24,.34,.16),roughness=.8)
    material('plant_stem',(.27,.28,.13))
    material('guitar_spruce',(.69,.49,.28),1)
    material('guitar_edge',(.29,.16,.09),1)
    material('sliding_profile',(.50,.52,.51),roughness=.33,metallic=.65)
    material('sliding_shadow',(.26,.25,.23))
    material('toilet_seat_joint',(.63,.63,.60),roughness=.55)
    def box(name,mat,p,s,detail=None,rotation=0):
        api.add_box(name,mat,p[0],p[2],s[0],s[2],s[1],base=p[1]-s[1]/2,rotation=rotation)
        e=api.ELEMENTS[-1];e.update(position=list(p),size=list(s),rotation=rotation,noEdges=True)
        if detail:
            e['detail']=dict(detail)
            if detail['type']=='rounded' and detail.get('radius',.01)<=.004:e['detail']['steps']=1
        return e
    def rod(name,mat,a,b,r=.004):
        p=[(a[i]+b[i])/2 for i in range(3)];s=[abs(a[i]-b[i])+2*r for i in range(3)]
        return box(name,mat,p,s,dict(type='rod',start=[(a[i]-p[i])/s[i] for i in range(3)],end=[(b[i]-p[i])/s[i] for i in range(3)],radius=r))
    def pillow(e,power=4):put(e,detail=dict(type='pillow',power=power),noEdges=True)
    def rounded(e,r=.006):put(e,detail=dict(type='rounded',radius=r,steps=1 if r<=.006 else 3),noEdges=True)

    # Consistent material vocabulary across all rooms, preserving their palette.
    for name,spec in api.MATERIALS.items():
        if any(t in name for t in ('oak','walnut')):spec['pattern']=1
        if name.startswith(('fabric','curtain_','coat_')) or name in ('bedroom_ivory','bedroom_navy','bedroom_rug','bedroom_rug_weave'):spec['pattern']=2
    for e in list(api.ELEMENTS):
        n=e['name'];r=resolved(e)
        if r['category']!='furniture' or r.get('detail'):continue
        if n.startswith(('Bed_','StudySofa','Furniture_Study','EntryCoat')):
            if any(t in n for t in ('Pillow','Cushion','Cover','Throw','SeatPad','Jacket','Sleeve','Shoulder','_seat_')):pillow(e,5 if 'Cover' in n or 'Cushion' in n else 4)
            elif r['shape']=='box' and not any(t in n for t in ('Key','Slat','Fastener','Pocket')):rounded(e,min(.025,min(r['size'])*.25))
        if n.startswith(('Bedside','ComputerDesk','Monitor','Keyboard','Piano','StudyOpenShelf','StudyShelfBook','Laundry','Washer','Dryer','BedroomAC','StudyWestRadiator','StudySouthRadiator','BedroomRadiator','KitchenRadiator','BedroomWardrobe','EntryWardrobe','HallWardrobe','BathroomVanity')):
            if r['shape']=='box':rounded(e,.004 if min(r['size'])>.025 else .0015)
        if n.startswith('BasinRim'):rounded(e,.008)
        if n.startswith('BathTallCabinetFacade'):rounded(e,.001)
        # The WC gets a dedicated tapered shell and closed lid below.
        if n.startswith(('BedroomRug','BedroomArt','PetFeeding')):put(e,noEdges=True)
    # Oval tapered bowl with a small rear mounting body, thin seat joint and lid.
    rear=node('ToiletWallHungBody_');bowl=node('ToiletBowl_');lid=node('ToiletSeatOpening_')
    z=resolved(bowl)['position'][2]
    put(rear,position=[8.861,.333,z],size=[.130,.24,.26],detail=dict(type='rounded',radius=.035),noEdges=True)
    rings=[[0,-.5],[.22,-.5],[.31,-.46],[.39,-.34],[.46,-.12],[.495,.22],[.5,.43],[.49,.5],[0,.5]]
    put(bowl,position=[8.655,.325,z],size=[.53,.26,.367],detail=dict(type='lathe',rings=rings,segments=64),noEdges=True)
    put(lid,position=[8.655,.475,z],size=[.546,.028,.387],material='ceramic',detail=dict(type='lathe',rings=[[0,-.5],[.48,-.5],[.5,-.15],[.5,.1],[.485,.43],[.44,.5],[0,.5]],segments=64),noEdges=True)
    box('ToiletSeatGasket','toilet_seat_joint',[8.655,.458,z],[.532,.004,.374],dict(type='lathe',rings=[[0,-.5],[.5,-.5],[.5,.5],[0,.5]],segments=64))
    # Matching separate cushions and a pair of soft back pads for the study sofa.
    seat=node('StudySofa_Cushion_');r=resolved(seat);p=r['position'];s=r['size'];width=s[0]/2-.004
    put(seat,position=[p[0]-s[0]/4-.002,p[1],p[2]],size=[width,s[1],s[2]])
    box('StudySofa_SeatPad','fabric_light',[p[0]+s[0]/4+.002,p[1],p[2]],[width,s[1],s[2]],dict(type='pillow',power=5))
    for x in (2.99,3.88):
        box('StudySofa_BackPad','fabric_light',[x,.69,5.93],[.80,.40,.17],dict(type='pillow',power=4))
    # Natural gathered textile surfaces in every remaining room, with original
    # width, height, clear-bottom and centre. West curtains rotate as whole panels.
    for room in ('BedroomWest','StudyWest','StudySouth'):
        west=room.endswith('West');along=2 if west else 0;normal=0 if west else 2
        for group,folds in (('LeftPanel',6),('RightPanel',6),('Tulle',16)):
            prefix='Curtain_'+room+'_'+group
            members=[e for e in api.ELEMENTS if e['name'].startswith(prefix)]
            if not members:continue
            old=[resolved(e) for e in members]
            lo=[min(e['position'][i]-e['size'][i]/2 for e in old) for i in range(3)]
            hi=[max(e['position'][i]+e['size'][i]/2 for e in old) for i in range(3)]
            api.ELEMENTS[:]=[e for e in api.ELEMENTS if e not in members]
            p=[(lo[i]+hi[i])/2 for i in range(3)]
            box(prefix,old[0]['material'],p,[hi[along]-lo[along],hi[1]-lo[1],.023 if group=='Tulle' else .06],dict(type='curtain',folds=folds),math.pi/2 if west else 0)
    members=[e for e in api.ELEMENTS if e['name'].startswith('BathShowerCurtain_')]
    old=[resolved(e) for e in members]
    lo=[min(e['position'][i]-e['size'][i]/2 for e in old) for i in range(3)];hi=[max(e['position'][i]+e['size'][i]/2 for e in old) for i in range(3)]
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if e not in members and not e['name'].startswith('BedroomRugWeave')]
    box('BathShowerCurtain',old[0]['material'],[(lo[i]+hi[i])/2 for i in range(3)],[hi[0]-lo[0],hi[1]-lo[1],.032],dict(type='curtain',folds=6))

    # Wardrobes: two overlapping full-height panels, two channels, recessed
    # vertical finger profiles. Nothing projects into the existing passages.
    api.SLIDING_WARDROBES={}
    for prefix,axis,sign in (('EntryWardrobe',0,1),('HallWardrobe',2,1),('BedroomWardrobe',0,-1)):
        if prefix=='BedroomWardrobe':
            crown=resolved(node('BedroomWardrobeCrown_'));base=api.FINISH_SETTINGS['dry_floor']
            center=[crown['position'][0],(base+crown['position'][1]+crown['size'][1]/2)/2,crown['position'][2]]
            size=[crown['size'][0],crown['position'][1]+crown['size'][1]/2-base,crown['size'][2]]
            remove=('BedroomWardrobeDoor','BedroomWardrobeStile','BedroomWardrobeRail','BedroomWardrobeHandle')
            # Recess the solid backing behind both sliding tracks.
            body=node('BedroomWardrobe_001');b=resolved(body);bp=list(b['position']);bs=list(b['size']);bp[0]+=.042;bs[0]-=.084
            put(body,position=bp,size=bs)
            mat='bedroom_oak_panel'
        else:
            source=api.CABINET_DETAIL_BOUNDS[prefix];center=source['position'];size=source['size'];base=center[1]-size[1]/2
            remove=(prefix+'Facade',prefix+'_Handle',prefix+'Reveal',prefix+'EndJoint')
            mat=resolved(node(prefix+'Case_Back'))['material']
        api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith(remove)]
        along=2 if axis==0 else 0;front=center[axis]+sign*size[axis]/2;w=size[along];h=size[1];overlap=.035
        api.SLIDING_WARDROBES[prefix]=dict(center=center,size=size,axis=axis,sign=sign,overlap=overlap)
        def part(label,mat,u,depth,y,width,thick,height):
            p=list(center);p[along]+=u;p[axis]=front-sign*depth;p[1]=base+y+height/2
            s=[0,height,0];s[along]=width;s[axis]=thick
            return box(prefix+label,mat,p,s,dict(type='rounded',radius=.001))
        for y in (.082,h-.028):
            for d in (.019,.048):part('SlidingTrack','sliding_profile',0,d,y,w-.040,.016,.012)
        dw=(w-.04+overlap)/2;dh=h-.146
        for i in range(2):
            u=(-1 if i==0 else 1)*(w-.04-overlap)/4;depth=.019+i*.029
            part('SlidingDoor',mat,u,depth,.112,dw,.018,dh)
            for edge in (-1,1):
                part('SlidingProfile','sliding_profile',u+edge*(dw/2-.009),depth-.010,.112,.016,.002,dh)
                part('SlidingRecess','sliding_shadow',u+edge*(dw/2-.018),depth-.011,.85,.006,.001,.55)

    # AC baskets sit beyond the outer facade face and below the window sill.
    api.OUTDOOR_BASKET_BOUNDS={}
    for prefix,window,axis,sign in (('BedroomOutdoorBasket','Window_BedroomWest_glass',0,-1),('KitchenOutdoorBasket','Window_KitchenSouth_glass',2,1)):
        members=[e for e in api.ELEMENTS if e['name'].startswith(prefix)]
        old=[resolved(e) for e in members];win=resolved(node(window));along=2 if axis==0 else 0
        lo=[min(e['position'][i]-e['size'][i]/2 for e in old) for i in range(3)];hi=[max(e['position'][i]+e['size'][i]/2 for e in old) for i in range(3)]
        exterior=win['position'][axis]+sign*win['size'][axis]/2
        target=exterior+sign*(.025+(hi[axis]-lo[axis])/2)
        shift=[0.,win['position'][1]-win['size'][1]/2-.05-hi[1],0.]
        shift[axis]=target-(lo[axis]+hi[axis])/2;shift[along]=win['position'][along]-(lo[along]+hi[along])/2
        for e in members:
            r=resolved(e);put(e,position=[r['position'][i]+shift[i] for i in range(3)],noEdges=True)
            if '_Unit_' in e['name']:rounded(e,.008)
        api.OUTDOOR_BASKET_BOUNDS[prefix]=dict(axis=axis,sign=sign,exterior=exterior,window=win['name'])
        p=[(lo[i]+hi[i])/2+shift[i] for i in range(3)];w=hi[along]-lo[along];depth=hi[axis]-lo[axis];height=hi[1]-lo[1];bottom=lo[1]+shift[1]
        # Open slatted enclosure at the outer face, brackets at the facade.
        for j in range(8):
            q=list(p);q[axis]+=sign*(depth/2-.010);q[1]=bottom+.08+j*.073
            s=[.014,.020,.014];s[along]=w
            box(prefix+'_Louvre','metal',q,s,dict(type='rounded',radius=.003))

    # Rebuild the slice-stack dog as smooth dark ellipsoids, including paws/muzzle.
    dog=[e for e in api.ELEMENTS if e['name'].startswith('Dog') and not e['name'].startswith('DogBed')]
    groups={}
    for e in dog:groups.setdefault(e['name'].rsplit('_',1)[0],[]).append(e)
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if e not in dog]
    for prefix,members in groups.items():
        for start in range(0,len(members),10):
            old=[resolved(e) for e in members[start:start+10]]
            lo=[min(e['position'][i]-e['size'][i]/2 for e in old) for i in range(3)];hi=[max(e['position'][i]+e['size'][i]/2 for e in old) for i in range(3)]
            mat='dog_nose_black' if any(k in prefix for k in ('Nose','Eye')) else 'dog_black_soft' if 'Ear' in prefix else 'dog_black'
            box(prefix,mat,[(lo[i]+hi[i])/2 for i in range(3)],[hi[i]-lo[i] for i in range(3)],dict(type='pillow',power=2),old[0]['rotation'])
    pillow(node('DogBedCushion'),4)
    # Guitar standing vertically in a separate black floor stand by the piano.
    original=resolved(node('GuitarBody'));gx,gz=original['position'][0],original['position'][2];base=api.FINISH_SETTINGS['dry_floor']
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith('Guitar')]
    def guitar(name,mat,u,y,v,w,h,d,detail=None):
        # Front looks west: local horizontal axis follows world Z.
        return box('Guitar'+name,mat,[gx+v,base+y,gz-u],[w,h,d],detail,math.pi/2)
    guitar('Body','guitar_spruce',0,.34,0,.30,.46,.105,dict(type='lathe',segments=48,rings=[[0,-.5],[.28,-.5],[.44,-.40],[.5,-.20],[.41,-.02],[.28,.12],[.37,.28],[.36,.40],[.18,.5],[0,.5]]))
    guitar('Neck','guitar_edge',0,.755,0,.047,.51,.036,dict(type='rounded',radius=.004))
    guitar('Fretboard','dark',0,.737,-.022,.044,.49,.006)
    guitar('Head','guitar_spruce',0,1.058,0,.073,.12,.033,dict(type='rounded',radius=.01))
    guitar('Soundhole','dark',0,.397,-.054,.081,.081,.003,dict(type='pillow',power=2))
    guitar('Bridge','guitar_edge',0,.26,-.052,.104,.022,.010,dict(type='rounded',radius=.003))
    for i in range(6):guitar('String','metal',(i-2.5)*.006,.666,-.058,.0007,.806,.0007)
    for i in range(15):guitar('Fret','metal',0,.53+.44*(1-2**(-i/12)), -.026,.046,.001,.001)
    for y in (1.026,1.059,1.09):
        for side in (-1,1):guitar('Tuner','metal',side*.045,y,0,.023,.012,.022,dict(type='rounded',radius=.005))
    for side in (-1,1):
        rod('GuitarStandLeg','dark',[gx+.05,base+.07,gz],[gx-.12,base+.025,gz+side*.14],.011)
        rod('GuitarStandCradle','dark',[gx+.055,base+.19,gz+side*.11],[gx-.08,base+.19,gz+side*.11],.009)
    rod('GuitarStandSpine','dark',[gx+.06,base+.055,gz],[gx+.06,base+.79,gz],.012)
    for side in (-1,1):rod('GuitarStandNeckFork','dark',[gx+.06,base+.79,gz],[gx-.015,base+.79,gz+side*.043],.007)

    # Natural sprigs: tapered pots retained; curved pointed leaves replace discs.
    for prefix in ('KitchenCoffeeDecor_','KitchenTVDecor_','KitchenCounterDecor_'):
        if not any(e['name'].startswith(prefix+'Vase') for e in api.ELEMENTS):continue
        vase=resolved(node(prefix+'Vase'));p=vase['position'];s=vase['size'];top=p[1]+s[1]/2;scale=s[1]/.19
        api.ELEMENTS[:]=[e for e in api.ELEMENTS if not (e['name'].startswith(prefix) and not e['name'].startswith(prefix+'Vase'))]
        for branch in range(4):
            angle=branch*2.39996;reach=(.065+.015*(branch%2))*scale;height=(.20+.035*(branch%3))*scale
            start=[p[0],top-.012,p[2]];end=[p[0]+reach*math.cos(angle),top+height,p[2]+reach*math.sin(angle)]
            rod(prefix+'Stem','plant_stem',start,end,.0018*scale)
            for leaf in range(3):
                t=.34+leaf*.24;center=[start[i]+t*(end[i]-start[i]) for i in range(3)]
                a=angle+(1 if leaf%2 else -1)*.9;length=(.085+.012*(leaf%2))*scale
                offset=.032*scale;tip=[center[0]+offset*math.cos(a),center[1]+length*.18,center[2]+offset*math.sin(a)]
                rod(prefix+'Petiole','plant_stem',center,tip,.0012*scale)
                tilt=.55+.22*((leaf+branch)%3);cs,sn=math.cos(tilt),math.sin(tilt);depth=.015*scale
                lp=[tip[0]+length*.43*sn*math.cos(a),tip[1]+length*.43*cs,tip[2]+length*.43*sn*math.sin(a)]
                box(prefix+'Leaf','plant_leaf_dark' if (leaf+branch)%2 else 'plant_leaf_light',lp,[length*.48,length*cs+depth*sn,length*sn+depth*cs],dict(type='leaf',leafSize=[length*.48,length,depth],tilt=tilt),math.pi/2-a)

    # Circular appliance portholes with separate gaskets and recessed dark glass.
    for prefix in ('Washer','Dryer'):
        e=node(prefix+'_Door_');r=resolved(e);p=r['position'];s=r['size']
        pillow(e,2)
        for name,diam,depth,mat in (('Seal',.39,.010,'metal'),('Glass',.315,.014,'kitchen_appliance_glass')):
            box(prefix+'_Porthole'+name,mat,[p[0]-.009 if name=='Seal' else p[0]-.016,p[1],p[2]],[depth,diam,diam],dict(type='pillow',power=2))
