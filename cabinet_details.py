"""Visible cabinet construction and the entry coat alcove; plan footprints retained."""


def build(api):
    floor=api.FINISH_SETTINGS['dry_floor']
    api.CABINET_DETAIL_BOUNDS={}
    api.MATERIALS['cabinet_reveal']=dict(color=[.26,.22,.17,1],metallic=0,roughness=.9)
    api.MATERIALS['coat_sand']=dict(color=[.62,.53,.40,1],metallic=0,roughness=1)
    api.MATERIALS['coat_slate']=dict(color=[.22,.31,.35,1],metallic=0,roughness=1)

    def cabinet(prefix,face,doors):
        source=next(e for e in api.ELEMENTS if e['name']==prefix+'_001')
        fitted=prefix=='BathTallCabinet'
        e=api.resolved(source)
        api.CABINET_DETAIL_BOUNDS[prefix]=dict(position=list(e['position']),size=list(e['size']))
        api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith(prefix+'_')]
        normal=0 if face in ('east','west') else 2
        along=2 if normal==0 else 0
        sign=1 if face in ('east','south') else -1
        center=e['position'];size=e['size'];w,d,h=size[along],size[normal],size[1]
        front=center[normal]+sign*d/2;base=center[1]-h/2
        def part(label,material,u,v,y,width,depth,height):
            p=[0,0,0];s=[0,0,0]
            p[along]=center[along]+u;p[normal]=front-sign*v
            s[along]=width;s[normal]=depth
            api.add_box(prefix+label,material,p[0],p[2],s[0],s[2],height,base=base+y)
            if fitted:
                # Preserve exact tile-derived boundaries, avoiding rounding gaps.
                api.ELEMENTS[-1]['position']=[p[0],base+y+height/2,p[2]]
                api.ELEMENTS[-1]['size']=[s[0],height,s[2]]
        wood=e['material'];t=.018;plinth=.08 if h>1 else .025
        panel_material='cabinet_panel_'+wood
        api.MATERIALS[panel_material]=dict(color=[v*.90 for v in api.MATERIALS[wood]['color'][:3]]+[1],metallic=0,roughness=.85)
        part('Case_Back',wood,0,d-t/2,plinth,w,t,h-plinth)
        for u in (-w/2+t/2,w/2-t/2):part('Case_Side',wood,u,d/2,plinth,t,d,h-plinth)
        for y in (plinth,h-t):part('Case_Horizontal',wood,0,d/2,y,w,d,t)
        # Recessed plinth plus backing for visible, genuine facade gaps.
        if fitted:part('Case_Plinth',wood,0,d/2,0,w,d,plinth)
        else:part('Case_Plinth','cabinet_reveal',0,d/2+.02,0,w-.036,d-.04,plinth)
        if not fitted:part('Reveal','cabinet_reveal',0,.029,plinth,w-.036,.008,h-plinth-.018)
        bands=[(plinth+.008,h-.48),(h-.476,h-.022)] if h>1.5 else [(plinth+.005,h-.022)]
        if fitted:
            # Fully closed again: a tall main door and an upper door.
            for y in (.43,.90,1.38,1.84):
                part('OpenShelf',wood,0,d/2,y-base,w-.036,d-.036,.018)
        for i in range(doors):
            u=-w/2+(i+.5)*w/doors
            for j,(low,high) in enumerate(bands):
                if fitted:
                    # Frame and inset centre stay wholly behind the niche front.
                    dw=w/doors-.005;border=.032
                    for du in (-dw/2+border/2,dw/2-border/2):
                        part('FacadeStile',wood,u+du,.009,low,border,.018,high-low)
                    for y in (low,high-border):
                        part('FacadeRail',wood,u,.009,y,dw-2*border,.018,border)
                    part('FacadePanel',panel_material,u,.011,low+border,dw-2*border,.018,high-low-2*border)
                    handle_y=low+.11 if j else low+.95
                    part('_Handle_Recess','cabinet_reveal',u+dw/2-.060,.0015,handle_y,.014,.001,.22)
                    continue
                part('Facade',wood,u,.009,low,w/doors-.005,.018,high-low)
                # A shallow contrasting centre panel leaves a 32 mm wood border.
                part('FacadePanel',panel_material,u,-.001,low+.032,w/doors-.069,.002,high-low-.064)
                handle_y=low+.11 if j else min(low+.95,high-.20)
                handle_u=u+(w/doors/2-.075)*(1 if i%2==0 else -1)
                part('_Handle_Grip','metal',handle_u,-.023,handle_y,.012,.016,.22)
                for y in (handle_y+.012,handle_y+.196):
                    part('_Handle_Mount','metal',handle_u,-.011,y,.018,.022,.012)
        # Narrow inset lines on exposed end panels communicate panel thickness.
        if not fitted:
            for u in (-w/2+.003,w/2-.003):
                part('EndJoint','cabinet_reveal',u,.055,plinth+.02,.002,.002,h-plinth-.06)

    for prefix,face,doors in [('EntryWardrobe','east',3),('HallWardrobe','south',3),
                              ('LaundryStorage','west',1),('LaundryUpperStorage','west',1),
                              ('BathTallCabinet','north',1)]:
        cabinet(prefix,face,doors)

    # Replace the former low shoe rack inside its exact 750 × 600 mm footprint.
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith('EntryShoe')]
    x0,x1,z0,z1=5.565,6.165,.035,.785
    def box(label,mat,x,z,w,d,h,y):
        api.add_box('EntryCoat'+label,mat,x,z,w,d,h,base=floor+y)
    box('Case_Back','bedroom_oak_panel',x0+.009,.410,.018,.75,2.5,0)
    for z in (z0+.009,z1-.009):box('Case_Side','oak_light',(x0+x1)/2,z,.6,.018,2.5,0)
    box('Case_Top','oak_light',(x0+x1)/2,.410,.6,.75,.018,2.482)
    box('Shelf','oak_light',(x0+x1)/2,.410,.564,.714,.025,2.10)
    box('Bench','oak_light',(x0+x1)/2,.410,.564,.714,.035,.43)
    box('SeatPad','fabric_light',5.895,.410,.45,.65,.035,.465)
    box('ShoeShelf','oak_light',(x0+x1)/2,.410,.54,.714,.018,.09)
    box('Rail','metal',5.89,.410,.022,.68,.022,1.96)
    for z in (.09,.73):box('RailMount','metal',5.89,z,.044,.016,.055,1.943)
    # Two stylised hanging coats: shoulder shape, sleeves, collars and fasteners.
    for z,mat,length in [(.235,'coat_slate',.78),(.565,'coat_sand',.96)]:
        box('HangerHook','metal',5.89,z,.014,.014,.075,1.89)
        box('Hanger','oak',5.89,z,.022,.24,.025,1.875)
        low=1.84-length
        box('JacketBody',mat,5.92,z,.12,.205,length,low)
        box('Shoulder',mat,5.92,z,.12,.27,.10,1.76)
        for dz in (-.126,.126):box('Sleeve',mat,5.92,z+dz,.105,.057,length*.76,1.78-length*.76)
        for dz in (-.04,.04):box('Collar',mat,5.995,z+dz,.025,.054,.07,1.805)
        box('Fastener','metal',5.983,z,.004,.007,length-.11,low+.035)
        for dz in (-.062,.062):box('Pocket','cabinet_reveal',5.982,z+dz,.005,.048,.013,low+.23)
    for z in (.19,.28,.54,.63):
        box('ShoeSole','dark',5.95,z,.26,.065,.016,.108)
        box('ShoeUpper','coat_sand' if z>.4 else 'coat_slate',5.95,z,.24,.06,.052,.124)
    box('TopBasket','fabric',5.87,.410,.43,.52,.20,2.125)
    box('BasketLabel','bedroom_ivory',6.086,.410,.005,.13,.055,2.19)
