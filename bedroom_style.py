"""Approved blue / milk-white / oak bedroom, local 13 September revision.

Keep shell, PDF footprints, sliding hardware and lighting circuit count.
One static coverlet mesh conceals the sleeping pillows and drapes over the bed.
"""
def build(api):
    def node(prefix):
        return next(e for e in api.ELEMENTS if e['name'].startswith(prefix))

    def put(e, **changes):
        e['finished'] = {**api.resolved(e), **changes}
        e['finished'].pop('finished', None)

    def material(name, rgb, pattern=0, roughness=.85):
        api.MATERIALS[name] = dict(color=[*rgb, 1], pattern=pattern,
                                   roughness=roughness, metallic=0)

    material('bedroom_render_blue', (.46, .52, .57))
    material('bedroom_render_white', (.94, .93, .90))
    material('bedroom_render_oak', (.75, .61, .44), 1)
    material('bedroom_render_navy', (.10, .17, .29), 2)
    material('bedroom_render_rug', (.76, .73, .66), 2)
    for i, factor in enumerate((.97, 1., 1.025)):
        material('bedroom_render_floor_'+str(i), [v*factor for v in (.79, .67, .51)], 1)

    for e in api.ELEMENTS:
        r = api.resolved(e); n = e['name']; mat = r['material']
        if r['category'] == 'finish_wall' and mat == 'wall_bedroom_blue':
            put(e, material='bedroom_render_blue')
        elif n.startswith('BedroomWardrobe'):
            # Preserve recessed shadows so the sliding tracks remain legible.
            if not any(k in n for k in ('Recess', 'Plinth')):
                put(e, material='bedroom_render_white')
        elif n.startswith(('BedsideLeft', 'BedsideRight')) and '_Light' not in n:
            put(e, material='bedroom_render_white' if '_Pull' in n else 'bedroom_render_oak')
        elif n.startswith(('Bed_Frame', 'Bed_Headboard')):
            put(e, material='bedroom_render_oak')
        elif n.startswith('BedroomArt'):
            if '_Frame' in n: put(e, material='bedroom_render_oak')
            elif mat == 'wall_bedroom_blue': put(e, material='bedroom_render_blue')
            elif mat == 'bedroom_navy': put(e, material='bedroom_render_navy')
        elif n.startswith('Curtain_BedroomWest') and any(k in n for k in ('LeftPanel','RightPanel')):
            put(e, material='bedroom_render_navy')
        elif n.startswith('BedroomRug'):
            put(e, material='bedroom_render_rug')
        elif r['category'] == 'finish_floor' and mat.startswith('floor_pale_oak'):
            x, _, z = r['position']
            if -.001 < x < 4.73 and 2.699 < z < 5.63:
                put(e, material='bedroom_render_floor_'+(mat[-1] if mat[-1] in '012' else '1'))

    # Remove only the old slats/rail and bedding, never the bed frame/mattress.
    api.ELEMENTS[:] = [e for e in api.ELEMENTS if not e['name'].startswith((
        'Bed_HeadboardSlat', 'Bed_HeadboardRail', 'Bed_Cover', 'Bed_Throw',
        'Bed_Pillow', 'Bed_AccentPillow', 'Bed_CenterPillow'))]
    head = node('Bed_Headboard_')
    put(head, detail=dict(type='rounded', radius=.008, steps=3), noEdges=True)
    mat = api.resolved(node('Bed_Mattress_'))
    x, y, z = mat['position']; w, h, d = mat['size']; top = y+h/2+.014
    api.add_box('Bed_Cover', 'bedroom_render_navy', x, z, w+.065, d+.065,
                .58, base=top-.43)
    cover = api.ELEMENTS[-1]
    cover.update(noEdges=True, detail=dict(type='coverlet', top=.14, drop=.32, pillowRise=.105))

    # Two small cylindrical white wall lights, matching the user's reference.
    # Keep original plan X anchors and elevations; reduce projection/depth.
    for prefix in ('BedsideLeft', 'BedsideRight'):
        plate = node(prefix+'_LightBackplate_'); p = api.resolved(plate)['position']
        x, y, z = p; wall = z-api.resolved(plate)['size'][2]/2
        put(plate, material='bedroom_render_white', size=[.075,.21,.024],
            position=[x,y,wall+.012], detail=dict(type='rounded',radius=.003,steps=1),noEdges=True)
        arm = node(prefix+'_LightArm_')
        put(arm, material='bedroom_render_white', position=[x,y+.035,wall+.066],
            size=[.016,.016,.085], detail=dict(type='rounded',radius=.003,steps=1), noEdges=True)
        shade = node(prefix+'_LightShade_'); cz = wall+.133; cy = y+.035
        shell = dict(type='lathe', segments=32,
            rings=[[.5,-.5],[.5,.5],[.455,.5],[.455,-.5],[.5,-.5]])
        put(shade, material='bedroom_render_white', position=[x,cy,cz],
            size=[.11,.145,.11],detail=shell,noEdges=True)
        rim = node(prefix+'_LightRim_')
        put(rim, material='bedroom_render_white', position=[x,cy+.071,cz],
            size=[.11,.003,.11],detail=shell,noEdges=True)
        diffuser = node(prefix+'_LightDiffuser_')
        put(diffuser, position=[x,cy-.070,cz],size=[.099,.003,.099],noEdges=True)
        api.add_box(prefix+'_LightSwitch','bedroom_render_white',x,wall+.030,.019,.012,.019,base=y-.067)
        switch = api.ELEMENTS[-1]
        switch.update(noEdges=True, detail=dict(type='pillow',power=2))
        ident = 'sconce-'+prefix.lower()
        members = [e for e in api.ELEMENTS if e['name'].startswith(prefix+'_Light')]
        source = [x,cy-.096,cz]
        for light in getattr(api,'SCENE_LIGHTS',[]):
            if light['fixture']==ident: light['position']=source
        for record in getattr(api,'LIGHTING_LAYOUT',[]):
            if record['id']==ident:
                record.update(position=source,elements=[e['name'] for e in members])
                for e in members: e['lightingId']=ident
