"""A closed cabinet, exact hinged transforms, and mesh-based first-contact limits."""
import math
import numpy as np
import generate_model as m
from cabinet_motion import triangles,intersects
m.build_scene()
items=[m.resolved(e) for e in m.ELEMENTS]
metal=triangles(m,[e for e in items if e['name'].startswith('BathTowelWarmer')])
cloth=triangles(m,[e for e in items if e['name'].startswith('BathTowelDrape')])
obstacles=np.concatenate([metal,cloth])
for group in m.CABINET_MOTION['groups']:
 angle=group['limitDegrees'];pivot=group['pivot'];bounds=group['bounds']
 assert not intersects(obstacles,pivot,bounds,0)
 for a in np.linspace(0,angle,80):assert not intersects(metal,pivot,bounds,a),(group['group'],a)
 if angle<90:assert intersects(metal,pivot,bounds,angle+.02)
 assert not intersects(metal,pivot,bounds,group['bareDegrees'])
 if group['bareDegrees']<90:assert intersects(metal,pivot,bounds,group['bareDegrees']+.02)
 if group['group']=='main':assert 50<angle<75 and angle==group['bareDegrees'] and group['fabricContactDegrees']<angle
 else:assert angle==90
parts=[e for e in items if e['name'].startswith('BathTallCabinet') and ('Facade' in e['name'] or '_Handle_' in e['name'])]
assert len(parts)==12
assert all(e.get('cabinetMotion') for e in parts)
assert all(e.get('rotation',0)==0 for e in parts),'exports start closed'
for e in parts:
 assert math.degrees(e['cabinetMotion']['angle'])<=90
assert len([e for e in parts if e['name'].startswith('BathTallCabinetFacadePanel')])==2
pressed=[{**e,'detail':{**e['detail'],'press':e['towelPress']}} for e in items if e.get('towelPress')]
pressed_triangles=triangles(m,pressed)
assert np.isfinite(pressed_triangles).all()
assert pressed_triangles[:,:,0].min()>7.275,'cloth stays outside tiled wall'
for group in m.CABINET_MOTION['groups']:
 assert not intersects(pressed_triangles,group['pivot'],group['bounds'],group['limitDegrees']),'displaced cloth clears open façade'
assert not np.allclose(pressed_triangles,cloth),'cloth visibly moves'
print('Passed: rigid-warmer stop, safe sweep, first contact, displaced cloth clearance and closed two-door cabinet:',m.CABINET_MOTION['groups'])
