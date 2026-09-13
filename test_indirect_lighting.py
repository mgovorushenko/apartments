"""Structural occlusion and material-dependent reflected-light receivers."""
import numpy as np
import generate_model as m
from indirect_lighting import patches,visibility

m.build_scene()
blockers=[]
for raw in m.ELEMENTS:
    e=m.resolved(raw)
    if e['category'] not in ('wall','door'):continue
    if e['category']=='door':e={**e,**e['closed']}
    blockers.append(e)
p,n,area,rho,kinds,_=patches(m,blockers)
assert len(p)>300 and all(kind in kinds for kind in ('floor','wall','ceiling'))
assert np.all(area>0) and np.all((rho>=.12)&(rho<=.88))
assert np.allclose(np.linalg.norm(n,axis=1),1)
assert np.ptp(rho)>.15,'floor and wall reflectance must influence transport'
assert np.all(n[np.array(kinds)=='ceiling']==[0,-1,0])
wall=dict(position=[0,1,0],size=[.1,2,3])
start=np.array([[-1,1,0],[-1,1,2]])
end=np.array([[1,1,0],[1,1,2]])
assert visibility(start,end,[wall]).tolist()==[False,True]
print('Passed: floor/wall/ceiling patches, varied material reflectance, normalized receivers and no transport through solid walls.')
