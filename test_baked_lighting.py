import json
import base64
from pathlib import Path
import numpy as np
from bake_lighting import sample,SIZE

data=json.loads(Path(__file__).with_name('lighting-bake.json').read_text())
for variant in data['variants'].values():
    for value in variant.values():assert len(base64.b64decode(value))==int(np.prod(SIZE))*3
points=np.array([[7.3,.04,6.3],[3.6,.04,7.2],[2.3,.04,4.1],[8.3,.04,2.8],[6.5,.04,.5]])
normals=np.tile([0,1,0],(len(points),1))
upper=sample(data,points,normals,upper=True,small=False)
small=sample(data,points,normals,upper=False,small=True)
assert np.all(upper>.10),upper
assert np.all(upper>small), (upper,small)
assert np.allclose(sample(data,points,normals),upper+small)
assert np.all(sample(data,points,normals,upper=False,small=False)==0)
assert data['variants']['open']!=data['variants']['closed']
print('Passed: upper light reaches floors in every principal room; independently additive circuits, dark state, distinct door variants. Upper irradiance:',upper.round(3))
