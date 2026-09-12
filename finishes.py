"""Finish layers measured inward from the immutable survey shell (metres).

Unconfirmed build-ups are illustrative, not construction specifications.
The explicit user value for screed is 6 mm pending clarification.
"""
import math

SETTINGS = dict(screed=.006, laminate_underlay=.012, plaster_wallpaper=.015,
                tile_adhesive=.015, ceiling_drop=.050)


def resolved(element):
    return {**element, **element.get('finished', {})}


def build(api):
    cfg = SETTINGS
    dry_floor = cfg['screed'] + cfg['laminate_underlay']
    wet_floor = cfg['screed'] + cfg['tile_adhesive']
    ceiling = 2.8 - cfg['ceiling_drop']
    plaster = cfg['plaster_wallpaper']
    tile = cfg['tile_adhesive']
    api.FINISH_SETTINGS = dict(cfg)
    api.FINISH_SETTINGS.update(provisional=True, dry_floor=dry_floor, wet_floor=wet_floor,
                               dry_clear_height=ceiling-dry_floor, wet_clear_height=ceiling-wet_floor)

    def box(name, mat, bounds, h, base, category):
        x0,z0,x1,z1=bounds
        api.add_box(name,mat,(x0+x1)/2,(z0+z1)/2,x1-x0,z1-z0,h,base=base,category=category)
        return api.ELEMENTS[-1]

    # Finish coordinates derive from the rough shell, never rescale it.
    def plan(bounds):
        x0,z0,x1,z1=bounds
        return ((x0-143)/100,(z0-161)/100,(x1-143)/100,(z1-161)/100)

    def surface(name, axis, at, start, end, sign, mat, thickness, base, top):
        lo,hi=sorted((at,at+sign*thickness))
        bounds=(lo,start,hi,end) if axis=='x' else (start,lo,end,hi)
        e=box(name,mat,bounds,top-base,base,'finish_wall')
        e['surface'] = dict(axis=axis,at=at,start=start,end=end,sign=sign)
        return e

    original=list(api.ELEMENTS)
    for e in original:
        name=e['name']
        if name.startswith('WallFinish_'):
            # Existing room-colour faces occupied 4 mm. Replace with full build-up.
            normal=0 if e['size'][0]<e['size'][2] else 2
            sign=-1 if any(s in name for s in ('East','South')) else 1
            # Door faces share the east wall; south-window faces face north.
            if 'BedroomDoor' in name: sign=-1
            if 'StudyDoor' in name: sign=1
            at=e['position'][normal]-sign*.002
            e['position'][normal]=round(at+sign*plaster/2,5)
            e['size'][normal]=plaster
            old_base=e['position'][1]-e['size'][1]/2
            old_top=e['position'][1]+e['size'][1]/2
            base=max(dry_floor,old_base); top=min(ceiling,old_top)
            e['position'][1]=(base+top)/2; e['size'][1]=top-base
            e['category']='finish_wall'
        elif e['category']=='wall':
            e['material']='rough_wall'
        elif e['category']=='floor':
            old_material=e['material']; e['material']='rough_floor'
            x,y,z=e['position'];w,h,d=e['size']; bounds=(x-w/2,z-d/2,x+w/2,z+d/2)
            wet='Bathroom' in name or 'BathThreshold' in name
            height=wet_floor if wet else dry_floor
            mat='stone_gray' if wet else ('floor_pale_oak' if any(s in name for s in ('Hall','Kitchen','Utility')) else old_material)
            box('Screed_'+name,'screed',bounds,cfg['screed'],0,'finish_floor')
            # Leave 0.4 mm for the visible tile/plank faces; avoid coplanar flicker.
            box('Finish_'+name,mat,bounds,height-cfg['screed']-.0004,cfg['screed'],'finish_floor')
            # Joint grid aligned to one common origin across hall and kitchen.
            x0,z0,x1,z1=bounds
            step_x,step_z=(.60,.60) if wet else (.20,1.20)
            gap=.004 if wet else .0018
            for ix in range(math.floor(x0/step_x),math.ceil(x1/step_x)):
                a=max(x0,ix*step_x+gap/2);b=min(x1,(ix+1)*step_x-gap/2)
                offset=0 if wet else (ix%3)*.40
                for iz in range(math.floor((z0-offset)/step_z),math.ceil((z1-offset)/step_z)):
                    c=max(z0,iz*step_z+offset+gap/2);d1=min(z1,(iz+1)*step_z+offset-gap/2)
                    if b-a<.002 or d1-c<.002:continue
                    tone=('stone_gray_' if wet else mat+'_')+str((ix*7+iz*3)%3)
                    box('FloorTile' if wet else 'FloorPlank',tone,(a,c,b,d1),.0004,height-.0004,'finish_floor')
            for label,bottom,raw in [('RoughCeiling',2.8,True),('StretchCeiling',ceiling,False)]:
                c=box(label+'_'+name,'rough_wall' if raw else 'ceiling_white',bounds,.001,bottom,'ceiling')
                c['shape']='ceiling';c['rawOnly']=raw
        elif e['category']=='door':
            e['material']='door_ivory'
            # Keep rough openings; fit an illustrative leaf between finished jambs.
            width=e['size'][0]-2*plaster
            bottom=dry_floor+.005;top=e['size'][1]-plaster
            height=top-bottom; y=(bottom+top)/2
            ca=e['closed']['rotation'];oa=e['rotation'];hx,hz=e['hinge']
            hx+=math.cos(ca)*plaster;hz-=math.sin(ca)*plaster
            e['finished']={
                'position':[hx+math.cos(oa)*width/2,y,hz-math.sin(oa)*width/2],
                'size':[width,height,e['size'][2]],
                'closed':{'position':[hx+math.cos(ca)*width/2,y,hz-math.sin(ca)*width/2],'rotation':ca}}

    for name,bounds,height in [
        ('Entry',(777,140,883,161),2.2),('Bedroom',(615,625,622,710),2.1),
        ('Study',(622,725,715,733),2.1),('Bathroom',(862,384,871,468),2.1),
    ]:
        x0,z0,x1,z1=plan(bounds)
        sides=[(x0,z0,x0+plaster,z1),(x1-plaster,z0,x1,z1)] if x1-x0>z1-z0 else [
            (x0,z0,x1,z0+plaster),(x0,z1-plaster,x1,z1)]
        for bounds1 in sides:
            box('DoorJamb_'+name,'door_ivory',bounds1,height-dry_floor,dry_floor,'finish_wall')
        box('DoorHead_'+name,'door_ivory',(x0,z0,x1,z1),plaster,height-plaster,'finish_wall')

    # Beige faces towards the connected hall, laundry and kitchen, including returns.
    # Each segment retains the surveyed openings and shared partition location.
    for name,axis,at,start,end,sign in [
        ('EntryWest','x',698,161,423,1),('EntryNorthLeft','z',161,698,777,1),
        ('EntryNorthRight','z',161,883,1056,1),('HallEast','x',1056,161,285,-1),
        ('KitchenEast','x',1056,577,1042,-1),('KitchenSouthLeft','z',1042,734,780,-1),
        ('KitchenSouthRight','z',1042,965,1056,-1),('KitchenWest','x',734,808,1042,1),
        ('HallStudyReturn','x',734,725,808,1),
        # The 190 mm pier beside the study opening also has a hall-facing end.
        # Only this solid pier gets finish; the opening at 622..715 stays clear.
        ('HallStudyReturnEnd','z',725,715,734,-1),
        ('HallBedroom','x',622,431,625,1),('HallBedroomNib','x',622,710,725,1),
        ('HallNorth','z',431,622,698,1),('BathOuterWest','x',862,293,384,-1),
        ('BathOuterWestLower','x',862,468,577,-1),('BathOuterSouth','z',577,862,1056,1),
        ('BathOuterNorth','z',285,862,1056,-1),('DividerNorth','z',423,698,756,-1),
        ('DividerSouth','z',431,698,756,1),('DividerEnd','x',756,423,431,1),
    ]:
        anchor=(at-(143 if axis=='x' else 161))/100
        origin=161 if axis=='x' else 143
        surface('FinishBeige_'+name,axis,anchor,(start-origin)/100,(end-origin)/100,
                sign,'wall_beige',plaster,dry_floor,ceiling)
    for name,axis,at,start,end,sign,base,top in [
        ('EntryLintel','z',161,777,883,1,2.2,ceiling),
        ('BedroomLintel','x',622,625,710,1,2.1,ceiling),
        ('StudyLintel','z',725,622,715,-1,2.1,ceiling),
        ('BathLintel','x',862,384,468,-1,2.1,ceiling),
        ('KitchenSill','z',1042,780,965,-1,dry_floor,.85),
        ('KitchenLintel','z',1042,780,965,-1,2.25,ceiling),
    ]:
        origin=161 if axis=='x' else 143
        surface('FinishBeige_'+name,axis,(at-(143 if axis=='x' else 161))/100,
                (start-origin)/100,(end-origin)/100,sign,'wall_beige',plaster,base,top)

    # Tile finish inside bathroom. Timber-effect feature wall is behind the bath.
    for name,axis,at,start,end,sign,wood,base,top in [
        ('BathFeature','z',293,871,1056,1,True,wet_floor,ceiling),
        ('BathEast','x',1056,293,568,-1,False,wet_floor,ceiling),
        ('BathWestUpper','x',871,293,384,1,False,wet_floor,ceiling),
        ('BathWestLower','x',871,468,568,1,False,wet_floor,ceiling),
        ('BathDoorLintel','x',871,384,468,1,False,2.1,ceiling),
        ('BathSouth','z',568,871,1056,-1,False,wet_floor,ceiling),
        ('VentFront','z',526,912,1056,-1,False,wet_floor,ceiling),
        ('VentSide','x',912,526,568,-1,False,wet_floor,ceiling),
    ]:
        origin=161 if axis=='x' else 143
        anchor=(at-(143 if axis=='x' else 161))/100
        a,b=(start-origin)/100,(end-origin)/100
        surface('TileBacking_'+name,axis,anchor,a,b,sign,'tile_grout',tile-.001,base,top)
        width=.20 if wood else .60; height=1.20
        for i in range(math.ceil((b-a)/width)):
            for j in range(math.ceil((top-base)/height)):
                lo=a+i*width+.002;hi=min(b-.002,a+(i+1)*width-.002)
                low=base+j*height+.002;high=min(top-.002,base+(j+1)*height-.002)
                if hi<=lo or high<=low:continue
                mat=('tile_wood_' if wood else 'stone_gray_')+str((i+2*j)%3)
                surface('Tile_'+name,axis,anchor+sign*(tile-.001),lo,hi,sign,mat,.001,low,high)

    # Raise movable items onto the finished floor; move wall-attached groups inward.
    # This is a finish allowance, not a new furniture arrangement.
    for e in original:
        if e['category']!='furniture':continue
        n=e['name']; x,y,z=e['position']; sx,sy,sz=e['size']
        wet=(7.2<x<9.14 and 1.32<z<4.08)
        rise=wet_floor if wet else dry_floor
        dx=dz=0
        if n.startswith(('Bed_','Bedside')):dz=plaster
        if n.startswith('BedroomWardrobe'):dx=-plaster;dz=plaster
        if n.startswith('BedroomArtHeadboard'):dz=plaster
        if n.startswith(('BedroomArtSouth','BedroomAC','StudySouthRadiator')):dz=-plaster
        if n.startswith(('EntryWardrobe','BedroomRadiator','StudyWestRadiator')):dx=plaster
        if n.startswith(('HallWardrobe','StudyOpenShelf','StudyShelfBook','StudySofa')):dz=plaster
        if n.startswith('HallWardrobe'):dx=plaster
        if n.startswith(('Laundry','Washer','Dryer','TV','KitchenAC','KitchenTap','OvenDoor','Hood','Cooktop','HobRing','Kettle','SinkUnit','Dishwasher','OvenUnit','EndUnit','KitchenSink')):dx=-plaster
        kitchen_attached=('Fridge','Freezer','Microwave','KitchenUpper','Kettle','SinkUnit',
                          'Dishwasher','OvenUnit','EndUnit','KitchenSink','KitchenTap','OvenDoor',
                          'Hood','Cooktop','HobRing','TV','KitchenAC')
        if n.startswith(kitchen_attached):dx=-plaster;dz=plaster
        if n.startswith(('Basin','BathroomMirror','Shower','Toilet')):dx=-tile
        if n.startswith('BathTallCabinet'):
            dx=-tile;dz=-tile
            if '_Handle_' not in n:sy=ceiling-rise
        if n.startswith(('KitchenRadiator','Curtain_KitchenSouth')):dz=-plaster
        if 'OutdoorBasket' in n:rise=0
        if n.startswith('Curtain_'):
            # Floor clearance is measured from finished floor; rail follows ceiling.
            if '_Track_' in n:rise=-cfg['ceiling_drop']
            else:
                base=y-e['size'][1]/2+rise
                top=y+e['size'][1]/2-cfg['ceiling_drop']
                sy=top-base;y=(top+base)/2;rise=0
        e['finished']={'position':[round(x+dx,5),round(y+rise,5),round(z+dz,5)],'size':[sx,sy,sz]}
        if n.startswith('EntryWardrobe'):
            # Cabinet between the north face and the new divider: allow both finishes.
            scale=(2.62-2*plaster)/2.62
            e['finished']['position'][2]=round(plaster+z*scale,5)
            e['finished']['size'][2]*=scale
        if n.startswith(('Laundry','Washer','Dryer')):
            # Keep appliance dimensions. Take the 30 mm loss out of storage width.
            if n.startswith(('LaundryWardrobeBack','LaundryWardrobeTop','LaundryWardrobePlinth')):
                e['finished']['size'][2]-=2*plaster
            elif n.startswith('LaundryWardrobeNorthSide'):
                e['finished']['position'][2]=round(z+plaster,5)
            elif n.startswith('LaundryStorage'):
                if '_Handle_' not in n:e['finished']['size'][2]-=2*plaster
            else:e['finished']['position'][2]=round(z-plaster,5)
        if n.startswith('Curtain_BedroomWest'):
            scale=(2.94-2*plaster)/2.94
            e['finished']['position'][2]=round(2.7+plaster+(z-2.7)*scale,5)
            e['finished']['size'][2 if '_Track_' in n else 0]*=scale
        if n.startswith('BathTallCabinet') and '_Handle_' not in n:
            e['finished']['position'][1]=rise+sy/2
        if n.startswith('KitchenUpper') and '_Handle_' not in n:e['material']='oak_light'
        if n.startswith('Furniture_DiningChair'):e['material']='oak_light'
        if n.startswith('KitchenSofa'):e['material']='sofa_olive'
