"""Current source audit. Old PNG checks belong to the superseded revision."""
from pathlib import Path
import json
import math
import struct
import base64
import generate_model as model

ROOT=Path(__file__).resolve().parent


def checks():
    by_id={o['id']:o for o in model.FURNITURE_CATALOG}
    rows=[]
    def check(label,expected,actual,origin='PDF, лист 8'):
        assert abs(expected-actual)<.001,(label,expected,actual)
        rows.append(dict(label=label,source=origin,expected_mm=expected,model_mm=round(actual,3)))
    for ident,axes in {
        'bed':{0:1870,1:2000},'bedside-left':{0:650},'bedside-right':{0:650},
        'bedroom-wardrobe':{0:1700,1:600},'hall-wardrobe':{0:1350,1:600},
        'entry-wardrobe':{0:1800},'entry-shoes':{0:750},'bath':{0:1800,1:750},
        'basin':{0:700},'table':{0:900,1:900},'kitchen-sofa':{0:1500},
        'study-sofa':{0:2000},'study-shelf':{0:700},'desk':{0:1400,1:600},
        'piano':{0:1400},'tv-console':{0:1500},'end-unit':{0:450,1:600},
        'sink-unit':{0:600,1:600},'dishwasher':{0:600,1:600},'oven':{0:600,1:600},
    }.items():
        for axis,expected in axes.items():check(by_id[ident]['label']+' '+('Ш','Г','В')[axis],expected,by_id[ident]['dimensionsMm'][axis])
    def node(prefix):return model.resolved(next(e for e in model.ELEMENTS if e['name'].startswith(prefix)))
    def edge(e,axis,sign):return e['position'][axis]+sign*e['size'][axis]/2
    check('Спальня: сумма поперечной цепочки',4675,1000*(edge(node('WallFinish_BedroomEastUpper'),0,-1)-edge(node('WallFinish_BedroomWestUpper'),0,1)))
    check('Спальня: 900 + 2000',2900,1000*(edge(node('WallFinish_BedroomSouth'),2,-1)-edge(node('WallFinish_BedroomNorth'),2,1)))
    check('Проход у изножья',900,1000*(edge(node('WallFinish_BedroomSouth'),2,-1)-edge(node('Bed_Frame_'),2,1)))
    check('Кухня: поперечная цепочка',3150,1000*(edge(node('FinishBeige_KitchenEast'),0,-1)-edge(node('FinishBeige_KitchenWest'),0,1)))
    check('Кухня: продольная цепочка',4580,1000*(edge(node('FinishBeige_KitchenSouthRight'),2,-1)-edge(node('FinishBeige_BathOuterSouth'),2,1)))
    check('Стол — стена',300,1000*(edge(node('Furniture_DiningTable_top'),0,-1)-edge(node('FinishBeige_KitchenWest'),0,1)),'Поздняя правка пользователя: стол к стене на 100 мм')
    check('Стол — кухонный фронт',1350,1000*(edge(node('OvenUnit_001'),0,-1)-edge(node('Furniture_DiningTable_top'),0,1)),'Поздняя правка пользователя: стол к стене на 100 мм')
    check('Стол — возврат кухни',950,1000*(edge(node('Furniture_DiningTable_top'),2,-1)-edge(node('FreezerBase_001'),2,1)))
    check('Диван кухни — окно',230,1000*(edge(node('FinishBeige_KitchenSouthRight'),2,-1)-edge(node('KitchenSofa_Base'),2,1)))
    check('Матрас',1800,node('Bed_Mattress_')['size'][0]*1000)
    for e in model.ELEMENTS:
        r=model.resolved(e)
        assert all(math.isfinite(v) and v>0 for v in r['size']),r['name']
        assert all(math.isfinite(v) for v in r['position'])
        if r.get('inspectId'):assert r['inspectId'] in by_id
        if r['category']=='furniture':assert edge(r,1,1)<=2.8+1e-6,r['name']
    # Export uses the same final geometry as the viewer (including selected groups).
    raw=(ROOT/'apartment-model.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+n]);assert len(doc['nodes'])==len(model.ELEMENTS)+1
    for actual,e in zip(doc['nodes'][1:],model.ELEMENTS):
        r=model.resolved(e);assert actual['translation']==r['position'] and actual['scale']==r['size']
    (ROOT/'measurement-checks.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'designer-changes.json').write_text(json.dumps(model.DESIGNER_CHANGES,ensure_ascii=False,indent=2)+'\n')
    return rows


def render():
    import audit_measured as visual
    visual.render_iso();visual.render_iso(closed=True);visual.render_iso(mode='rough');visual.render_iso(mode='finished')
    # Plain plan image, no misleading overlay on superseded PNGs.
    from PIL import Image,ImageDraw
    img=Image.new('RGB',(1200,1200),(249,248,245));draw=ImageDraw.Draw(img)
    scene=sorted([model.resolved(e) for e in model.ELEMENTS],key=lambda e:e['position'][1]+e['size'][1]/2)
    for e in scene:
        if e['category'] in ('window','ceiling'):continue
        if e['category'] in ('wall','finish_wall') and e['position'][1]-e['size'][1]/2>1.35:continue
        rgb=tuple(round(c*255) for c in model.MATERIALS[e['material']]['color'][:3])
        draw.polygon(visual.footprint(e),fill=rgb,outline=None if e.get('noEdges') else (95,95,90))
    img.save(ROOT/'model-top.png')
    shell=(ROOT/'designer-comparison-shell.html').read_text()
    for marker,p in [('PDF',ROOT/'assets/designer-dimensions.png'),('MODEL',ROOT/'model-top.png')]:
        shell=shell.replace('__'+marker+'__','data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode())
    (ROOT/'comparison.html').write_text(shell)


if __name__=='__main__':
    model.build_scene();rows=checks();render()
    print(f'{len(rows)} designer dimensions/chains passed; finite geometry and GLB identity passed.')
