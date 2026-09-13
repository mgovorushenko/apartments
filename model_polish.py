"""Local whole-apartment detailing. Geometry remains in measured metres.

Door limits are collision-limited mock-up clearances, not hinge specifications.
"""
import math
import re


def build(api):
    def node(prefix): return next(e for e in api.ELEMENTS if e['name'].startswith(prefix))
    def put(e, **kw):
        e['finished'] = {**api.resolved(e), **kw}
        e['finished'].pop('finished', None)
    def box(name, mat, p, s, radius=0, category='furniture', rotation=0, detail=None):
        api.add_box(name, mat, p[0], p[2], s[0], s[2], s[1], base=p[1]-s[1]/2,
                    category=category, rotation=rotation)
        e=api.ELEMENTS[-1];e.update(position=list(p),size=list(s),noEdges=True)
        if detail: e['detail']=detail
        elif radius: e['detail']=dict(type='rounded',radius=radius,steps=2)
        return e
    def rod(name, mat, a, b, radius=.004):
        p=[(a[i]+b[i])/2 for i in range(3)];s=[abs(a[i]-b[i])+radius*2 for i in range(3)]
        return box(name,mat,p,s,detail=dict(type='rod',start=[(a[i]-p[i])/s[i] for i in range(3)],
                    end=[(b[i]-p[i])/s[i] for i in range(3)],radius=radius))
    floor=api.FINISH_SETTINGS['dry_floor']
    ceiling=2.8-api.FINISH_SETTINGS['ceiling_drop']
    api.MATERIALS['exterior_graphite']=dict(color=[.20,.22,.23,1],roughness=.55,metallic=.25)
    api.MATERIALS['radiator_shadow']=dict(color=[.65,.66,.65,1],roughness=.65,metallic=.1)
    api.MATERIALS['polish_steel']=dict(color=[.68,.73,.76,1],roughness=.2,metallic=.95)
    api.MATERIALS['router_led']=dict(color=[.32,.56,.45,1],roughness=.5,metallic=0)
    api.MATERIALS['facade_terracotta']['pattern']=8

    # Exterior wall cores use brick too: exposed end faces formerly stayed white.
    exterior_names={e['name'][len('Facade_'):].rsplit('_',1)[0]
                    for e in api.ELEMENTS if e['name'].startswith('Facade_')}
    for e in api.ELEMENTS:
        r=api.resolved(e);n=e['name']
        if n in exterior_names: put(e,material='facade_terracotta',noEdges=True)
        if n.startswith('Wall_StudyHingePier'):
            put(e,position=[r['position'][0],1.4,r['position'][2]],size=[r['size'][0],2.8,r['size'][2]])
        if n.startswith('StudyHingePierFinish'):
            low=r['position'][1]-r['size'][1]/2
            put(e,position=[r['position'][0],(low+ceiling+.003)/2,r['position'][2]],size=[r['size'][0],ceiling+.003-low,r['size'][2]])
        # Bury the finish top 3 mm in the ceiling, without a shadow-gap profile.
        if r['category']=='finish_wall' and not n.startswith('Facade_') and abs(r['position'][1]+r['size'][1]/2-ceiling)<.004:
            put(e,position=[r['position'][0],r['position'][1]+.0015,r['position'][2]],size=[r['size'][0],r['size'][1]+.003,r['size'][2]])
        if r['category']=='finish_floor' and not any(t in n for t in ('Bath','FloorTile')):
            if r['material'].startswith(('floor_','study_floor','study_oak','bedroom_render_floor','kitchen_floor')):
                v=r['material'][-1] if r['material'][-1] in '012' else '1'
                put(e,material='kitchen_floor_'+v)

    # Window frames are white indoors / dark outside. Dark external drip sills
    # and reveal linings stop at the glazing plane; the interior sill stays white.
    for win in [e for e in api.ELEMENTS if e['name'].startswith('Window_') and '_glass_' in e['name']]:
        w=api.resolved(win);west='West_' in win['name'];axis=0 if west else 2;along=2-axis;sign=-1 if west else 1
        p=w['position'];s=w['size'];prefix=win['name'].split('_glass')[0]
        for frame in [e for e in api.ELEMENTS if e['name'].startswith(prefix+'_frame')]:
            r=api.resolved(frame);fp=list(r['position']);fs=list(r['size'])
            # Split the profile at the glazing plane, including its side faces.
            # A thin front-only overlay left white profile edges visible outside.
            fs[axis]/=2;inside=list(fp);inside[axis]-=sign*fs[axis]/2
            put(frame,position=inside,size=fs)
            fp[axis]+=sign*fs[axis]/2
            box('ExteriorFrame_'+frame['name'],'exterior_graphite',fp,fs,category='window')
        depth=.535/2-.037
        for y in (.854,2.246):
            q=list(p);ss=list(s);q[axis]+=sign*(.036+depth/2);q[1]=y
            ss[axis]=depth;ss[along]+=.008;ss[1]=.008
            if y<1: ss[axis]+=.045;q[axis]+=sign*.0225
            box('ExteriorSill_'+prefix if y<1 else 'ExteriorRevealTop_'+prefix,'exterior_graphite',q,ss,category='window')
        for side in (-1,1):
            q=list(p);ss=list(s);q[axis]+=sign*(.036+depth/2);q[along]+=side*(s[along]/2-.002)
            ss[axis]=depth;ss[along]=.008
            box('ExteriorRevealSide_'+prefix,'exterior_graphite',q,ss,category='window')
            q[axis]=p[axis]-sign*(.036+depth/2)
            box('InteriorRevealSide_'+prefix,'window_white',q,ss,category='window')
        q=list(p);ss=list(s);q[axis]-=sign*(.036+depth/2);q[1]=2.246
        ss[axis]=depth;ss[along]+=.008;ss[1]=.008
        box('InteriorRevealTop_'+prefix,'window_white',q,ss,category='window')
        # Cover the inward-facing sill/lintel core, keeping indoor paint white.
        face=p[axis]-sign*.535/2
        for y,height in ((.425,.85),(2.525,.55)):
            q=list(p);q[axis]=face-sign*.001;q[1]=y
            ss=list(s);ss[axis]=.002;ss[1]=height
            box('InteriorWindowPaint_'+prefix,'wall_white',q,ss,category='finish_wall')

    # Align right edges as seen from inside the corresponding room.
    for prefix,wp,axis,sign in [('BedroomOutdoorBasket','Window_BedroomWest_glass',0,-1),('KitchenOutdoorBasket','Window_KitchenSouth_glass',2,1)]:
        members=[e for e in api.ELEMENTS if e['name'].startswith(prefix)]
        w=api.resolved(node(wp));along=2-axis;right=-1  # looking west / south from inside
        old=[api.resolved(e) for e in members]
        lo=min(e['position'][along]-e['size'][along]/2 for e in old)
        hi=max(e['position'][along]+e['size'][along]/2 for e in old)
        target=w['position'][along]+right*w['size'][along]/2
        delta=target-(lo if right<0 else hi)
        for e in members:
            r=api.resolved(e);p=list(r['position']);p[along]+=delta;put(e,position=p)

    # Panel radiators: recessed channels, raised ribs, top grille, connectors.
    for prefix in ('BedroomRadiator','StudyWestRadiator','StudySouthRadiator','KitchenRadiator'):
        e=node(prefix+'_');r=api.resolved(e);p=r['position'];s=r['size'];axis=0 if 'West' in prefix or prefix=='BedroomRadiator' else 2
        along=2-axis;sign=1 if axis==0 else -1;front=p[axis]+sign*s[axis]/2
        bp=list(p);bs=list(s);bs[axis]-=.012;bp[axis]-=sign*.006
        put(e,position=bp,size=bs,detail=dict(type='rounded',radius=.012,steps=3),noEdges=True)
        count=max(8,round((s[along]-.045)/.038));pitch=(s[along]-.045)/count
        for i in range(count):
            q=list(p);ss=[0,s[1]-.04,0];q[axis]=front-sign*.005;q[along]+=-(count-1)*pitch/2+i*pitch
            ss[axis]=.011;ss[along]=pitch*.68
            rib=box(prefix+'_Rib','white',q,ss,.005)
            rib['detail']['steps']=1  # Tiny bevels need no dense curved tessellation.
        for i in range(count):
            q=list(p);q[1]+=s[1]/2+.0008;q[along]+=-(count-1)*pitch/2+i*pitch
            ss=[0,.0016,0];ss[axis]=s[axis]*.65;ss[along]=pitch*.35
            box(prefix+'_TopVent','radiator_shadow',q,ss)
        for end in (-1,1):
            q=list(p);q[along]+=end*(s[along]/2+.015);q[1]-=s[1]/2-.055
            a=list(q);b=list(q);a[along]-=.026;b[along]+=.026
            rod(prefix+'_Union','polish_steel',a,b,.014)
            low=list(q);low[1]=floor+.02
            rod(prefix+'_Pipe','white',low,q,.009)
        q=list(p);q[along]+=s[along]/2+.053;q[1]+=s[1]/2-.07
        ss=[.045,.045,.045];ss[along]=.068
        box(prefix+'_Thermostat','white',q,ss,.018)

    # The freezer top existed as a separate old white primitive; make a single
    # continuous stone return, level with the adjacent worktop and under the MW.
    e=node('FreezerWorktop_');r=api.resolved(e);put(e,material='kitchen_stone',size=[.6,.04,.612],position=[8.175,.888,4.481],noEdges=True)
    for e in api.ELEMENTS:
        if e['name'].startswith('Microwave'):
            r=api.resolved(e);put(e,position=[r['position'][0]+.025,r['position'][1]+.002,r['position'][2]])

    # Full-height oak left gable; the upper cabinet fits BETWEEN the niche gables.
    niche_left=node('KitchenFridgeNiche_Side_001')
    niche_right=node('KitchenFridgeNiche_Side_002')
    put(niche_left,material='kitchen_oak',noEdges=True)
    nl=api.resolved(niche_left);nr=api.resolved(niche_right)
    niche_inner_left=nl['position'][0]+nl['size'][0]/2
    niche_inner_right=nr['position'][0]-nr['size'][0]/2

    # Wooden carcases with independent milk-white doors, within the same bounds.
    for e in list(api.ELEMENTS):
        n=e['name'];r=api.resolved(e)
        if not n.startswith(('FreezerBase_','KettleCorner_','SinkUnit_','Dishwasher_','OvenUnit_','EndUnit_','KitchenUpper')):continue
        if not re.fullmatch(r'(FreezerBase|KettleCorner|SinkUnit|Dishwasher|OvenUnit|EndUnit|KitchenUpper(?:Fridge|Freezer|Corner|CornerReturn|Sink|Dishwasher|Hood|End))_001',n):continue
        if r['material']!='kitchen_ivory':continue
        axis=2 if n.startswith(('FreezerBase','KitchenUpperFridge','KitchenUpperFreezer','KitchenUpperCornerReturn')) else 0
        sign=1 if axis==2 else -1;p=list(r['position']);s=list(r['size']);front=p[axis]+sign*s[axis]/2
        outline=[[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5]]
        for v in outline:
            if v[axis//2]*sign>.49:v[axis//2]-=sign*.018/s[axis]
        if n=='KitchenUpperFridge_001':
            # Preserve the 700 mm nominal assembly envelope for dimensions,
            # while leaving 1 mm assembly clearance to each full-height gable.
            for v in outline:
                x=niche_inner_left+.001 if v[0]<0 else niche_inner_right-.001
                v[0]=(x-p[0])/s[0]
        put(e,material='kitchen_oak',detail=dict(type='miter',outline=outline))
        fp=list(r['position']);fs=list(r['size']);fp[axis]=front-sign*.009;fs[axis]=.018
        fs[1]-=.006;fs[2-axis]-=.006
        if n=='KitchenUpperFridge_001':
            fp[0]=(niche_inner_left+niche_inner_right)/2
            fs[0]=niche_inner_right-niche_inner_left-.004
        box(n.rsplit('_',1)[0]+'_IvoryFacade','kitchen_ivory',fp,fs,.0015)
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith('KitchenSofa_AccentPillow')]
    for e in list(api.ELEMENTS):
        n=e['name'];r=api.resolved(e)
        if n.startswith('Furniture_DiningChair') and '_seat_' in n:
            p=list(r['position']);s=list(r['size']);top=p[1]+s[1]/2
            put(e,material='kitchen_oak',position=[p[0],top-.045,p[2]],size=[s[0],.036,s[2]],detail=dict(type='rounded',radius=.012,steps=3),bevel=0)
            box(n.split('_seat')[0]+'_SeatCushion','kitchen_seat',[p[0],top-.014,p[2]],[s[0]-.042,.032,s[2]-.042],rotation=r.get('rotation',0),detail=dict(type='pillow',power=6))

    # Kettle body, rolled lid, curved handle, hollow spout and power base.
    e=node('Kettle_001');r=api.resolved(e);p=r['position'];s=r['size'];x,y,z=p
    put(e,material='polish_steel',detail=dict(type='lathe',segments=40,rings=[[0,-.5],[.38,-.5],[.47,-.43],[.50,-.2],[.49,.28],[.39,.45],[.34,.5],[0,.5]]),noEdges=True)
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith(('Kettle_Handle','Kettle_Spout'))]
    for i in range(14):
        a=-math.pi/2+i*math.pi/14;b=-math.pi/2+(i+1)*math.pi/14
        rod('Kettle_HandleCurve','dark',[x+.085+.065*math.cos(a),y+.005+.090*math.sin(a),z],
            [x+.085+.065*math.cos(b),y+.005+.090*math.sin(b),z],.011)
    rod('Kettle_Spout','polish_steel',[x-.075,y+.045,z],[x-.132,y+.092,z],.018)
    box('Kettle_SpoutOpening','dark',[x-.133,y+.103,z],[.026,.003,.024],.002)
    box('Kettle_Base','dark',[x,y-s[1]/2+.006,z],[.198,.015,.198],detail=dict(type='lathe',segments=40,rings=[[0,-.5],[.48,-.5],[.5,0],[.48,.5],[0,.5]]))
    box('Kettle_LidGrip','dark',[x,y+s[1]/2+.017,z],[.055,.016,.045],.007)
    box('Kettle_Switch','dark',[x+.123,y-.08,z],[.037,.009,.027],.004)
    box('Kettle_WaterGauge','dark',[x,y,z+.104],[.027,.105,.002],.001)
    for j in range(4):box('Kettle_GaugeMark','white',[x,y-.034+j*.023,z+.1055],[.016,.0015,.001])

    # Round the room-facing lower AC edge; a rounded body retains exact bounds.
    for prefix in ('KitchenAC','BedroomAC'):
        e=node(prefix+'_001');r=api.resolved(e);p=r['position'];s=r['size'];axis=0 if prefix=='KitchenAC' else 2
        put(e,detail=dict(type='rounded',radius=.045,steps=5),noEdges=True)
        q=list(p);ss=list(s);q[axis]-=s[axis]/2-.011;q[1]-=.098
        ss[axis]=.009;ss[1]=.020;ss[2-axis]-=.13
        box(prefix+'_Outlet','radiator_shadow',q,ss,.004)
        q[1]-=.002;q[axis]-=.004;ss[1]=.004
        box(prefix+'_Louver','white',q,ss,.001)

    # Metal bowls on a 16 cm-high open stand, retaining their plan positions.
    for e in api.ELEMENTS:
        if e['name'].startswith('PetFeeding') and not e['name'].startswith('PetFeedingMat'):
            r=api.resolved(e);put(e,position=[r['position'][0],r['position'][1]+.12,r['position'][2]])
            if e['name'].startswith(('PetFeedingBowl','PetFeedingRim')):put(e,material='polish_steel')
            if e['name'].startswith('PetFeedingBowl'):
                put(e,detail=dict(type='lathe',segments=40,rings=[[0,-.5],[.32,-.5],[.43,-.36],[.5,.48],[.48,.5],[.45,.4],[.36,-.24],[0,-.28]]))
    for x in (4.82,5.10):
        rod('PetFeedingStandRail','dark',[x,floor+.16,3.825],[x,floor+.16,4.415],.007)
        for z in (3.84,4.40):rod('PetFeedingStandLeg','dark',[x,floor+.008,z],[x,floor+.16,z],.007)
    for z in (3.84,4.40):rod('PetFeedingStandCross','dark',[4.82,floor+.16,z],[5.10,floor+.16,z],.007)

    # Top-shelf router, closed appliance facade and entry electrical panel.
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith(('EntryCoatTopBasket','EntryCoatBasketLabel'))]
    box('EntryRouter_Body','white',[5.87,2.174,.41],[.22,.036,.16],.009)
    for z in (.35,.47):rod('EntryRouter_Antenna','white',[5.80,2.18,z],[5.80,2.33,z],.006)
    for j in range(4):box('EntryRouter_LED','router_led',[5.981,2.172,.383+j*.018],[.002,.003,.003])
    for j in range(10):box('EntryRouter_Vent','radiator_shadow',[5.84+j*.009,2.1925,.41],[.003,.001,.075])
    box('LaundryApplianceFacade','kitchen_ivory',[8.421,1.005,.915],[.018,1.847,.606],.0015)
    box('LaundryApplianceFacade_Handle','kitchen_brass',[8.398,1.11,.68],[.018,.22,.012],.004)
    box('EntryElectricalPanel','door_ivory',[7.72,1.55,.022],[.32,.44,.035],.008)
    box('EntryElectricalPanel_Door','white',[7.72,1.55,.042],[.297,.417,.008],.004)
    box('EntryElectricalPanel_Latch','metal',[7.838,1.51,.048],[.012,.027,.004],.002)

    # Apron front is fixed by the tile course. Recess the tub bottom behind it.
    e=node('BathBase_');r=api.resolved(e);front=api.resolved(node('BathApronBacking_'))
    limit=front['position'][2]-front['size'][2]/2-.002
    back=r['position'][2]-r['size'][2]/2
    put(e,position=[r['position'][0],r['position'][1],(back+limit)/2],size=[r['size'][0],r['size'][1],limit-back])

    artwork(api,box,put)
    door_limits(api,put)


def artwork(api,box,put):
    import base64
    from pathlib import Path
    from PIL import Image
    path=Path(__file__).with_name('assets')/'nordic-lake-art.png'
    # Resampling for the GPU upload is an asset build step. The source stays intact.
    im=Image.open(path).convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
    api.ARTWORK=dict(width=512,height=512,pixels=base64.b64encode(im.tobytes()).decode(),source='assets/nordic-lake-art.png')
    api.MATERIALS['photo_print']=dict(color=[1,1,1,1],roughness=.9,metallic=0,pattern=7)
    for e in list(api.ELEMENTS):
        n=e['name'];r=api.resolved(e)
        if (n.startswith('BedroomArt') and '_Art_' in n) or n.startswith(('KitchenArt_Dune','KitchenArt_Hill','KitchenArt_Horizon','KitchenArt_Sun')):
            api.ELEMENTS.remove(e)
        if (n.startswith('BedroomArt') and '_Canvas_' in n) or n.startswith('KitchenArt_Paper'):
            axis=0 if r['size'][0]<r['size'][2] else 2;along=2-axis
            sign=1 if axis==0 or 'Headboard' in n else -1
            p=list(r['position']);s=list(r['size']);p[axis]+=sign*(s[axis]/2+.001)
            s[axis]=.001;s[along]-=.045;s[1]-=.045
            photo=box(n.split('_')[0]+'_Photo','photo_print',p,s)
            photo['artwork']=dict(axis=axis,sign=sign,along=along)


def door_limits(api,put):
    """Sweep each leaf until its first solid obstacle; 0.25° conservative steps."""
    def rect(r):
        a=r.get('rotation',0);c,s=math.cos(a),math.sin(a);x,_,z=r['position'];w,_,d=r['size']
        return [(x+c*u+s*v,z-s*u+c*v) for u,v in ((-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2))]
    def overlap(a,b):
        for p in (a,b):
            for i in (0,1):
                dx=p[i+1][0]-p[i][0];dz=p[i+1][1]-p[i][1];n=(-dz,dx)
                aa=[x*n[0]+z*n[1] for x,z in a];bb=[x*n[0]+z*n[1] for x,z in b]
                if min(max(aa),max(bb))-max(min(aa),min(bb))<=.0001*math.hypot(*n):return False
        return True
    api.DOOR_OPENING_LIMITS=[]
    # Outward entry leaf is mounted at the exterior rebate, not the inner edge
    # of a 210 mm deep reveal. Move its hardware and closed pose together.
    for e in api.ELEMENTS:
        if e['name'].startswith(('Door_Entry_','DoorHandle_Entry_')):
            r=api.resolved(e);closed={**r['closed']}
            closed['position']=[closed['position'][0],closed['position'][1],closed['position'][2]-.238]
            put(e,position=[r['position'][0],r['position'][1],r['position'][2]-.238],closed=closed)
    for door in [e for e in api.ELEMENTS if e['category']=='door']:
        r=api.resolved(door);cp=r['closed']['position'];ca=r['closed']['rotation'];w,h,d=r['size']
        hinge=[cp[0]-math.cos(ca)*w/2,cp[2]+math.sin(ca)*w/2]
        delta=(r.get('rotation',0)-ca+math.pi)%(2*math.pi)-math.pi;sign=1 if delta>0 else -1
        # Hinge pin lies outside the closed leaf face, allowing it past 90°.
        hinge[0]-=math.sin(ca)*sign*(d/2+.008)
        hinge[1]-=math.cos(ca)*sign*(d/2+.008)
        low=r['position'][1]-h/2;high=low+h
        obstacles=[]
        for e in api.ELEMENTS:
            b=api.resolved(e);n=b['name']
            if b['category'] not in ('wall','furniture'):continue
            if b['category']=='furniture' and not n.startswith(('BedroomWardrobe','StudySofa','Piano','StudyOpenShelf','BathTallCabinet','EntryWardrobe','HallWardrobe','Laundry','EntryCoat','ComputerDesk')):continue
            if b['position'][1]+b['size'][1]/2<=low+.03 or b['position'][1]-b['size'][1]/2>=high:continue
            obstacles.append((n,rect(b)))
        def pose(degrees):
            a=sign*math.radians(degrees);dx=cp[0]-hinge[0];dz=cp[2]-hinge[1]
            return dict(position=[hinge[0]+dx*math.cos(a)+dz*math.sin(a),cp[1],hinge[1]-dx*math.sin(a)+dz*math.cos(a)],size=[w,h,d],rotation=ca+a)
        # Ignore baseline overlap due to traced jamb tolerances, not new obstacles.
        baseline={n for n,p in obstacles if overlap(rect(pose(0)),p)}
        maximum=0;reason='ограничение петель 180°'
        for step in range(1,721):
            deg=step*.25;poly=rect(pose(deg));hit=next((n for n,p in obstacles if n not in baseline and overlap(poly,p)),None)
            if hit:reason=hit;break
            maximum=deg
        final=pose(maximum);old_a=r.get('rotation',0);old_p=r['position'];change=final['rotation']-old_a
        put(door,position=final['position'],rotation=final['rotation'])
        room=door['name'].split('_')[1]
        for e in api.ELEMENTS:
            if not e['name'].startswith('DoorHandle_'+room+'_'):continue
            q=api.resolved(e);dx=q['position'][0]-old_p[0];dz=q['position'][2]-old_p[2]
            put(e,position=[final['position'][0]+dx*math.cos(change)+dz*math.sin(change),q['position'][1],final['position'][2]-dx*math.sin(change)+dz*math.cos(change)],rotation=q.get('rotation',0)+change)
        api.DOOR_OPENING_LIMITS.append(dict(name=door['name'],degrees=maximum,obstacle=reason,baseline=list(baseline)))
