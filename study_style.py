"""Approved sage/white/oak study concept; illustrative compact PC equipment.

Keep surveyed shell and PDF furniture footprints. All additions are static,
using shared procedural meshes/materials (no new lights or per-frame work).
"""
def build(api):
    def put(e, **changes):
        e['finished'] = {**api.resolved(e), **changes}
        e['finished'].pop('finished', None)

    def node(prefix):
        return next(e for e in api.ELEMENTS if e['name'].startswith(prefix))

    def material(name, color, pattern=0, roughness=.85):
        api.MATERIALS[name] = dict(color=[*color, 1], pattern=pattern,
                                   roughness=roughness, metallic=0)

    for name, color, pattern in [
        ('study_sage', (.59, .61, .55), 0),
        ('study_oak', (.73, .59, .42), 1),
        ('study_white', (.94, .935, .91), 0),
        ('study_sofa', (.72, .69, .63), 2),
        ('study_cushion', (.83, .80, .74), 2),
        ('study_olive', (.48, .52, .40), 2),
        ('study_charcoal', (.22, .235, .235), 2),
        ('study_blind', (.76, .735, .68), 2),
        ('study_rug', (.69, .67, .62), 2),
        ('study_pc', (.13, .145, .15), 0),
        ('study_pc_seam', (.055, .065, .07), 0),
        ('study_screen', (.075, .10, .12), 0),
        ('study_key', (.22, .24, .25), 0),
    ]:
        material(name, color, pattern)

    def box(name, mat, p, s, detail=None):
        api.add_box(name, mat, p[0], p[2], s[0], s[2], s[1], base=p[1]-s[1]/2)
        e = api.ELEMENTS[-1]
        e.update(position=list(p), size=list(s), noEdges=True)
        if detail: e['detail'] = detail
        return e

    def rounded(name, mat, p, s, radius=.003):
        return box(name, mat, p, s, dict(type='rounded', radius=radius, steps=1))

    def rod(name, mat, a, b, radius=.003):
        p = [(a[i]+b[i])/2 for i in range(3)]
        s = [abs(a[i]-b[i])+2*radius for i in range(3)]
        return box(name, mat, p, s, dict(type='rod', radius=radius,
            start=[(a[i]-p[i])/s[i] for i in range(3)],
            end=[(b[i]-p[i])/s[i] for i in range(3)]))

    # Reassign individual elements; shared materials elsewhere stay untouched.
    for e in api.ELEMENTS:
        r = api.resolved(e); n = e['name']; mat = r['material']
        if r['category'] == 'finish_wall' and mat == 'wall_bluegray':
            put(e, material='study_sage')
        elif r['category'] == 'finish_floor' and mat.startswith('floor_walnut'):
            target = 'study_oak'
            if mat[-1:] in ('0', '1', '2'):
                target += '_'+mat[-1]
                factor = (.97, 1., 1.025)[int(mat[-1])]
                material(target, [c*factor for c in (.73, .59, .42)], 1)
            put(e, material=target)
        elif n.startswith(('ComputerDesk', 'DeskLeg')):
            put(e, material='study_white')
        elif n.startswith('StudySofa'):
            put(e, material='study_oak' if 'Leg' in n else 'study_sofa')
        elif n.startswith('StudyOpenShelf'):
            put(e, material='study_oak')
        elif n.startswith('Furniture_Study') and mat.startswith('fabric'):
            put(e, material='study_charcoal')
    for i, x in enumerate((2.88, 3.86)):
        box('StudySofa_Accent', 'study_olive' if i == 0 else 'study_cushion',
            [x, .735, 6.08], [.36, .36, .12], dict(type='pillow', power=3))

    # Keep each existing window reveal and radiator clear. Blinds occupy only
    # the upper 420 mm; white cassette and bottom weight describe real hardware.
    api.ELEMENTS[:] = [e for e in api.ELEMENTS
                      if not e['name'].startswith(('Curtain_StudyWest_', 'Curtain_StudySouth_'))]
    for room, axis, at in [('StudyWest', 0, 1.53), ('StudySouth', 2, 8.83)]:
        win = api.resolved(node('Window_'+room+'_glass'))
        along = 2 if axis == 0 else 0
        width = win['size'][along]-.04
        for label, mat, y, h, depth in [
            ('Cassette', 'study_white', 2.219, .048, .05),
            ('Fabric', 'study_blind', 1.988, .420, .004),
            ('BottomBar', 'study_white', 1.777, .018, .013),
        ]:
            p = list(win['position']); p[axis] = at; p[1] = y
            s = [.004, h, .004]; s[axis] = depth; s[along] = width
            rounded('StudyBlind_'+room+'_'+label, mat, p, s, .001)
    base = api.FINISH_SETTINGS['dry_floor']
    rounded('StudyRug', 'study_rug', [3.55, base+.003, 7.035], [2.15, .006, 1.25], .001)

    # Smooth ergonomic indentation, still precisely 1400 x 600 in plan.
    desk = node('ComputerDesk_'); d = api.resolved(desk)
    put(desk, detail=dict(type='desktop', cutout=.065), noEdges=True)
    top = d['position'][1]+d['size'][1]/2
    # Facing the desk is +Z: the seated user's RIGHT is -X.
    api.ELEMENTS[:] = [e for e in api.ELEMENTS
                      if not e['name'].startswith(('Monitor1', 'Monitor2', 'Keyboard'))]
    for i, x in enumerate((2.775, 2.21), 1):
        prefix = 'Monitor'+str(i)
        rounded(prefix, 'study_pc', [x, top+.265, 8.65], [.54, .32, .029])
        rounded(prefix+'Screen', 'study_screen', [x, top+.269, 8.634], [.516, .291, .002], .001)
        rounded(prefix+'Chin', 'study_pc', [x, top+.112, 8.632], [.528, .017, .004], .001)
        rounded(prefix+'Stem', 'study_pc', [x, top+.071, 8.675], [.035, .14, .033])
        rounded(prefix+'Foot', 'study_pc', [x, top+.008, 8.62], [.20, .016, .16])

    # Compact tower 190 x 400 x 360 mm, clear of screens and tabletop edges.
    x, z = 1.805, 8.50
    for dx in (-.070, .070):
        for dz in (-.16, .16):
            rounded('StudyPC_Foot', 'study_pc_seam', [x+dx, top+.006, z+dz], [.026, .012, .028])
    rounded('StudyPC_Case', 'study_pc', [x, top+.192, z], [.19, .36, .40], .006)
    rounded('StudyPC_Front', 'study_pc_seam', [x, top+.192, z-.201], [.165, .324, .003], .001)
    for j in range(14):
        box('StudyPC_Vent', 'study_key', [x, top+.052+j*.019, z-.204], [.13, .003, .002])
    for dz in (-.15, .15):
        box('StudyPC_PanelSeam', 'study_pc_seam', [x+.0955, top+.19, z+dz], [.001, .31, .002])
    rounded('StudyPC_PowerButton', 'study_key', [x+.052, top+.358, z-.201], [.015, .015, .004])
    for dx in (-.03, -.007):
        box('StudyPC_USB', 'study_pc_seam', [x+dx, top+.373, z-.12], [.012, .002, .006])
    # Compact keyboard with individual keycaps and larger modifiers; no lights.
    kx, kz = 2.49, 8.36
    rounded('StudyKeyboard_Base', 'study_pc', [kx, top+.010, kz], [.36, .020, .13])
    for row in range(5):
        for col in range(14):
            if row == 0 and 3 <= col <= 9: continue
            rounded('StudyKeyboard_Key', 'study_key',
                [kx-.161+col*.0247, top+.024, kz-.05+row*.025], [.020, .007, .020], .001)
    rounded('StudyKeyboard_Space', 'study_key', [kx-.013, top+.024, kz-.05], [.165, .007, .020], .001)
    rounded('StudyMousePad', 'study_charcoal', [2.145, top+.0015, 8.35], [.24, .003, .21], .001)
    box('StudyMouse_Body', 'study_pc', [2.145, top+.022, 8.35], [.065, .038, .115], dict(type='pillow', power=3))
    box('StudyMouse_ButtonSplit', 'study_pc_seam', [2.145, top+.040, 8.38], [.0015, .001, .045])
    rounded('StudyMouse_Wheel', 'study_key', [2.145, top+.042, 8.37], [.010, .008, .019], .002)
    # A short tidy cable route into a tray below the rear desk edge.
    for x in (2.21, 2.775):
        rod('StudyCable_Monitor', 'study_pc_seam', [x, top+.18, 8.68], [x, top-.05, 8.70])
    rounded('StudyCable_Tray', 'study_pc', [2.47, top-.075, 8.69], [.85, .06, .09])
