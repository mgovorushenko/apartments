// Geometry/UV/selection regression; no browser or real GPU is simulated here.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const win={},ctx=vm.createContext({window:win,console});
vm.runInContext(fs.readFileSync('scene-data.js','utf8'),ctx);
const code=fs.readFileSync('viewer-core.js','utf8');
vm.runInContext(code.replace('global.ApartmentViewer = { mount, pickObject, adjustedElement };',
  'global.ApartmentViewer = { mount, pickObject, adjustedElement, buildGeometry };'),ctx);
const model=win.APARTMENT_SCENE,source=model.elements.filter(e=>e.artwork||e.name.startsWith('Furniture_DiningChair1_'));
const small={...model,elements:source},state={mode:'furniture',furniture:true,cutWalls:false,doorsClosed:false};
const plain=win.ApartmentViewer.buildGeometry(small,state,[0,0,0,1]);
const selected=win.ApartmentViewer.buildGeometry(small,{...state,selected:'chair-1'},[0,0,0,1]);
assert(selected.opaque.positions.length>plain.opaque.positions.length,'visible 3D corner brackets');
const tags=[];
for(let i=0;i<plain.opaque.surfaces.length;i+=4){
 const [tag,u,v]=plain.opaque.surfaces.slice(i,i+4);tags.push(tag);
 if(tag===7)assert(u>=-1e-9&&u<=1+1e-9&&v>=-1e-9&&v<=1+1e-9,'photo UVs stay inside the source image');
}
assert(tags.includes(7)&&tags.includes(9),'real photo material and context ground');
assert(selected.opaque.surfaces.some((v,i)=>i%4===0&&v===10),'selection is independent of lighting');
assert(code.includes('uniform sampler2D uArtwork')&&code.includes('texture(uArtwork,vSurface.yz)'));
assert(code.includes('receiver.y=min(receiver.y,2.57)'));
assert(code.includes('mod(floor(brick.y),2.0)*.5'),'running bond brick');
console.log('Passed: photo UVs, ground plane, lit-independent selection corners, brick shader and ceiling sample boundary.');
