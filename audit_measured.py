"""Offline geometric audit. Images are rasterized directly from exported scene data.

This checks geometry independently of the WebGL camera; it is not a browser screenshot.
"""
from pathlib import Path
import base64
import html
import json
import math
import struct
import numpy as np
from PIL import Image, ImageDraw
import generate_model as model

ROOT=Path(__file__).resolve().parent
SOURCES=[Path('/Users/mgovorusenko/Desktop/Замеры (без мебели).png'),Path('/Users/mgovorusenko/Desktop/Планировка Лены.png')]


def footprint(e):
    x,y,z=e['position']; sx,sy,sz=e['size']; angle=e.get('rotation',0)
    if e['shape']=='cylinder':
        local=[(math.cos(i*math.tau/48)/2,math.sin(i*math.tau/48)/2) for i in range(48)]
    elif e['shape']=='hexagon':
        local=[(0,-.5),(.5,-.313),(.5,.307),(0,.5),(-.5,.307),(-.5,-.313)]
    else: local=[(-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)]
    return [(143+100*(x+a*sx*math.cos(angle)+b*sz*math.sin(angle)),
             161+100*(z-a*sx*math.sin(angle)+b*sz*math.cos(angle))) for a,b in local]


def node(prefix):
    return next(e for e in model.ELEMENTS if e['name'].startswith(prefix+'_'))


def checks():
    if getattr(model,'PDF_REFERENCE',False):
        from audit_designer import checks as designer_checks
        return designer_checks()
    rows=[]
    def check(label,source,value):
        assert abs(source-value)<.00011,(label,source,value)
        rows.append(dict(measurement=label,source=source,model=round(value,4)))
    check('Черновая высота',2.8,node('Wall_EastExterior')['size'][1])
    check('От входного проёма до внутренней грани правой стены',1.73,9.13-(node('Wall_EntryLintel')['position'][0]+.53))
    check('Санузел снаружи по верхней стене',1.94,node('Wall_BathNorth')['size'][0])
    check('Санузел внутри — ширина',1.85,node('Floor_Bathroom')['size'][0])
    check('Санузел внутри — глубина',2.75,node('Floor_Bathroom')['size'][2])
    check('Короб вентиляции — ширина',.9,node('Wall_VentilationBox')['size'][0])
    check('Короб вентиляции — глубина',.42,node('Wall_VentilationBox')['size'][2])
    check('Слева от короба',.41,(node('Wall_VentilationBox')['position'][0]-.45)-(node('Floor_Bathroom')['position'][0]-.925))
    check('Справа от короба до правой стены',.54,9.13-(node('Wall_VentilationBox')['position'][0]+.45))
    check('Спальня — верхняя ширина',4.72,node('Floor_Bedroom')['size'][0])
    check('Спальня — левая глубина',2.94,node('Floor_Bedroom')['size'][2])
    check('Кабинет — нижняя ширина',4.22,node('Floor_Study')['size'][0])
    check('Кабинет — северная перегородка',3.2,node('Wall_BedroomStudy')['size'][0])
    kitchen=node('Floor_KitchenMain'); upper=node('Floor_KitchenUpper')
    check('Кухня — правая длина',4.65,kitchen['position'][2]+kitchen['size'][2]/2-(upper['position'][2]-upper['size'][2]/2))
    check('Кухня — рабочая ширина',3.22,node('Floor_KitchenMain')['size'][0])
    sill=node('KitchenSouth_Sill')
    check('Простенок слева от кухонного окна',.46,sill['position'][0]-sill['size'][0]/2-(kitchen['position'][0]-kitchen['size'][0]/2))
    check('Простенок справа от кухонного окна',.91,kitchen['position'][0]+kitchen['size'][0]/2-(sill['position'][0]+sill['size'][0]/2))
    check('Верхняя глухая часть перегородки спальни',1.94,node('Wall_BedroomEastUpper')['size'][2])
    for name in ['Fridge','FreezerBase']:
        check(name+' ширина',.60,node(name)['size'][0]); check(name+' глубина',.60,node(name)['size'][2])
    for name,length in [('KettleCorner',.6),('SinkUnit',.6),('Dishwasher',.6),('OvenUnit',.6),('EndUnit',.5)]:
        check(name+' глубина',.6,node(name)['size'][0]); check(name+' длина',length,node(name)['size'][2])
    for name,sx,sz in [('StudyWestRadiator',.11,1.24),('StudySouthRadiator',1.24,.11),('KitchenRadiator',.94,.17)]:
        check(name+' X',sx,node(name)['size'][0]); check(name+' Z',sz,node(name)['size'][2])
    for e in model.ELEMENTS:
        assert all(math.isfinite(v) and v>0 for v in e['size']),e
        assert all(math.isfinite(v) for v in e['position']),e
        if e['category']!='ceiling':assert e['position'][1]+e['size'][1]/2 <=2.8001,e['name']
    for primitive in [model.cube_geometry,model.cylinder_geometry,model.hexagon_geometry,model.ceiling_geometry]:
        p,n,idx=primitive(); p=np.array(p).reshape(-1,3); n=np.array(n).reshape(-1,3)
        for a,b,c in np.array(idx).reshape(-1,3):
            assert np.dot(np.cross(p[b]-p[a],p[c]-p[a]),n[a]+n[b]+n[c])>0,primitive.__name__
    # Scene/export identity and binary accessor bounds.
    document_bytes=(ROOT/'apartment-model.glb').read_bytes()
    length=struct.unpack_from('<I',document_bytes,12)[0]
    document=json.loads(document_bytes[20:20+length])
    assert len(document['nodes'])==len(model.ELEMENTS)+1
    for actual,e in zip(document['nodes'][1:],model.ELEMENTS):
        e=model.resolved(e)
        assert actual['name']==e['name'] and actual['translation']==e['position'] and actual['scale']==e['size']
    for view in document['bufferViews']:
        assert view['byteOffset']+view['byteLength']<=document['buffers'][0]['byteLength']
    # Regression tests for the user's seven corrections (distinct from survey checks).
    assert not any(e['name'].startswith(('FreezerMicrowaveColumn_','ToiletTank_','ToiletBase_','UnspecifiedSanitaryBlock_')) for e in model.ELEMENTS)
    assert node('DiningTable')['shape']=='box'
    assert node('DiningTable')['size']==[1.2,.055,.75]
    chairs=[e for e in model.ELEMENTS if e['name'].startswith('Furniture_DiningChair') and '_seat_' in e['name']]
    assert len(chairs)==4
    assert len([e for e in model.ELEMENTS if e['name'].startswith('KitchenUpper') and '_Handle_' not in e['name']])==8
    assert node('KitchenUpperCorner')['size'][0]==.35
    assert node('KitchenUpperCornerReturn')['size'][2]==.35
    assert node('Wall_EntryWardrobeDivider')['size']==[.58,2.8,.08]
    assert node('ComputerDesk')['size']==[1.5,.05,.86]
    desk_foot=footprint(node('ComputerDesk'))
    assert min(x for x,z in desk_foot)==307 and max(x for x,z in desk_foot)==457
    assert min(z for x,z in desk_foot)==951 and max(z for x,z in desk_foot)==1037
    assert node('Monitor1')['size'][0]==.62 and node('Monitor2')['size'][0]==.62
    assert node('StudyOpenShelfSide')['size'][1]==2.50
    assert len([e for e in model.ELEMENTS if e['name'].startswith('StudyOpenShelfBoard_')])==7
    assert not any(e['name'].startswith('StudyShelf_') for e in model.ELEMENTS)
    assert min(z for x,z in footprint(node('TV')))==899
    assert node('BathTallCabinet')['size'][1]==2.8 and node('BathTallCabinet')['material']=='oak'
    assert not any(e['name'].startswith('BathroomMirrorCabinet_') for e in model.ELEMENTS)
    assert node('BathroomMirror')['size'][0]==.01
    assert node('ShowerRiser')['position'][0]>9
    assert len([e for e in model.ELEMENTS if e['name'].startswith('BathShowerCurtain_')])==28
    assert node('EndUnit')['size'][2]==.50
    tv=[e for e in model.ELEMENTS if e['name'].startswith('TVConsole_') and '_Handle_' not in e['name']]
    assert len(tv)==3 and all(e['size'][2]==.50 for e in tv)
    assert node('Floor_Bedroom')['material']=='rough_floor'
    assert node('Floor_Study')['material']=='rough_floor'
    assert node('Finish_Floor_Bedroom')['material']=='floor_pale_oak'
    assert node('Finish_Floor_Study')['material']=='floor_walnut'
    assert node('WallFinish_BedroomNorth')['material']=='wall_bedroom_blue'
    # Bedroom reference styling: preserve the plan while adding surface detail.
    assert node('Bed_Frame')['size']==[1.81,.3,2.06]
    assert node('Curtain_BedroomWest_Track')['size'][2]==2.94
    for part in ('LeftPanel','RightPanel'):
        assert node('Curtain_BedroomWest_'+part)['material']=='bedroom_navy'
    assert node('Bed_Cover')['material']=='bedroom_ivory'
    assert len([e for e in model.ELEMENTS if e['name'].startswith('Bed_HeadboardSlat_')])==25
    assert len([e for e in model.ELEMENTS if e['name'].startswith('BedroomWardrobeDoor_')])==3
    assert len([e for e in model.ELEMENTS if e['name'].startswith('BedroomWardrobeHandle_')])==3
    for side in ('Left','Right'):
        lamp=node('Bedside'+side+'_LightShade')
        table=node('Bedside'+side)
        assert lamp['position'][0]==table['position'][0]
        assert lamp['position'][1]>1.4
    for art in ('Headboard','SouthLeft','SouthRight'):
        assert node('BedroomArt'+art+'_Canvas')['material']=='bedroom_ivory'
    assert node('WallFinish_StudyNorth')['material']=='wall_bluegray'
    assert len([c for c in chairs if c['position'][2]<node('DiningTable')['position'][2]])==2
    assert len([c for c in chairs if c['position'][2]>node('DiningTable')['position'][2]])==2
    assert node('FreezerBase')['size'][1]==.85
    assert node('ToiletWallHungBody')['position'][1]-node('ToiletWallHungBody')['size'][1]/2>.15
    assert node('BasinBottom')['position'][1]>.7
    assert node('LaundryWardrobeTop')['size'][2]==1.24
    for name in ('Washer','Dryer'):
        assert node(name+'_Door')['position'][0]<node(name)['position'][0]-.3
        assert node(name)['position'][2]>1.61/2
    assert abs(node('Door_Entry')['position'][0]-7.4)<.0001
    for window in ('BedroomWest','StudyWest','StudySouth','KitchenSouth'):
        assert node('Curtain_'+window+'_Track')['position'][1]>2.7
        for part in ('LeftPanel','RightPanel','Tulle'):
            cloth=node('Curtain_'+window+'_'+part)
            assert cloth['category']=='furniture'
            bottom=cloth['position'][1]-cloth['size'][1]/2
            assert abs(bottom-(.90 if window in ('StudyWest','StudySouth') else .04))<.0001
        assert model.MATERIALS[node('Curtain_'+window+'_Tulle')['material']]['color'][3]<.3
    # Chair bodies stay clear of the kitchen sofa and west partition.
    sofa=node('KitchenSofa_Base')
    sofa_pts=footprint(sofa)
    for chair in [e for e in model.ELEMENTS if e['name'].startswith('Furniture_DiningChair')]:
        pts=footprint(chair)
        assert min(p[0] for p in pts)>734
        overlap_x=min(max(p[0] for p in pts),max(p[0] for p in sofa_pts))-max(min(p[0] for p in pts),min(p[0] for p in sofa_pts))
        overlap_z=min(max(p[1] for p in pts),max(p[1] for p in sofa_pts))-max(min(p[1] for p in pts),min(p[1] for p in sofa_pts))
        assert overlap_x<=0 or overlap_z<=0,chair['name']
    pullout_conflicts=[]
    for seat in chairs:
        angle=seat['rotation']
        shifted=dict(seat,position=[seat['position'][0]+.4*math.sin(angle),seat['position'][1],seat['position'][2]+.4*math.cos(angle)])
        pts=footprint(shifted)
        overlap_x=min(max(p[0] for p in pts),798)-max(min(p[0] for p in pts),738)
        overlap_z=min(max(p[1] for p in pts),1017)-max(min(p[1] for p in pts),857)
        if overlap_x>0 and overlap_z>0: pullout_conflicts.append(seat['name'])
    # Requested two-per-side arrangement is retained; report, do not hide the
    # chair/sofa pull-out constraint by changing the requested layout.
    (ROOT/'clearance-notes.json').write_text(json.dumps({'chairPullout40cmConflicts':pullout_conflicts},ensure_ascii=False,indent=2)+'\n')
    doors=[e for e in model.ELEMENTS if e['category']=='door']
    assert len(doors)==4 and all('closed' in e for e in doors)
    expected={'Door_Entry':[(777,161),(883,161)],'Door_Bedroom':[(615,625),(615,710)],
              'Door_Study':[(622,733),(715,733)],'Door_Bathroom':[(862,384),(862,468)]}
    for e in doors:
        closed=e['closed'];angle=closed['rotation'];cx,cy,cz=closed['position'];w=e['size'][0]
        ends=sorted((round(143+100*(cx+s*w/2*math.cos(angle)),3),round(161+100*(cz-s*w/2*math.sin(angle)),3)) for s in (-1,1))
        key=next(k for k in expected if e['name'].startswith(k+'_'))
        assert ends==expected[key],(key,ends)
    (ROOT/'measurement-checks.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    return rows


def render_plans():
    source=Image.open(SOURCES[1]).convert('RGBA')
    overlay=Image.new('RGBA',source.size)
    draw=ImageDraw.Draw(overlay)
    svg=[]
    # Ignore lintels / sill tops to compare the actual floor-level openings.
    visible=[model.resolved(e) for e in model.ELEMENTS if e['category'] not in ('floor','window','finish_floor','finish_wall','ceiling') and
             not (e['category']=='wall' and e['position'][1]-e['size'][1]/2>.01)]
    for e in visible:
        pts=footprint(e)
        if e['category']=='wall': color=(23,110,235,190); cat='wall'
        elif e['category']=='door': color=(170,64,215,210); cat='door'
        else: color=(220,91,12,175); cat='furniture'
        draw.line(pts+[pts[0]], fill=color, width=2)
        svg.append(f'<polygon class="{cat}" points="'+ ' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)+'"><title>'+html.escape(e['name'])+'</title></polygon>')
    Image.alpha_composite(source,overlay).convert('RGB').save(ROOT/'plan-overlay.png')
    top=Image.new('RGB',(1200,1200),(249,248,245)); d=ImageDraw.Draw(top)
    ordered=sorted([model.resolved(e) for e in model.ELEMENTS],key=lambda e:e['position'][1]+e['size'][1]/2)
    for e in ordered:
        if e['category'] in ('window','ceiling'): continue
        if e['category']=='wall' and e['position'][1]-e['size'][1]/2>.01:continue
        rgb=tuple(round(v*255) for v in model.MATERIALS[e['material']]['color'][:3])
        d.polygon(footprint(e),fill=rgb,outline=(95,95,90))
    top.save(ROOT/'model-top.png')
    shell=(ROOT/'comparison-shell.html').read_text()
    for i,path in enumerate(SOURCES):
        shell=shell.replace(f'__SOURCE{i}__','data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode())
    shell=shell.replace('__POLYGONS__','\n'.join(svg))
    (ROOT/'comparison.html').write_text(shell)


def render_iso(closed=False,mode='furniture'):
    # Orthographic software projection of the very same geometry. No browser used.
    pixels=np.full((1100,1400,3),(246,245,240),dtype=np.uint8)
    depth_buffer=np.full((1100,1400),-np.inf)
    yaw=1.02; pitch=1.02
    eye=np.array([math.cos(pitch)*math.cos(yaw),math.sin(pitch),math.cos(pitch)*math.sin(yaw)])
    right=np.cross([0,1,0],eye);right=right/np.linalg.norm(right);up=np.cross(eye,right)
    faces=[]
    for original in model.ELEMENTS:
        if original['category']=='ceiling':continue
        if mode=='rough' and (original['category'].startswith('finish_') or original['category']=='furniture'):continue
        if mode=='rough' and original['category']=='door' and not original['name'].startswith('Door_Entry_'):continue
        if mode=='finished' and original['category']=='furniture':continue
        e=dict(original) if mode=='rough' else model.resolved(original)
        e['position']=list(e['position']);e['size']=list(e['size'])
        if closed and e['category']=='door':
            rise=0 if (mode!='rough' and original.get('finished',{}).get('closed')) else e['position'][1]-original['position'][1]
            e.update(e['closed']);e['position']=list(e['position']);e['position'][1]+=rise
        if e['category']=='window':continue
        if e['category'] in ('wall','door','finish_wall'):
            base=e['position'][1]-e['size'][1]/2
            h=min(e['size'][1],1.35-base)
            if h<=0:continue
            e['position'][1]=base+h/2;e['size'][1]=h
        geom={'box':model.cube_geometry,'cylinder':model.cylinder_geometry,'hexagon':model.hexagon_geometry}[e['shape']]
        positions,normals,indices=geom()
        pts=np.array(positions).reshape(-1,3)*e['size']
        a=e.get('rotation',0); rot=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])
        pts=pts@rot.T+e['position']
        for idx in np.array(indices).reshape(-1,3):
            p=pts[idx];normal=np.cross(p[1]-p[0],p[2]-p[0]);normal/=np.linalg.norm(normal)
            if np.dot(normal,eye)<=0:continue
            shade=.66+.34*max(0,np.dot(normal,np.array([-.48,.86,.34])/np.linalg.norm([-.48,.86,.34])))
            color=tuple(round(v*255*shade) for v in model.MATERIALS[e['material']]['color'][:3])
            q=p-[4.25,0,4.65]
            polygon=[(700+np.dot(v,right)*83,565-np.dot(v,up)*83) for v in q]
            faces.append((p@eye,polygon,color))
    for depths,polygon,color in faces:
        (x0,y0),(x1,y1),(x2,y2)=polygon
        lo_x=max(0,int(min(x0,x1,x2)));hi_x=min(1399,math.ceil(max(x0,x1,x2)))
        lo_y=max(0,int(min(y0,y1,y2)));hi_y=min(1099,math.ceil(max(y0,y1,y2)))
        if hi_x<lo_x or hi_y<lo_y:continue
        den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(den)<1e-9:continue
        yy,xx=np.mgrid[lo_y:hi_y+1,lo_x:hi_x+1]
        xx=xx+.5;yy=yy+.5
        a=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/den
        b=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/den
        c=1-a-b
        depth=a*depths[0]+b*depths[1]+c*depths[2]
        region=depth_buffer[lo_y:hi_y+1,lo_x:hi_x+1]
        mask=(a>=0)&(b>=0)&(c>=0)&(depth>region)
        region[mask]=depth[mask]
        pixels[lo_y:hi_y+1,lo_x:hi_x+1][mask]=color
    filename=('model-isometric-closed.png' if closed else 'model-isometric.png') if mode=='furniture' else 'model-'+mode+'.png'
    Image.fromarray(pixels).save(ROOT/filename)


if __name__=='__main__':
    model.build_scene()
    rows=checks()
    if getattr(model,'PDF_REFERENCE',False):
        from audit_designer import render
        render()
    else:
        render_plans();render_iso();render_iso(closed=True);render_iso(mode='rough');render_iso(mode='finished')
    print(f'{len(rows)} current-source dimension checks passed; GLB scene identity passed.')
