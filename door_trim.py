"""Interior door casings, referenced to finished openings after all plan changes."""


def build(api):
    width,depth=.06,.01
    trims=[]
    def edge(e,axis,sign):return e['position'][axis]+sign*e['size'][axis]/2
    for room in ('Bedroom','Study','Bathroom'):
        head=api.resolved(next(e for e in api.ELEMENTS if e['name'].startswith('DoorHead_'+room+'_')))
        normal=0 if head['size'][0]<head['size'][2] else 2
        along=2 if normal==0 else 0
        jambs=sorted([api.resolved(e) for e in api.ELEMENTS if e['name'].startswith('DoorJamb_'+room+'_')],
                     key=lambda e:e['position'][along])
        lo,hi=edge(jambs[0],along,1),edge(jambs[1],along,-1)
        top=edge(head,1,-1)
        for side in (-1,1):
            wet=room=='Bathroom' and side==1
            layer=api.FINISH_SETTINGS['tile_adhesive' if wet else 'plaster_wallpaper']
            base=api.FINISH_SETTINGS['wet_floor' if wet else 'dry_floor']
            face=edge(head,normal,side)+side*layer
            n=face+side*depth/2
            for part,start,end,bottom,height in (
                ('Left',lo-width,lo,base,top-base),
                ('Right',hi,hi+width,base,top-base),
                ('Top',lo-width,hi+width,top,width),
            ):
                p=[0,0,0];s=[0,0,0]
                p[normal]=n;p[along]=(start+end)/2
                s[normal]=depth;s[along]=end-start
                api.add_box(f'DoorCasing_{room}_{"A" if side<0 else "B"}_{part}',
                            'door_ivory',p[0],p[2],s[0],s[2],height,base=bottom,category='finish_wall')
                trims.append(api.ELEMENTS[-1])

    # Butt the thin skirting against the vertical casings instead of running
    # through them. Only skirting geometry is shortened; walls stay unchanged.
    for e in list(api.ELEMENTS):
        if not e['name'].startswith('Skirting_'):continue
        along=0 if e['size'][0]>e['size'][2] else 2
        normal=2 if along==0 else 0
        spans=[(edge(e,along,-1),edge(e,along,1))]
        for trim in trims:
            if '_Top_' in trim['name']:continue
            if min(edge(e,normal,1),edge(trim,normal,1))-max(edge(e,normal,-1),edge(trim,normal,-1))<=1e-6:continue
            a,b=edge(trim,along,-1),edge(trim,along,1)
            remaining=[]
            for lo,hi in spans:
                if a>=hi or b<=lo:remaining.append((lo,hi));continue
                if a>lo:remaining.append((lo,a))
                if b<hi:remaining.append((b,hi))
            spans=remaining
        api.ELEMENTS.remove(e)
        for i,(lo,hi) in enumerate(spans):
            if hi-lo<1e-5:continue
            part={**e,'position':list(e['position']),'size':list(e['size'])}
            part['position'][along]=(lo+hi)/2;part['size'][along]=hi-lo
            if i:part['name']=api.unique_name(e['name']+'_Split')
            api.ELEMENTS.append(part)
