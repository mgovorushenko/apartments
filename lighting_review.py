"""Static source overlay of actual ceiling fixture centres, inverse-registered."""
from html import escape
from lighting_plan import inverse


def write(api,output):
    markers=[]
    for i,row in enumerate(r for r in api.LIGHTING_LAYOUT if r['kind'] in ('spot','central')):
        e=api.resolved(next(e for e in api.ELEMENTS if e['name']==row['elements'][0]))
        x,y=inverse(e['position'][0],e['position'][2])
        title=escape(f"{row['id']} · X {e['position'][0]:.3f} м · Z {e['position'][2]:.3f} м")
        markers.append(f'<g><title>{title}</title><circle cx="{x:.2f}" cy="{y:.2f}" r="12"/><path d="M {x-16:.2f},{y:.2f} h32 M {x:.2f},{y-16:.2f} v32"/></g>')
    page='''<!doctype html>
<html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Сверка освещения</title><style>
body{font:16px system-ui,sans-serif;margin:24px;background:#f4f1eb;color:#262724}main{max-width:1000px;margin:auto}
svg{display:block;width:100%;height:auto;background:white;margin-top:16px}.marks{fill:none;stroke:#087bf5;stroke-width:2}
#overlay:not(:checked)~svg .marks{display:none}a{color:inherit}label{display:inline-block;padding:10px}
</style><main><a href="index.html">← К 3D-модели</a><h1>Сверка потолочного освещения</h1>
<p>Синие перекрестия — центры светильников из модели, жёлтые обозначения — исходная схема.
40 отдельных спотов и один центральный светильник. Координаты перенесены по пропорциям между стенами; это не обмерный план электрики.</p>
<input id="overlay" type="checkbox" checked><label for="overlay">Показать точки модели</label>
<svg viewBox="0 0 1630 1536" role="img" aria-label="Исходная схема и центры светильников модели">
<image href="assets/lighting-plan.png" width="1630" height="1536" preserveAspectRatio="none"/>
<g class="marks">'''+''.join(markers)+'''</g></svg>
<p>Также перенесены четыре бра. Учтены подсветка зеркала прихожей, зеркала ванной и кухни.
Красные выводы питания отдельными светильниками не считаются. Высоты бра и размеры приборов предварительные.</p></main></html>'''
    (output/'lighting-comparison.html').write_text(page,encoding='utf-8')
