"""Final-metre tile courses and bathroom detailing; preserves the measured shell."""
import math


def tile_intervals(lo,hi,origin,length,gap=.002):
    """Actual tile length plus a separate joint; origin is a tile's lower edge."""
    pitch=length+gap
    for k in range(math.floor((lo-origin-length)/pitch)+1,math.ceil((hi-origin)/pitch)):
        a=max(lo,origin+k*pitch);b=min(hi,origin+k*pitch+length)
        if b>a+.00001:yield k,a,b


def subtract_rect(rect,obstacle):
    """Keep cuts from one tile coplanar and touching: no fictitious grout line."""
    a,b,c,d=rect;x0,x1,z0,z1=obstacle
    x0,x1=max(a,x0),min(b,x1);z0,z1=max(c,z0),min(d,z1)
    if x1<=x0 or z1<=z0:return [rect]
    return [r for r in ((a,x0,c,d),(x1,b,c,d),(x0,x1,c,z0),(x0,x1,z1,d))
            if r[1]>r[0]+.00001 and r[3]>r[2]+.00001]


def build(api):
    items = list(api.ELEMENTS)
    def resolved(e): return api.resolved(e)
    def node(prefix): return next(e for e in api.ELEMENTS if e['name'].startswith(prefix))
    def edge(e, a, sign): return e['position'][a] + sign*e['size'][a]/2
    def put(e, **changes):
        e['finished']={**resolved(e),**changes}; e['finished'].pop('finished',None)
    floor=api.FINISH_SETTINGS['wet_floor']; ceiling=2.8-api.FINISH_SETTINGS['ceiling_drop']
    api.TILE_LAYOUT=[]
    # Visible far-right floor corner, at the FINISHED installation/vent faces.
    # The starter is a full 600 mm square with a 2 mm perimeter joint. Extend
    # this one grid over the whole floor, threshold and grey vertical surfaces.
    installation=resolved(node('ToiletInstallationEnclosure_'))
    vent_face=resolved(node('Tile_VentFront_'));vent_side=resolved(node('Tile_VentSide_'))
    corner_x=edge(installation,0,-1);corner_z=edge(vent_face,2,-1)
    grid_x=corner_x-.002-.600;grid_z=corner_z-.002-.600
    api.TILE_REFERENCE=dict(corner=[corner_x,corner_z],starterBounds=[grid_x,corner_x-.002,grid_z,corner_z-.002],
        gridOrigin=[grid_x,grid_z],floorPitchMm=602,wallFormatMm=[600,1200],jointMm=2,
        note='Чистовой угол между лицевой гранью короба инсталляции и венткоробом; целая плитка 600 × 600, отступ от коробов 2 мм.')
    for i, factor in enumerate((.985,1,1.015)):
        api.MATERIALS['stone_gray_'+str(i)]=dict(color=[.73*factor,.715*factor,.68*factor,1],roughness=.78,metallic=0,pattern=3)
        api.MATERIALS['tile_wood_'+str(i)]['pattern']=1
        api.MATERIALS['tile_wood_'+str(i)]['color']=[.76*factor,.62*factor,.445*factor,1]
    api.MATERIALS['bath_oak']=dict(color=[.79,.65,.47,1],roughness=.76,metallic=0,pattern=1)
    for e in api.ELEMENTS:
        if e['name'].startswith(('BathTallCabinet','BathroomVanity')) and resolved(e)['material'] not in ('metal','cabinet_reveal'):
            put(e,material='bath_oak',noEdges=True)
    api.MATERIALS['bath_grout']=dict(color=[.55,.565,.55,1],roughness=.95,metallic=0)
    api.MATERIALS['bath_silicone']=dict(color=[.73,.735,.72,1],roughness=.8,metallic=0)
    api.MATERIALS['bath_light']=dict(color=[1,.94,.83,1],roughness=.5,metallic=0,pattern=4)
    api.MATERIALS['bath_mirror']=dict(color=[.66,.72,.73,1],roughness=.06,metallic=.95,pattern=6)
    api.MATERIALS['bath_chrome']=dict(color=[.72,.76,.77,1],roughness=.17,metallic=.95)

    def box(name,mat,x,z,w,d,h,base,category='furniture'):
        api.add_box(name,mat,x,z,w,d,h,base=base,category=category)
        e=api.ELEMENTS[-1];e['noEdges']=True
        return e
    def sheet(name,mat,axis,at,u0,u1,v0,v1,sign,category):
        p=[0,0,0];s=[0,0,0]; along=2 if axis==0 else 0
        p[axis]=at+sign*.0005;p[along]=(u0+u1)/2;p[1]=(v0+v1)/2
        s[axis]=.001;s[along]=u1-u0;s[1]=v1-v0
        e=box(name,mat,p[0],p[2],s[0],s[2],s[1],v0,category)
        # Keep reference faces exact, including the fitted niche's non-round coordinates.
        e['position']=p;e['size']=s
        return e
    def intervals(lo,hi,origin,step,gap=.002):
        for k in range(math.floor((lo-origin)/step),math.ceil((hi-origin)/step)):
            a=max(lo,origin+k*step+gap/2); b=min(hi,origin+(k+1)*step-gap/2)
            if b>a+.00001:yield k,a,b
    def tile_wall(name,axis,at,lo,hi,bottom,top,sign,wood=False,category='finish_wall',origin=None):
        width,height=(.20,1.20) if wood else (.60,1.20)
        origin=(lo if wood else grid_z if axis==0 else grid_x) if origin is None else origin
        spans=intervals if wood else tile_intervals
        for i,a,b in spans(lo,hi,origin,width):
            y_origin=floor+(i%3)*.40 if wood else floor+.002
            for j,c,d in spans(bottom,top,y_origin,height):
                e=sheet(name,('tile_wood_' if wood else 'stone_gray_')+str((i+2*j)%3),axis,at,a,b,c,d,sign,category)
                api.TILE_LAYOUT.append(dict(name=e['name'],formatMm=[round(width*1000),round(height*1000)],axis=axis,
                                           bounds=[a,b,c,d],staggerMm=400 if wood else 0,jointMm=2))

    # Replace the pre-PDF stretched grid, deriving immutable finished normal faces
    # from the old tiles. Entire new pieces are generated AFTER the PDF warp.
    for prefix in ('BathFeature','BathEast','BathWestUpper','BathWestLower','BathDoorLintel','BathSouth','VentFront','VentSide'):
        old=[resolved(e) for e in items if e['name'].startswith('Tile_'+prefix+'_')]
        backing=resolved(node('TileBacking_'+prefix+'_'))
        axis=0 if backing['size'][0]<backing['size'][2] else 2;along=2 if axis==0 else 0
        sign=1 if prefix in ('BathFeature','BathWestUpper','BathWestLower','BathDoorLintel') else -1
        face=edge(old[0],axis,sign)
        api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith('Tile_'+prefix+'_')]
        put(node('TileBacking_'+prefix+'_'),material='bath_grout',noEdges=True)
        lo,hi=edge(backing,along,-1),edge(backing,along,1)
        tile_wall('Tile_'+prefix,axis,face-sign*.001,lo,hi,edge(backing,1,-1),edge(backing,1,1),sign,prefix=='BathFeature')

    # 600 x 600 floor course, shared origin across the threshold and room.
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith('FloorTile')]
    # Stop finish pieces at solid boxes, keeping 2 mm perimeter joints. Split
    # L-shaped cuts into touching coplanar rectangles from the same grid cell.
    blocked=[(corner_x-.002,edge(installation,0,1)+.002,
              edge(installation,2,-1)-.002,edge(installation,2,1)+.002),
             (edge(vent_side,0,-1)-.002,edge(vent_face,0,1)+.002,corner_z-.002,10)]
    for raw in items:
        if not raw['name'].startswith(('Finish_Floor_Bathroom','Finish_Floor_BathThreshold')):continue
        r=resolved(raw);put(raw,material='bath_grout',noEdges=True)
        for ix,a,b in tile_intervals(edge(r,0,-1),edge(r,0,1),grid_x,.60):
            for iz,c,d in tile_intervals(edge(r,2,-1),edge(r,2,1),grid_z,.60):
                cuts=[(a,b,c,d)]
                for obstacle in blocked:cuts=[piece for cut in cuts for piece in subtract_rect(cut,obstacle)]
                for aa,bb,cc,dd in cuts:
                    e=box('FloorTile','stone_gray_'+str((ix+iz*2)%3),(aa+bb)/2,(cc+dd)/2,bb-aa,dd-cc,.0004,floor-.0004,'finish_floor')
                    e['position']=[(aa+bb)/2,floor-.0002,(cc+dd)/2];e['size']=[bb-aa,.0004,dd-cc]
                    api.TILE_LAYOUT.append(dict(name=e['name'],formatMm=[600,600],axis=1,bounds=[aa,bb,cc,dd],staggerMm=0,jointMm=2,gridCell=[ix,iz]))

    # Tiled bath apron stays inside the approved 1800 x 750 outline.
    bath=resolved(node('BathBase_'));x0,x1=edge(bath,0,-1),edge(bath,0,1);front=edge(bath,2,1)
    for prefix in ('BathSouth_','BathWest_','BathEast_'):
        e=node(prefix);r=resolved(e);p=list(r['position']);s=list(r['size']);p[2]-=.001;s[2]-=.002
        put(e,position=p,size=s,noEdges=True)
    box('BathApronBacking','bath_grout',(x0+x1)/2,front-.006,x1-x0,.01,.558,floor)
    tile_wall('BathApronTile',2,front-.001,x0,x1,floor,.579,1,category='furniture')
    box('BathApronLip','ceramic',(x0+x1)/2,front-.025,x1-x0,.05,.032,.579)
    box('BathApronSeal','bath_silicone',(x0+x1)/2,front-.0015,x1-x0,.003,.003,.578)

    # All exposed faces and top of the installation enclosure; recess the grout
    # substrate 1 mm to avoid duplicate white and tiled coplanar surfaces.
    e=node('ToiletInstallationEnclosure_');r=resolved(e);p=list(r['position']);s=list(r['size'])
    fx=edge(r,0,-1);back=edge(r,0,1);z0=edge(r,2,-1);z1=edge(r,2,1)
    # One uncut 1200 mm vertical course, above the existing 2 mm floor joint.
    # The top's 1 mm visual finish sits above that course, with no second strip.
    face_top=floor+.002+1.20;top=face_top+.001
    p[0]+=.0005;s[0]-=.001;s[1]=face_top-floor;p[1]=floor+s[1]/2;s[2]-=.002
    api.TILE_REFERENCE['installationHeightMm']=round((top-floor)*1000)
    put(e,position=p,size=s,material='bath_grout',noEdges=True)
    tile_wall('BathInstallationTileFront',0,fx+.001,z0,z1,floor,face_top,-1,category='furniture')
    for name,z,sign in [('North',z0,-1),('South',z1,1)]:
        tile_wall('BathInstallationTile'+name,2,z-sign*.001,fx,back,floor,face_top,sign,category='furniture')
    for iz,c,d in tile_intervals(z0,z1,grid_z,.60):
        cap=box('BathInstallationTileTop','stone_gray_'+str(iz%3),(fx+back)/2,(c+d)/2,back-fx,d-c,.001,top-.001)
        cap['position']=[(fx+back)/2,top-.0005,(c+d)/2];cap['size']=[back-fx,.001,d-c]
        api.TILE_LAYOUT.append(dict(name=cap['name'],formatMm=[1200,600],axis=1,bounds=[fx,back,c,d],staggerMm=0,jointMm=2))
    # Two flush buttons, rim, drain/overflow, chrome shower nozzles.
    flush=resolved(node('ToiletFlushPlate_'))
    for dz,w in [(-.043,.073),(.048,.052)]:
        b=box('BathFlushButton','bath_chrome',edge(flush,0,-1)-.001,flush['position'][2]+dz,.002,w,.075,flush['position'][1]-.0375);b['bevel']=.008
    box('BathOverflow','bath_chrome',8.984,1.71,.003,.075,.035,.50)
    api.add_cylinder('BathDrain','bath_chrome',8.85,1.71,.065,.006,base=.176)
    put(node('BathInner_'),material='ceramic',noEdges=True)
    for raw in api.ELEMENTS:
        if raw['name'].startswith(('Basin','Shower','ToiletBowl','ToiletWallHung')):put(raw,noEdges=True)
    head=resolved(node('ShowerHead_'))
    for i in range(4):
        for j in range(4):
            api.add_cylinder('BathShowerNozzle','dark',head['position'][0]+(i-1.5)*.044,head['position'][2]+(j-1.5)*.044,.006,.002,base=edge(head,1,-1)-.002)
            api.ELEMENTS[-1]['noEdges']=True

    # Backlit plain mirror: a slim light perimeter, no mirror cabinet.
    mirror=node('BathroomMirror_');r=resolved(mirror);p=list(r['position']);p[0]-=.018
    put(mirror,position=p,material='bath_mirror',noEdges=True)
    for sign in (-1,1):
        box('BathMirrorLED','bath_light',p[0]+.006, p[2]+sign*(r['size'][2]/2+.004),.012,.008,r['size'][1]+.016,edge(r,1,-1)-.008)
        box('BathMirrorLED','bath_light',p[0]+.006,p[2],.012,r['size'][2],.008,p[1]+sign*(r['size'][1]/2+.004)-.004)
    # Recessed trim and diffuser; provisional positions, no drilling/electrical spec.
    for z in (1.78,2.55,3.30):
        for name,mat,diam,h,base in [('Trim','door_ivory',.115,.009,ceiling-.012),('Diffuser','bath_light',.085,.003,ceiling-.015)]:
            api.add_cylinder('BathCeilingLight_'+name,mat,8.12,z,diam,h,base=base)
            api.ELEMENTS[-1]['noEdges']=True
