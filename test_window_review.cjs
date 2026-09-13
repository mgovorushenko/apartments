// Static shader contract; actual GPU transparency is a separate visual check.
const fs=require('node:fs'),assert=require('node:assert/strict');
const code=fs.readFileSync('viewer-core.js','utf8');
assert(code.includes('alpha=mix(alpha,.12,uEvening)'));
assert(!code.includes('alpha=mix(alpha,1.0,uEvening)'));
assert(code.includes('gl.depthMask(false)'));
assert(code.includes('gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)'));
assert(code.includes("`${item.label} · Ш × Г × В: ${item.dimensionsMm.join(' × ')} мм`"));
assert(!code.includes('модель Ш × Г × В:'));
assert(code.includes('vSurface.x>9.5&&vSurface.x<10.5'));
assert(code.includes('vSurface.x>11.5&&vSurface.x<12.5'));
console.log('Passed: evening glass transmits, compact furniture info, rug pattern remains lit.');
