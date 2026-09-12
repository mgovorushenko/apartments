"""September 8 revision, traced from the two new 1200×1200 plans.

Plan coordinates are retained for auditing: one diagram pixel = 0.01 m.
This calibration is supported by several independent dimensioned edges.
Unclosed dimension chains are recorded in accuracy.md, not silently rescaled.
Y=0 is the rough slab; no unprovided screed thickness is deducted.
"""
import math

ORIGIN = (143, 161)
FOOTPRINTS = []


def build(api):
    FOOTPRINTS.clear()
    box, cyl = api.add_box, api.add_cylinder

    def xy(x, z):
        return (x - ORIGIN[0]) / 100, (z - ORIGIN[1]) / 100

    def rect(name, material, x0, z0, x1, z1, height, base=0, category="furniture", record=True):
        x, z = xy((x0 + x1) / 2, (z0 + z1) / 2)
        box(name, material, x, z, (x1 - x0) / 100, (z1 - z0) / 100,
            height, base=base, category=category)
        if record:
            FOOTPRINTS.append(dict(name=name, category=category, bounds=[x0,z0,x1,z1], height=height, base=base))

    def disc(name, material, x, z, diameter, height, base=0):
        x, z = xy(x, z)
        cyl(name, material, x, z, diameter, height, base=base)

    def wall(name, bounds, height=2.8, base=0, material="wall"):
        rect(name, material, *bounds, height, base, "wall")

    def floor(name, bounds, material="floor_oak"):
        # Below rough slab datum, visual support only; not a screed specification.
        rect(name, material, *bounds, .06, -.06, "floor")

    def window(name, bounds):
        x0,z0,x1,z1 = bounds
        wall(name+"_Sill", bounds, .85)
        wall(name+"_Lintel", bounds, .55, 2.25)
        if x1-x0 > z1-z0:
            a,z = xy(x0,(z0+z1)/2); b,_ = xy(x1,(z0+z1)/2)
            api.add_window_horizontal(name,a,b,z)
        else:
            x,a = xy((x0+x1)/2,z0); _,b=xy((x0+x1)/2,z1)
            api.add_window_vertical(name,a,b,x)

    def door(name, hinge, end, width, height=2.1):
        x,z=xy(*hinge)
        api.add_door_leaf(name,"oak_light",x,z,width,math.atan2(end[1]-hinge[1],end[0]-hinge[0]),height)
        closed_angle={'Entry':math.pi,'Bedroom':-math.pi/2,'Study':math.pi,'Bathroom':math.pi/2}[name]
        api.ELEMENTS[-1]['hinge']=[x,z]
        api.ELEMENTS[-1]['closed']={
            'position':[round(x+math.cos(closed_angle)*width/2,4),height/2,round(z+math.sin(closed_angle)*width/2,4)],
            'rotation':-closed_angle,
        }

    def cabinet(name,bounds,height=2.4,face="west",material="oak_light",base=0):
        rect(name,material,*bounds,height,base)
        x0,z0,x1,z1=bounds
        if face in ("east","west"):
            x=x1-.7 if face=="east" else x0+.7
            for z in range(round(z0+8),round(z1-5),50):
                rect(name+"_Handle","metal",x-.5,z,x+.5,z+12,.02,base+min(height*.5,1.1),record=False)
        else:
            z=z1-.7 if face=="south" else z0+.7
            for x in range(round(x0+10),round(x1-5),50):
                rect(name+"_Handle","metal",x,z-.5,x+12,z+.5,.02,base+min(height*.5,1.1),record=False)

    def sofa(name,bounds,facing,material="fabric_blue"):
        x0,z0,x1,z1=bounds
        rect(name+"_Base",material,*bounds,.33,.1)
        if facing=="south":
            rect(name+"_Back",material,x0,z0,x1,z0+15,.65,.3)
            rect(name+"_Cushion","fabric_light",x0+12,z0+17,x1-12,z1-3,.14,.43)
            for x in (x0,x1-10): rect(name+"_Arm",material,x,z0,x+10,z1,.4,.3)
        else:
            rect(name+"_Back",material,x0,z0,x0+12,z1,.65,.3)
            rect(name+"_Cushion","fabric_light",x0+14,z0+10,x1-3,z1-10,.14,.43)
            for z in (z0,z1-9): rect(name+"_Arm",material,x0,z,x1,z+9,.4,.3)

    # Connected floor zones in the NEW orientation (entrance at top of plan).
    floor("Floor_Bedroom",(143,431,615,725))
    floor("Floor_BedroomThreshold",(615,625,622,710))
    floor("Floor_Study",(302,733,724,1042))
    floor("Floor_StudyThreshold",(622,725,715,733))
    floor("Floor_HallMiddle",(622,431,862,725))
    floor("Floor_HallEntry",(698,161,862,431),"floor_tile")
    floor("Floor_Utility",(862,161,1056,285),"floor_tile")
    floor("Floor_Bathroom",(871,293,1056,568),"floor_tile")
    floor("Floor_BathThreshold",(862,384,871,468),"floor_tile")
    floor("Floor_KitchenUpper",(862,577,1056,725))
    floor("Floor_KitchenMain",(734,725,1056,1042))

    for name,bounds in [
        ("WestEntry",(678,140,698,431)),("NorthEntryLeft",(698,140,777,161)),
        ("NorthEntryRight",(883,140,1076,161)),("EastExterior",(1056,161,1076,1061)),
        ("BedroomNorth",(123,411,678,431)),("BedroomWestUpper",(123,431,143,490)),
        ("BedroomWestLower",(123,675,143,745)),("BedroomSouthExterior",(143,725,302,745)),
        ("StudyWestUpper",(282,745,302,789)),("StudyWestLower",(282,976,302,1061)),
        ("SouthWest",(302,1042,465,1061)),("SouthMiddle",(651,1042,780,1061)),
        ("SouthEast",(965,1042,1056,1061)),
    ]: wall("Wall_"+name,bounds)
    window("BedroomWest",(123,490,143,675))
    window("StudyWest",(282,789,302,976))
    window("StudySouth",(465,1042,651,1061))
    window("KitchenSouth",(780,1042,965,1061))
    wall("Wall_EntryLintel",(777,140,883,161),.6,2.2)
    # Retain the hinge side; the leaf opens outside, towards negative plan Z.
    door("Entry",(883,161),(883,55),1.06,2.2)

    for name,bounds in [
        ("BedroomEastUpper",(615,431,622,625)),("BedroomEastNib",(615,710,622,725)),
        ("BedroomStudy",(302,725,622,733)),("StudyEastReturn",(715,725,734,808)),
        ("StudyEast",(724,808,734,1042)),("BathNorth",(862,285,1056,293)),
        ("BathWestUpper",(862,293,871,384)),("BathWestLower",(862,468,871,577)),
        ("BathSouth",(871,568,1056,577)),("VentilationBox",(912,526,1002,568)),
        ("PipeEnclosure",(1002,526,1056,568)),
    ]: wall("Wall_"+name,bounds,material="wall_inner")
    for name,bounds in [("BedroomDoor",(615,625,622,710)),("StudyDoor",(622,725,715,733)),("BathDoor",(862,384,871,468))]:
        wall("Wall_"+name+"Lintel",bounds,.7,2.1,material="wall_inner")
    door("Bedroom",(615,710),(569,648),.85)
    door("Study",(715,733),(691,804),.93)
    door("Bathroom",(862,384),(838,461),.84)
    wall('Wall_EntryWardrobeDivider',(698,423,756,431),material='wall_inner')

    # Separate room finishes on interior faces preserve structural dimensions
    # and let the shared partition have a different colour on each side.
    def finish(name,bounds,material,height=2.8,base=0):
        wall('WallFinish_'+name,bounds,height,base,material)
    for name,bounds in [
        ('BedroomNorth',(143,431,615,431.4)),('BedroomSouth',(143,724.6,615,725)),
        ('BedroomWestUpper',(143,431,143.4,490)),('BedroomWestLower',(143,675,143.4,725)),
        ('BedroomEastUpper',(614.6,431,615,625)),('BedroomEastNib',(614.6,710,615,725)),
    ]: finish(name,bounds,'wall_bedroom_blue')
    for height,base in [(.85,0),(.55,2.25)]:
        finish('BedroomWindow',(143,490,143.4,675),'wall_bedroom_blue',height,base)
    finish('BedroomDoor',(614.6,625,615,710),'wall_bedroom_blue',.7,2.1)
    for name,bounds in [
        ('StudyNorth',(302,733,622,733.4)),('StudyWestUpper',(302,733,302.4,789)),
        ('StudyWestLower',(302,976,302.4,1042)),('StudySouthWest',(302,1041.6,465,1042)),
        ('StudySouthEast',(651,1041.6,724,1042)),('StudyEastReturn',(714.6,733,715,808)),
        ('StudyEast',(723.6,808,724,1042)),
    ]: finish(name,bounds,'wall_bluegray')
    for height,base in [(.85,0),(.55,2.25)]:
        finish('StudyWestWindow',(302,789,302.4,976),'wall_bluegray',height,base)
        finish('StudySouthWindow',(465,1041.6,651,1042),'wall_bluegray',height,base)
    finish('StudyDoor',(622,733,715,733.4),'wall_bluegray',.7,2.1)
    for e in api.ELEMENTS:
        if e['name'].startswith('Floor_Bedroom'): e['material']='floor_pale_oak'
        if e['name'].startswith('Floor_Study'): e['material']='floor_walnut'

    # Bedroom styling from the user's reference. All existing furniture footprints
    # stay fixed; new surface details and fixture heights are design assumptions.
    rect('BedroomRug','bedroom_rug',188,486,450,690,.012)
    for x in range(193,449,8):
        rect('BedroomRugWeave','bedroom_rug_weave',x,491,x+.35,685,.001,.012,record=False)
    for z in (491,495,681,685):
        rect('BedroomRugBorder','bedroom_rug_weave',193,z,445,z+.5,.001,.013,record=False)
    rect("Bed_Frame","bedroom_oak",227,431,408,637,.3,.10)
    rect("Bed_Mattress","bedroom_ivory",231,438,404,634,.22,.40)
    rect("Bed_Headboard","bedroom_oak_panel",227,431,408,434,1.1)
    for x in range(230,405,7):
        rect('Bed_HeadboardSlat','bedroom_oak',x,434,x+4,438,.99,.11)
    rect('Bed_HeadboardRail','bedroom_oak',227,431,408,438,.04,1.06)
    for x0,x1 in [(238,311),(322,395)]:
        rect("Bed_Pillow","bedroom_ivory",x0,444,x1,482,.12,.62)
    for x in (256,334):
        rect('Bed_AccentPillow','bedroom_navy',x,473,x+46,509,.15,.645)
    rect('Bed_CenterPillow','wall_bedroom_blue',295,498,340,524,.12,.645)
    rect("Bed_Cover","bedroom_ivory",231,499,404,634,.035,.62)
    rect('Bed_Throw','bedroom_navy',231,579,404,618,.025,.655)
    for x in (231,402):
        rect('Bed_ThrowDrape','bedroom_navy',x,579,x+2,618,.21,.445)
    for name,x0,x1 in [('BedsideLeft',178,227),('BedsideRight',410,457)]:
        rect(name,'bedroom_oak_panel',x0,436,x1,474,.475)
        rect(name+'_Top','bedroom_oak',x0,436,x1,475,.025,.475)
        for base in (.08,.275):
            rect(name+'_Drawer','bedroom_oak',x0+1,474,x1-1,475,.18,base)
            rect(name+'_Pull','bedroom_brass',(x0+x1)/2-5,475,(x0+x1)/2+5,476.5,.012,base+.10)
        # Two matching wall-mounted downlights centred over the nightstands.
        x=(x0+x1)/2
        rect(name+'_LightBackplate','bedroom_brass',x-4,431.4,x+4,433.5,.16,1.48)
        rect(name+'_LightArm','bedroom_brass',x-1,433.5,x+1,452,.02,1.57)
        disc(name+'_LightShade','bedroom_ivory',x,452,.25,.22,1.41)
        disc(name+'_LightRim','bedroom_brass',x,452,.252,.012,1.405)
        disc(name+'_LightDiffuser','bedroom_lamp',x,452,.225,.006,1.401)

    # Closed three-door wardrobe, 168 × 60 × 250 cm, facing west.
    rect('BedroomWardrobe','bedroom_oak_panel',558,431,615,599,2.385,.08)
    rect('BedroomWardrobePlinth','dark',561,433,613,597,.08)
    rect('BedroomWardrobeCrown','bedroom_oak',555,431,615,599,.035,2.465)
    for z0 in (431,487,543):
        a,b=z0+.3,z0+55.7
        rect('BedroomWardrobeDoor','bedroom_oak_panel',555.6,a,558,b,2.35,.10)
        for za,zb in ((a,a+4),(b-4,b)):
            rect('BedroomWardrobeStile','bedroom_oak',555,za,555.6,zb,2.35,.10)
        for base,height in ((.10,.05),(1.83,.045),(2.40,.05)):
            rect('BedroomWardrobeRail','bedroom_oak',555,a+4,555.6,b-4,height,base)
        rect('BedroomWardrobeHandle','bedroom_brass',552.4,b-7,553.4,b-5.8,.32,1.03)
        for base in (1.04,1.32):
            rect('BedroomWardrobeHandleMount','bedroom_brass',553.4,b-7,555.6,b-5.8,.018,base)

    def bedroom_art(name,cx,z,width,height,base,facing):
        # Original geometric seascape composition, modelled in relief in a wood frame.
        x0,x1=cx-width/2,cx+width/2
        def layer(part,mat,a,b,low,high,offset,depth):
            z0,z1=sorted((z+facing*offset,z+facing*(offset+depth)))
            rect(name+'_'+part,mat,a,z0,b,z1,high-low,low,record=False)
        layer('Canvas','bedroom_ivory',x0,x1,base,base+height,0,1.0)
        for a,b in ((x0,x0+2),(x1-2,x1)):
            layer('Frame','bedroom_oak',a,b,base,base+height,0,2.5)
        for low,high in ((base,base+.02),(base+height-.02,base+height)):
            layer('Frame','bedroom_oak',x0+2,x1-2,low,high,0,2.5)
        for index,(mat,l,r,bot,top) in enumerate([
            ('wall_bedroom_blue',.16,.83,.40,.72),
            ('bedroom_navy',.22,.63,.25,.43),
            ('bedroom_rug',.39,.86,.20,.30),
            ('bedroom_ivory',.37,.48,.34,.66),
            ('bedroom_ivory',.15,.57,.51,.55),
            ('bedroom_oak',.56,.77,.68,.72),
        ]):
            layer('Art',mat,x0+width*l,x0+width*r,base+height*bot,base+height*top,1.1+index*.17,.15)
    bedroom_art('BedroomArtHeadboard',317.5,431.5,68,.62,1.45,1)
    bedroom_art('BedroomArtSouthLeft',440,724.5,45,.62,1.38,-1)
    bedroom_art('BedroomArtSouthRight',499,724.5,45,.62,1.38,-1)
    rect("BedroomAC","white",196,700,333,723,.30,2.2)

    cabinet("EntryWardrobe",(698,161,756,423),2.5,"east")
    cabinet("HallWardrobe",(622,431,742,492),2.5,"south")
    # Full 1.24 m right-wall wardrobe; south half is on the observer's right
    # when looking east at its front. Open appliance bay faces west into hall.
    for name,bounds in [("Back",(1054,161,1056,285)),("NorthSide",(991,161,1054,162)),
                        ("Divider",(991,222,1054,223)),("SouthSide",(991,284,1054,285))]:
        rect("LaundryWardrobe"+name,"oak_light",*bounds,2.65)
    rect("LaundryWardrobeTop","oak_light",991,161,1056,285,.02,2.63)
    rect("LaundryWardrobePlinth","oak_light",991,161,1056,285,.06)
    cabinet("LaundryStorage",(991,162,1054,222),2.57,"west",base=.06)
    rect("LaundryApplianceShelf","oak_light",991,223,1054,284,.025,1.84)
    cabinet("LaundryUpperStorage",(991,223,1054,284),.765,"west",base=1.865)
    for name,base in [("Washer",.06),("Dryer",.94)]:
        rect(name,"white",993,223.5,1053,283.5,.85,base)
        rect(name+"_Door","dark",992.5,235.5,993,271.5,.39,base+.21)
        rect(name+"_Controls","metal",992.5,228.5,993,279.5,.08,base+.70)
    for x in (919,942):
        disc("PetBowl","metal",x,187,.20,.07)
        disc("PetBowlInset","dark",x,187,.155,.012,.071)

    # Bathroom: dimensioned recess 1.85 × 2.75, vent 0.90 × 0.42.
    rect("BathBase","ceramic",877,299,1050,369,.12)
    for name,bounds in [("BathWest",(877,299,883,369)),("BathEast",(1044,299,1050,369)),
                        ("BathNorth",(883,299,1044,305)),("BathSouth",(883,363,1044,369))]:
        rect(name,"ceramic",*bounds,.47,.12)
    rect("BathInner","glass",885,307,1042,361,.015,.14)
    rect("BathCurtainRail","metal",877,367,1050,369,.025,2.23)
    # Gathered curtain at the left end; shower remains visible at the east end.
    for i in range(28):
        x0=879+i*2.2;x1=x0+2.2
        z0=368+math.sin(i*math.pi/2)*1.2;z1=368+math.sin((i+1)*math.pi/2)*1.2
        x,z=xy((x0+x1)/2,(z0+z1)/2)
        box('BathShowerCurtain','fabric_light',x,z,math.hypot(x1-x0,z1-z0)/100,.005,1.61,
            base=.60,rotation=-math.atan2(z1-z0,x1-x0))
    rect('ShowerRiser','metal',1051,332,1053,334,1.17,.95)
    rect('ShowerMixer','metal',1047,324,1053,342,.045,.98)
    rect('ShowerArm','metal',1030,332,1053,334,.025,2.10)
    disc('ShowerHead','metal',1032,333,.22,.025,2.07)
    rect('ShowerHose','metal',1048.5,338,1049.5,339,.72,.56)
    rect('ShowerHandset','metal',1048,337,1051,341,.15,1.27)
    rect("BathroomMirror","mirror",1055,379,1056,439,.70,1.10)
    # Basin beneath the mirror; wall-hung vanity, dimensions provisional.
    cabinet("BathroomVanity",(1011,379,1056,439),.45,"west","oak_light",base=.30)
    rect("BasinBottom","ceramic",1011,379,1056,439,.04,.75)
    for name,bounds in [("West",(1011,379,1015,439)),("East",(1052,379,1056,439)),
                        ("North",(1015,379,1052,383)),("South",(1015,435,1052,439))]:
        rect("BasinRim"+name,"ceramic",*bounds,.08,.79)
    rect("BasinInterior","white",1016,384,1051,434,.01,.795)
    rect("BasinTap","metal",1050,407,1053,410,.23,.87)
    rect("BasinSpout","metal",1040,407,1053,410,.025,1.07)
    # Suspended bowl, no floor pedestal or exposed cistern.
    rect("ToiletWallHungBody","ceramic",1000,467,1041,493,.22,.18)
    disc("ToiletBowl","ceramic",1006,480,.40,.10,.35)
    disc("ToiletSeatOpening","dark",1006,480,.25,.006,.451)
    cabinet("BathTallCabinet",(877,521,912,568),2.8,"north","oak")
    rect("ToiletInstallationEnclosure","white",1041,445,1056,527,1.15)
    rect("ToiletFlushPlate","metal",1040.5,470,1041,490,.12,.91)

    # Kitchen modules: upper run 60+60+60; east run 60+60+60+50.
    cabinet("Fridge",(876,577,936,637),2.0,"south","white")
    cabinet("FreezerBase",(936,577,996,637),.85,"south","oak_light")
    rect("FreezerWorktop","white",936,577,996,637,.04,.85)
    rect("MicrowaveBody","white",941,598,991,636,.32,.89)
    rect("Microwave","dark",944,636,988,636.5,.25,.925)
    for name,z0,z1 in [("KettleCorner",577,637),("SinkUnit",637,697),("Dishwasher",697,757),
                       ("OvenUnit",757,817),("EndUnit",817,867)]:
        cabinet(name,(996,z0,1056,z1),.85,"west")
        rect(name+"_Worktop","white",996,z0,1056,z1,.04,.85)
    disc("KitchenSink","metal",1026,667,.46,.012,.891)
    disc("KitchenSinkInterior","dark",1026,667,.38,.007,.904)
    rect("KitchenTap","metal",1049,656,1052,659,.30,.90)
    disc("Kettle","metal",1030,608,.21,.25,.89)
    rect("Cooktop","dark",999,762,1052,812,.022,.89)
    for x in (1011,1040):
        for z in (775,798): disc("HobRing","metal",x,z,.145,.006,.915)
    rect("OvenDoor","dark",995.5,765,996.5,809,.47,.20)
    rect("Hood","metal",1011,757,1056,817,.16,1.72)
    # Continuous L-shaped upper row; higher bridging unit above refrigerator.
    cabinet("KitchenUpperFridge",(876,577,936,637),.55,"south","white",base=2.10)
    cabinet("KitchenUpperFreezer",(936,577,996,612),1.15,"south","white",base=1.50)
    cabinet("KitchenUpperCorner",(1021,577,1056,637),1.15,"west","white",base=1.50)
    cabinet("KitchenUpperCornerReturn",(996,577,1021,612),1.15,"south","white",base=1.50)
    for name,z0,z1,base in [("Sink",637,697,1.50),("Dishwasher",697,757,1.50),
                            ("Hood",757,817,1.88),("End",817,867,1.50)]:
        cabinet("KitchenUpper"+name,(1021,z0,1056,z1),2.65-base,"west","white",base=base)
    for z in (867,917,967): cabinet("TVConsole",(1026,z,1056,z+50),.46,"west")
    rect("TV","dark",1050,899,1055,1004,.68,.75)
    rect("KitchenAC","white",1033,897,1056,997,.3,2.25)
    sofa("KitchenSofa",(738,857,798,1017),"east","terracotta")
    # User revision supersedes the hexagon in the source PNG.
    # User-specified 120×75 cm, two chairs along each long side.
    rect("DiningTable","oak_light",734,735,854,810,.055,.715)
    for x in (740,844):
        for z in (741,800): rect("DiningTableLeg","dark",x,z,x+4,z+4,.715)
    for index,(x,z,angle) in enumerate([(763,721,math.pi),(825,721,math.pi),
                                       (763,825,0),(825,825,0)],1):
        px,pz=xy(x,z)
        api.add_chair("DiningChair"+str(index),px,pz,angle,width=.42,depth=.42)

    # Study: north sofa, SW desk, east piano, guitar in SE corner.
    # Replace the low shelf at the window-side end of the sofa, as confirmed.
    for x0,x1 in ((308,310),(419,421)):
        rect('StudyOpenShelfSide','oak_light',x0,733,x1,771,2.50)
    rect('StudyOpenShelfDivider','oak_light',363.5,733,365.5,771,2.46,.02)
    for base in (.00,.40,.81,1.22,1.63,2.04,2.48):
        rect('StudyOpenShelfBoard','oak_light',310,733,419,771,.02,base)
    for x,base,material in ((315,.42,'fabric_blue'),(320,.42,'white'),(325,.42,'terracotta'),
                             (373,1.24,'fabric_blue'),(378,1.24,'fabric'),(383,1.24,'white')):
        rect('StudyShelfBook',material,x,740,x+4,766,.27,base)
    sofa("StudySofa",(420,733,620,813),"south")
    rect("ComputerDesk","oak_light",307,951,457,1037,.05,.73)
    for x in (311,449):
        for z in (957,1028): rect("DeskLeg","dark",x,z,x+4,z+4,.73)
    for index,x0 in enumerate((315,386),1):
        rect('Monitor'+str(index),'dark',x0,1009,x0+62,1013,.36,.90)
        rect('Monitor'+str(index)+'Screen','fabric_blue',x0+2,1008.7,x0+60,1009,.31,.925)
        rect('Monitor'+str(index)+'Stand','metal',x0+26,1002,x0+36,1020,.12,.78)
    rect("Keyboard","dark",350,987,411,1003,.025,.78)
    x,z=xy(382,949); api.add_office_chair("Study",x,z,math.pi)
    rect("Piano","dark",686,849,722,989,1.05)
    rect("PianoLowerBody","dark",672,849,686,989,.72)
    rect("PianoKeyboard","white",672,853,686,985,.06,.73)
    for z in range(857,984,6): rect("PianoBlackKey","dark",679,z,686,z+2,.025,.79)
    disc("GuitarBody","oak",702,1014,.30,.10,.12)
    rect("GuitarNeck","oak",699,1011,705,1018,.77,.21)
    rect("GuitarHead","dark",697,1011,707,1018,.15,.98)

    # Radiator footprint dimensions explicitly supplied on measurement plan.
    for name,bounds in [("BedroomRadiator",(143,528,160,632)),
                        ("StudyWestRadiator",(302,818,313,942)),
                        ("StudySouthRadiator",(491,1031,615,1042)),
                        ("KitchenRadiator",(824,1025,918,1042))]:
        rect(name,"white",*bounds,.52,.15)
    # External AC baskets shown outside facades; elevation is unspecified.
    for name,bounds in [("BedroomOutdoorBasket",(44,573,123,675)),("KitchenOutdoorBasket",(861,1061,965,1119))]:
        x0,z0,x1,z1=bounds
        rect(name+"_Tray","metal",*bounds,.04,.50)
        rect(name+"_Unit","white",x0+5,z0+5,x1-5,z1-5,.55,.54)
        for x in (x0,x1-2): rect(name+"_Rail","metal",x,z0,x+2,z1,.7,.50)

    # Window textiles: pleated strips form a continuous folded surface.
    # Position in front of radiators. South study window uses sill-length cloth
    # to keep the existing computer desk clear. All textile sizes are provisional.
    def curtain_set(name,axis,start,end,front,sheer_front,bottom=.04,wall_span=None):
        top=2.69
        def cloth(part,a,b,normal,amplitude,material):
            steps=math.ceil((b-a)/2.5)
            for i in range(steps):
                u0=a+(b-a)*i/steps;u1=a+(b-a)*(i+1)/steps
                v0=normal+amplitude*math.sin((u0-a)*math.tau/10)
                v1=normal+amplitude*math.sin((u1-a)*math.tau/10)
                p0=(v0,u0) if axis=='west' else (u0,v0)
                p1=(v1,u1) if axis=='west' else (u1,v1)
                x,z=xy((p0[0]+p1[0])/2,(p0[1]+p1[1])/2)
                dx,dz=p1[0]-p0[0],p1[1]-p0[1]
                box('Curtain_'+name+'_'+part,material,x,z,math.hypot(dx,dz)/100,.004,
                    top-bottom,base=bottom,rotation=-math.atan2(dz,dx))
        track_start,track_end=start-18,end+18
        if wall_span:
            track_start,track_end=wall_span
            cloth('LeftPanel',track_start+.5,start+16,front,1.2,'bedroom_navy')
            cloth('RightPanel',end-25,track_end-.5,front,1.2,'bedroom_navy')
            cloth('Tulle',track_start+.5,track_end-.5,sheer_front,.45,'curtain_sheer')
        else:
            cloth('LeftPanel',start-16,start+28,front,1.2,'curtain_linen')
            cloth('RightPanel',end-28,end+16,front,1.2,'curtain_linen')
            cloth('Tulle',start,end,sheer_front,.45,'curtain_sheer')
        if axis=='west':
            rect('Curtain_'+name+'_Track','white',front-2,track_start,front+2,track_end,.025,2.72)
        else:
            rect('Curtain_'+name+'_Track','white',track_start,front-2,track_end,front+2,.025,2.72)

    curtain_set('BedroomWest','west',490,675,168,163,wall_span=(431,725))
    curtain_set('StudyWest','west',789,976,320,315,bottom=.90)
    curtain_set('StudySouth','south',465,651,1021,1027,bottom=.90)
    curtain_set('KitchenSouth','south',780,965,1021,1023.7)

    api.LAYOUT_FOOTPRINTS = list(FOOTPRINTS)
