// Cross-language parity of live meshes and exported / CPU-rendered geometry.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict'),cp=require('node:child_process');
const python=process.env.APARTMENT_PYTHON || '/Users/mgovorusenko/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const fixture=JSON.parse(cp.execFileSync(python,['-c',`import generate_model as m,json
from detail_geometry import mesh
m.build_scene()
seen=set();items=[]
for raw in m.ELEMENTS:
 e=m.resolved(raw)
 if not e.get('detail'):continue
 kind=e['detail']['type']
 if kind in seen:continue
 seen.add(kind);items.append(dict(element=e,mesh=mesh(e)))
for raw in m.ELEMENTS:
 if raw.get('towelPress'):
  e=m.resolved(raw);e={**e,'detail':{**e['detail'],'press':e['towelPress']}}
  items.append(dict(element=e,mesh=mesh(e)))
print(json.dumps(items))`],{cwd:__dirname,maxBuffer:8*1024*1024}));
const win={},context=vm.createContext({window:win,console});
vm.runInContext(fs.readFileSync(path.join(__dirname,'viewer-core.js'),'utf8').replace('global.ApartmentViewer = { mount, pickObject, adjustedElement };','global.ApartmentViewer = { mount, pickObject, adjustedElement, detailMesh };'),context);
for(const row of fixture){
  const e=row.element,actual=win.ApartmentViewer.detailMesh(e),[p,n,indices]=row.mesh;
  assert.equal(actual.points.length*3,p.length);
  assert.deepEqual([...actual.indices],indices,e.detail.type+' triangle winding');
  actual.points.forEach((point,j)=>point.forEach((v,i)=>assert(Math.abs(v/e.size[i]-p[j*3+i])<1e-8,e.detail.type+' position')));
  actual.normals.forEach((normal,j)=>{
    const scaled=normal.map((v,i)=>v*e.size[i]),length=Math.hypot(...scaled);
    scaled.forEach((v,i)=>assert(Math.abs(v/length-n[j*3+i])<1e-8,e.detail.type+' normal'));
  });
  assert.equal(win.ApartmentViewer.detailMesh(e),actual,'mesh must be cached');
}
console.log('Passed: live/export mesh positions, normals and winding match for all eight profiles; cached meshes reused.');
