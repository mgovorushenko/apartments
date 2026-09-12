"""Designer PDF revision: dimensioned furniture and closed dimension chains.

PDF coordinates are interpreted as finished reference faces for this revision;
raw faces are inferred using the provisional finish build-ups. No wall thickness
is dimensioned in the PDF. Exterior window-wall depths are raster estimates.
"""
import math


def build(api):
    # Preserve each 15 mm finish at reference faces while closing labelled chains.
    xknots=[(-1,-1),(0,0),(.015,.015),(4.705,4.690),(4.72,4.705),(4.79,4.775),
            (5.55,5.55),(5.91,5.91),(5.925,5.925),(7.19,7.17),(7.28,7.26),(7.295,7.275),
            (9.115,9.075),(9.13,9.09),(10,9.96)]
    zknots=[(-1,-1),(2.715,2.715),(3.635,3.605),(3.65,3.62),(4.16,4.16),(4.175,4.175),(4.64,4.635),
            (5.625,5.615),(5.64,5.63),(5.72,5.71),(5.735,5.725),(8.795,8.755),(8.81,8.77),(10,9.96)]
    def mapped(v,knots):
        for (a,b),(c,d) in zip(knots,knots[1:]):
            if v<=c:return b+(v-a)*(d-b)/(c-a)
        return v+knots[-1][1]-knots[-1][0]
    def warp(data):
        result={**data};p=list(data['position']);s=list(data['size'])
        for axis,knots in ((0,xknots),(2,zknots)):
            lo,hi=mapped(p[axis]-s[axis]/2,knots),mapped(p[axis]+s[axis]/2,knots)
            p[axis]=(lo+hi)/2;s[axis]=hi-lo
        result.update(position=p,size=s)
        if 'closed' in data:
            cp=data['closed']['position'];result['closed']={**data['closed'],'position':[mapped(cp[0],xknots),cp[1],mapped(cp[2],zknots)]}
        return result
    for e in api.ELEMENTS:
        final=warp(api.resolved(e));base=warp(e)
        e.update(base)
        if 'hinge' in e:e['hinge']=[mapped(e['hinge'][0],xknots),mapped(e['hinge'][1],zknots)]
        if 'finished' in e:e['finished']={k:final[k] for k in ('position','size','closed') if k in final}

    # Thick window reveals visible in the PDF (~0.55 m from calibrated raster).
    # Other structural thicknesses remain unverified and are recorded separately.
    for e in api.ELEMENTS:
        n=e['name']
        if e['category'] not in ('wall','window'):continue
        if n.startswith(('Wall_BedroomWest','BedroomWest_','Window_BedroomWest_')):
            e['position'][0]=-.2675;e['size'][0]=.535
        elif n.startswith(('Wall_StudyWest','StudyWest_','Window_StudyWest_')):
            # Preserve the inner facade line; extend only the exterior reveal.
            inner=mapped(1.59,xknots);e['position'][0]=inner-.2675;e['size'][0]=.535
        elif n.startswith(('Wall_South','StudySouth_','KitchenSouth_','Window_StudySouth_','Window_KitchenSouth_')):
            e['position'][2]=8.77+.2675;e['size'][2]=.535
        if n.startswith('Wall_BedroomNorth_'):
            hi=e['position'][0]+e['size'][0]/2;e['position'][0]=(hi-.535)/2;e['size'][0]=hi+.535
        if n.startswith('Wall_SouthWest_'):
            hi=e['position'][0]+e['size'][0]/2;lo=mapped(1.59,xknots)-.535
            e['position'][0]=(hi+lo)/2;e['size'][0]=hi-lo
        if n.startswith(('Wall_StudyWestLower_','Wall_EastExterior_')):
            lo=e['position'][2]-e['size'][2]/2;e['position'][2]=(lo+9.305)/2;e['size'][2]=9.305-lo

    def group(ident):return [e for e in api.ELEMENTS if e.get('inspectId')==ident]
    def bounds(elements):
        values=[]
        for raw in elements:
            e=api.resolved(raw);x,y,z=e['position'];sx,sy,sz=e['size'];a=e.get('rotation',0)
            values.extend((x+u*math.cos(a)+v*math.sin(a),z-u*math.sin(a)+v*math.cos(a)) for u in (-sx/2,sx/2) for v in (-sz/2,sz/2))
        return [min(p[0] for p in values),min(p[1] for p in values),max(p[0] for p in values),max(p[1] for p in values)]
    changes=[]
    def place(ident,target,primary=None,source=None):
        members=group(ident)
        if not members:return
        core=[e for e in members if primary and e['name'].startswith(primary)] if primary else members
        before=bounds(core or members);x0,z0,x1,z1=target
        ax=(x1-x0)/(before[2]-before[0]);az=(z1-z0)/(before[3]-before[1])
        for e in members:
            f=api.resolved(e);x,y,z=f['position'];sx,sy,sz=f['size'];a=f.get('rotation',0)
            # Furniture groups here are axis-aligned. Pleat and trim angles retain shape.
            scale_x=math.hypot(ax*math.cos(a),az*math.sin(a))
            scale_z=math.hypot(ax*math.sin(a),az*math.cos(a))
            e['finished']={**f,'position':[x0+(x-before[0])*ax,y,z0+(z-before[1])*az],
                           'size':[sx*scale_x,sy,sz*scale_z]}
            e['finished'].pop('finished',None)
        changes.append(dict(id=ident,bounds=target,source=source or 'Положение по PDF; неподписанная ось по контуру'))

    # Bedroom: 200 + 250 + 650 + 35 + 1800 + 35 + 650 + 455 + 600 = 4675.
    place('bed',[1.115,2.715,2.985,4.715],primary='Bed_Frame_',source='1870 × 2000; проход у изножья 900')
    for e in group('bed'):
        if e['name'].startswith('Bed_Mattress_'):
            f=api.resolved(e);e['finished']={**f,'position':[2.05,f['position'][1],f['position'][2]],'size':[1.8,f['size'][1],f['size'][2]]}
    place('bedside-left',[.465,2.715,1.115,3.165],primary='BedsideLeft_Top_',source='Ширина 650; глубина 450 по контуру')
    place('bedside-right',[2.985,2.715,3.635,3.165],primary='BedsideRight_Top_',source='Ширина 650; глубина 450 по контуру')
    place('light-left',[.664,2.715,.916,3.04])
    place('light-right',[3.184,2.715,3.436,3.04])
    place('bedroom-wardrobe',[4.09,2.715,4.69,4.415],primary='BedroomWardrobeCrown_',source='1700 × 600')
    # Lighting and artwork follow the new bed; the previously chosen palette stays.
    place('art-Headboard',[1.71,2.715,2.39,2.741])
    place('BedroomRug',[.72,3.20,3.40,5.10])

    # Hall: distinct 1800 mm wardrobe and 750 mm shoe niche.
    place('hall-wardrobe',[4.79,2.715,6.14,3.315],primary='HallWardrobe_001',source='1350 × 600')
    place('entry-wardrobe',[5.565,.795,6.165,2.595],primary='EntryWardrobe_001',source='Закрытая часть 1800; глубина 600 по контуру')
    floor=api.FINISH_SETTINGS['dry_floor']
    for y in (.08,.30,.52):
        api.add_box('EntryShoeShelf','oak_light',5.865,.410,.6,.75,.025,base=floor+y)
    api.add_box('EntryShoeSide','oak_light',5.575,.410,.02,.75,.62,base=floor)
    # Bathroom: labelled bath 1800 × 750, basin module width 700.
    place('bath',[7.275,1.335,9.075,2.085],source='1800 × 750')
    place('basin',[8.625,2.135,9.075,2.835],source='700; глубина 450 условная')
    # User override: fitted cabinet fills the actual finished niche, not the
    # previous illustrative 300 mm furniture symbol. Recompute from tile faces.
    def tile_face(prefix,axis,sign):
        e=api.resolved(next(e for e in api.ELEMENTS if e['name'].startswith(prefix)))
        return e['position'][axis]+sign*e['size'][axis]/2
    niche=[tile_face('Tile_BathWestLower_',0,1),tile_face('Tile_VentFront_',2,-1),
           tile_face('Tile_VentSide_',0,-1),tile_face('Tile_BathSouth_',2,-1)]
    place('bath-cabinet',niche,primary='BathTallCabinet_001',source='Правка пользователя: вся чистовая ниша, фасад вровень с коробом')
    place('bath-shower-curtain',[7.275,2.06,9.075,2.09],primary='BathCurtainRail_')
    # Align the entire sanitary assembly with the final enclosure, after warping.
    enclosure=next(e for e in api.ELEMENTS if e['name'].startswith('ToiletInstallationEnclosure_'))
    center=api.resolved(enclosure)['position'][2]
    for e in api.ELEMENTS:
        if e['name'].startswith(('ToiletWallHungBody_','ToiletBowl_','ToiletSeatOpening_','ToiletFlushPlate_')):
            e['position'][2]=center
            if 'finished' in e:e['finished']['position'][2]=center

    # Kitchen: 600 + 1250 + Ø900 + 400 = 3150; along run 4580.
    for ident,z,length in [('corner',4.175,.6),('sink-unit',4.775,.6),('dishwasher',5.375,.6),('oven',5.975,.6),('end-unit',6.575,.45)]:
        primary={'corner':'KettleCorner_001','sink-unit':'SinkUnit_001','dishwasher':'Dishwasher_001','oven':'OvenUnit_001','end-unit':'EndUnit_001'}[ident]
        place(ident,[8.475,z,9.075,z+length],primary=primary,source=f'{round(length*1000)} × 600')
    place('tv-console',[8.725,7.025,9.075,8.525],source='Длина 1500; глубина по контуру')
    place('tv',[9.01,7.20,9.065,8.35])
    ac=api.resolved(next(e for e in api.ELEMENTS if e['name'].startswith('KitchenAC_')))
    tv_delta=ac['position'][2]-7.775
    for e in group('tv'):e['finished']['position'][2]+=tv_delta
    place('kitchen-sofa',[5.925,7.025,6.825,8.525],primary='KitchenSofa_Base_',source='Длина 1500; глубина 900 по контуру')
    place('fridge',[7.175,4.175,7.875,4.775],primary='Fridge_001',source='Возврат 1300 = 700 + 600; деление по контуру')
    place('freezer',[7.875,4.175,8.475,4.775],primary='FreezerBase_001',source='600 из цепочки возврата 1300')
    place('microwave',[7.93,4.39,8.43,4.755])
    for ident,target in [('upper-Fridge',[7.175,4.175,7.875,4.775]),('upper-Freezer',[7.875,4.175,8.475,4.525]),
                         ('upper-Corner',[8.725,4.175,9.075,4.775]),('upper-CornerReturn',[8.475,4.175,8.725,4.525]),
                         ('upper-Sink',[8.725,4.775,9.075,5.375]),('upper-Dishwasher',[8.725,5.375,9.075,5.975]),
                         ('upper-Hood',[8.725,5.975,9.075,6.575]),('upper-End',[8.725,6.575,9.075,7.025]),
                         ('hood',[8.625,5.975,9.075,6.575])]:place(ident,target)
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if e.get('inspectId') not in ('table','chair-1','chair-2','chair-3','chair-4')]
    start=len(api.ELEMENTS)
    # Later user correction: 100 mm towards the west wall, chairs tucked in.
    api.add_round_table('DiningTable',6.675,6.175,.9,height=.77,material='oak_light')
    for i,(dx,dz) in enumerate([(-.40,-.40),(.40,-.40),(-.40,.40),(.40,.40)],1):
        api.add_chair('DiningChair'+str(i),6.675+dx,6.175+dz,math.atan2(dx,dz),width=.42,depth=.42,material='oak_light')
    for e in api.ELEMENTS[start:]:
        e['position'][1]+=floor;e['material']='oak_light'
    # Undimensioned symbols from the PDF; their dimensions remain inferred.
    start=len(api.ELEMENTS)
    api.add_round_table('CoffeeTable',7.50,7.86,.55,height=.44,material='oak_light')
    for e in api.ELEMENTS[start:]:e['position'][1]+=floor

    # Study: desk in the corner by the window; shelf at the window side of sofa.
    place('study-shelf',[1.705,5.725,2.405,6.075],source='700; глубина 350 по контуру')
    place('study-sofa',[2.435,5.725,4.435,6.625],primary='StudySofa_Base_',source='2000; глубина 900 по контуру')
    place('desk',[1.685,8.155,3.085,8.755],primary='ComputerDesk_001',source='1400 × 600; отступ 80 у окна')
    place('monitor1',[1.74,8.60,2.36,8.71])
    place('monitor2',[2.42,8.60,3.04,8.71])
    place('study-chair',[2.05,7.62,2.71,8.28])
    place('piano',[5.345,6.755,5.795,8.155],source='Длина 1400; отступ от окна 600')
    api.DESIGNER_CHANGES=changes
    api.PDF_REFERENCE=True
    api.FINISH_SETTINGS['reference']='PDF: условно чистовые грани; тип размеров не подтверждён'
