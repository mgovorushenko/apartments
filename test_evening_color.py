"""Display palette -> linear lighting -> display, without lifted black levels."""
from pathlib import Path
import numpy as np
from render_kitchen_check import srgb_to_linear,evening_display

black=np.array([.15,.16,.16]);white=np.array([.96,.96,.94]);oak=np.array([.76,.63,.46])
lit=lambda color,energy:evening_display(srgb_to_linear(color)*energy)
old=lambda color,energy:(color*energy/(1+color*energy))**(1/2.2)
assert np.max(lit(black,.75))<.15
assert np.all(lit(white,.75)<old(white,1))
assert np.all(lit(white,.75)>.60)
assert np.min(lit(white,.25))>.40 # softly lit ceiling remains visible
assert np.max(lit(white,.004))<.06 # lights-off keeps darkness
assert np.ptp(lit(oak,.75))>np.ptp(old(oak,1))
assert np.mean(lit(white,.75))/np.mean(lit(black,.75))>4
levels=np.linspace(0,8,257)
out=evening_display(levels[:,None]*srgb_to_linear(white))
assert np.all(np.isfinite(out)) and np.all(np.diff(out,axis=0)>=0)
assert np.max(out)<1
shader=Path(__file__).with_name('viewer-core.js').read_text()
for code in ('srgbToLinear(base)','rgb=eveningDisplay(rgb)','mix(1.0,.75,uEvening)','1.0+dot(c,vec3(.2126,.7152,.0722))'):
    assert code in shader
assert 'if(uSmallLight>.5)energy+=bakedLight(uSmallPositive,uSmallNegative,uv,n);' in shader
print('Passed: black level, highlight reduction, wood chroma, ceiling visibility, darkness and monotonic tone response.')
