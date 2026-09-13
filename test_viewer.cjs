// Unit tests only: WebGL calls and DOM are mocked, no browser is launched.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const dataCode=fs.readFileSync(path.join(__dirname,'scene-data.js'),'utf8');
const code=fs.readFileSync(path.join(__dirname,'viewer-core.js'),'utf8');
function test(width,dark){
  const callbacks=[],nodes={},draws=[],matrices=[],uploads=[],uniforms={},shaders=[];
  let lightArrayUploads=0,textureUploads=0,volumeUploads=0;
  function element(){return {style:{},dataset:{},listeners:{},textContent:'',attrs:{},
    addEventListener(n,f){this.listeners[n]=f},setAttribute(n,v){this.attrs[n]=v},
    appendChild(){},remove(){},focus(){},setPointerCapture(){},getBoundingClientRect(){return {left:0,top:0,width,height:Math.min(600,Math.max(320,width*.68))}}};}
  for(const s of ['.apt-stage','.apt-buildup','canvas','[aria-live]','.apt-error','[data-action="walls"]','[data-action="rough"]','[data-action="finished"]','[data-action="furniture"]','[data-action="reset"]','[data-action="top"]','[data-action="doors"]'])nodes[s]=element();
  for(const s of ['.apt-layer-values','.apt-inspection','[data-action="object"]'])nodes[s]=element();
  nodes['[data-action="kitchen"]']=element();
  nodes['[data-action="bathroom"]']=element();nodes['[data-action="evening"]']=element();
  for(const s of ['[data-action="upper-light"]','[data-action="small-light"]','.apt-light-controls'])nodes[s]=element();
  nodes['[data-action="cabinet"]']=element();
  nodes['[data-action="towels"]']=element();nodes['[data-action="towels-label"]']=element();
  const root=element();root.querySelector=s=>{assert(nodes[s],s);return nodes[s]};
  root.contains=target=>target===root || Object.values(nodes).includes(target);
  const gl=new Proxy({
    getShaderParameter:()=>true,getProgramParameter:()=>true,
    texImage2D:(_t,_l,_f,w,h,_b,_format,_type,pixels)=>{textureUploads++;assert.equal(pixels.length,w*h*(_format==='RGB'?3:1))},
    texImage3D:(_t,_l,_f,w,h,d,_b,_format,_type,pixels)=>{assert.equal(pixels.length,w*h*d*3);if(w>1)volumeUploads++},
    shaderSource:(_,s)=>shaders.push(s),getUniformLocation:(_,s)=>s,
    uniform1f:(key,v)=>uniforms[key]=v,uniform1i:(key,v)=>uniforms[key]=v,
    uniform3fv:(key,v)=>{assert([...v].every(Number.isFinite));uniforms[key]=[...v];if(key.includes('[0]'))lightArrayUploads++},
    uniform4fv:(key,v)=>{assert([...v].every(Number.isFinite));uniforms[key]=[...v];if(key.includes('[0]'))lightArrayUploads++},
    bufferData:(_,data)=>{assert([...data].every(Number.isFinite));uploads.push(data)},
    uniformMatrix4fv:(_,transpose,data)=>{assert.equal(transpose,false);assert([...data].every(Number.isFinite));matrices.push([...data])},
    drawArrays:(mode,start,count)=>{assert(count>0);draws.push(count)},
  },{get(t,k){if(k in t)return t[k]; if(k.toUpperCase()===k)return k; return ()=>({});}});
  nodes.canvas.getContext=type=>{assert.equal(type,'webgl2');return gl};
  nodes.canvas.clientWidth=width;nodes.canvas.clientHeight=nodes['.apt-stage'].getBoundingClientRect().height;
  const win={listeners:{},addEventListener(n,f){this.listeners[n]=f},devicePixelRatio:1,requestAnimationFrame:fn=>callbacks.push(fn),matchMedia:()=>({addEventListener(){}})};
  const document={listeners:{},addEventListener(n,f){this.listeners[n]=f},hidden:false,getElementById:id=>{assert.equal(id,'apartment-3d-root');return root},createElement:element,documentElement:element(),body:{}};
  const context=vm.createContext({window:win,document,console,Float32Array,Uint8Array,atob,ResizeObserver:class{observe(){}},MutationObserver:class{observe(){}},
    getComputedStyle:()=>({color:dark?'rgb(230,230,230)':'rgb(30,30,30)'})});
  vm.runInContext(dataCode,context);
  vm.runInContext(code.replace('global.ApartmentViewer = { mount, pickObject, adjustedElement };','global.ApartmentViewer = { mount, pickObject, adjustedElement, addCylinder };'),context);
  // Oval pet-bed primitives must use their depth and yaw in rendered vertices.
  const oval={position:[0,0,0],size:[2,.2,.6],rotation:Math.PI/2,noEdges:true};
  const triangles={positions:[],normals:[],colors:[]},lines={positions:[],normals:[],colors:[]};
  win.ApartmentViewer.addCylinder(triangles,lines,oval,[1,1,1,1],[0,0,0,1]);
  assert(Math.abs(Math.max(...triangles.positions.filter((_,i)=>i%3===0))-.3)<1e-8);
  assert(Math.abs(Math.max(...triangles.positions.filter((_,i)=>i%3===2))-1)<1e-8);
  assert.equal(lines.positions.length,0);
  win.ApartmentViewer.mount('apartment-3d-root',win.APARTMENT_SCENE);
  function flush(){let n=0;while(callbacks.length){assert(++n<10);callbacks.shift()()}assert.equal(nodes['.apt-error'].textContent,'');}
  const click=action=>{nodes[`[data-action="${action}"]`].listeners.click();flush()};
  flush();assert(draws.length>0);assert.equal(nodes.canvas.width,width);
  assert.equal(textureUploads,2,'contact and photographic art textures each upload once');
  const immutableScene=JSON.stringify(win.APARTMENT_SCENE);
  // Solve the three clip planes x=y=w=0 to recover the perspective camera eye.
  function eyeFromMatrix(m){
    const rows=[0,1,3].map(r=>[m[r],m[4+r],m[8+r],-m[12+r]]);
    for(let c=0;c<3;c++){
      const pivot=rows.slice(c).reduce((best,row,j)=>Math.abs(row[c])>Math.abs(rows[best][c])?j+c:best,c);
      [rows[c],rows[pivot]]=[rows[pivot],rows[c]];
      const div=rows[c][c];for(let j=c;j<4;j++)rows[c][j]/=div;
      for(let r=0;r<3;r++)if(r!==c){const scale=rows[r][c];for(let j=c;j<4;j++)rows[r][j]-=scale*rows[c][j];}
    }
    return rows.map(r=>r[3]);
  }
  const initial=matrices.at(-1);assert(uploads.length>=12);
  const openPositions=uploads[0];
  click('doors');assert.equal(nodes['[data-action="doors"]'].textContent,'Открыть двери');
  assert.equal(nodes['[data-action="doors"]'].attrs['aria-pressed'],'true');
  assert.notDeepEqual(uploads[12],openPositions);
  for(const e of win.APARTMENT_SCENE.elements.filter(e=>e.category==='door')) {
    const full=win.ApartmentViewer.adjustedElement(e,{doorsClosed:true,cutWalls:false,furniture:true});
    assert.deepEqual([...full.position],[...e.finished.closed.position]);assert.equal(full.rotation,e.closed.rotation);
    const cut=win.ApartmentViewer.adjustedElement(e,{doorsClosed:true,cutWalls:true,cutHeight:1.35,furniture:true});
    assert(Math.abs(cut.size[1]-(1.35-win.APARTMENT_SCENE.metadata.finishes.dry_floor-.005))<1e-8);assert.equal(cut.rotation,e.closed.rotation);
    assert.equal(cut.position[0],e.finished.closed.position[0]);assert.equal(cut.position[2],e.finished.closed.position[2]);
  }
  click('doors');assert.equal(nodes['[data-action="doors"]'].textContent,'Закрыть двери');
  assert.deepEqual(uploads[24],openPositions);
  click('top');assert.equal(nodes['[data-action="top"]'].attrs['aria-pressed'],'true');
  const top=matrices.at(-1);
  function project(x,y,z){return [top[0]*x+top[4]*y+top[8]*z+top[12],top[1]*x+top[5]*y+top[9]*z+top[13]];}
  assert(project(2,0,2)[0]>project(1,0,2)[0]);
  assert(project(2,0,3)[1]<project(2,0,2)[1]);
  for(const x of [-.99,9.33])for(const z of [-.21,9.58])assert(project(x,0,z).every(v=>Math.abs(v)<1),'top view must fit');
  click('rough');assert.equal(nodes['[data-action="rough"]'].attrs['aria-pressed'],'true');
  const rawUploads=uploads.at(-12);
  click('finished');assert.equal(nodes['[data-action="finished"]'].attrs['aria-pressed'],'true');
  assert.equal(nodes['[data-action="furniture"]'].attrs['aria-pressed'],'false');
  assert.notDeepEqual(uploads.at(-12),rawUploads,'finished geometry differs from raw shell');
  for (const mode of ['rough','finished','furniture']) {
    const visible=win.APARTMENT_SCENE.elements.map(e=>win.ApartmentViewer.adjustedElement(e,{mode,furniture:mode==='furniture',cutWalls:false})).filter(Boolean);
    assert.equal(visible.some(e=>e.category==='furniture'),mode==='furniture');
    assert.equal(visible.some(e=>e.category.startsWith('finish_')),mode!=='rough');
    assert(visible.filter(e=>e.category==='ceiling').every(e=>e.rawOnly===(mode==='rough')));
    assert(visible.filter(e=>e.category==='ceiling').length>0);
    if(mode==='rough') assert(visible.filter(e=>e.category==='door').every(e=>e.name.startsWith('Door_Entry_')));
    const cut=win.APARTMENT_SCENE.elements.map(e=>win.ApartmentViewer.adjustedElement(e,{mode,furniture:mode==='furniture',cutWalls:true,cutHeight:1.35})).filter(Boolean);
    assert(!cut.some(e=>e.category==='ceiling'));
  }
  click('furniture');click('walls');assert.equal(nodes['[data-action="walls"]'].attrs['aria-pressed'],'true');click('walls');
  click('reset');assert.deepEqual(matrices.at(-1),initial);
  const event={pointerId:1,clientX:100,clientY:100,button:0,preventDefault(){}};
  const fixedEye=eyeFromMatrix(initial),fixedUploads=uploads.length;
  nodes.canvas.listeners.pointerdown(event);nodes.canvas.listeners.pointermove({...event,clientX:140,clientY:110});flush();
  eyeFromMatrix(matrices.at(-1)).forEach((v,i)=>assert(Math.abs(v-fixedEye[i])<1e-4,'mouse changes gaze around a fixed camera eye'));
  assert.equal(uploads.length,fixedUploads,'camera movement must not rebuild apartment geometry');
  assert.notDeepEqual(matrices.at(-1),initial);nodes.canvas.listeners.pointerup(event);
  nodes.canvas.listeners.wheel({deltaY:-100,preventDefault(){}});flush();
  assert(Math.hypot(...eyeFromMatrix(matrices.at(-1)).map((v,i)=>v-fixedEye[i]))>1,'wheel must move camera');
  const before=matrices.at(-1);click('top');
  nodes.canvas.listeners.pointerdown(event);nodes.canvas.listeners.pointermove({...event,clientX:110,clientY:110});flush();nodes.canvas.listeners.pointerup(event);
  assert.notDeepEqual(matrices.at(-1),before);
  // Keyboard tests use explicit RAF ticks so held keys can animate continuously.
  click('reset');
  const key=(code,extra={})=>document.listeners.keydown({code,key:'ц',target:document.body,preventDefault(){},...extra});
  const release=code=>document.listeners.keyup({code});
  const tick=t=>{assert(callbacks.length>0);callbacks.shift()(t)};
  const stationary=matrices.at(-1);
  key('KeyW');tick(1000);tick(1016);assert.notDeepEqual(matrices.at(-1),stationary);
  // Continue holding W while starting, moving and ending a mouse drag.
  const moving=matrices.at(-1);
  nodes.canvas.listeners.pointerdown(event);
  document.listeners.focusin({target:document.body});
  nodes.canvas.listeners.pointermove({...event,clientX:160,clientY:115});tick(1032);
  const turning=matrices.at(-1);
  assert.notEqual(turning[0],moving[0],'mouse must rotate while W is held');
  nodes.canvas.listeners.pointerup(event);tick(1048);
  assert.equal(matrices.at(-1)[0],turning[0],'orientation stays after mouse release');
  assert.notDeepEqual(matrices.at(-1),turning,'W continues after mouse release');
  release('KeyW');flush();assert.equal(callbacks.length,0);
  for(const code of ['KeyA','KeyS','KeyD']) {
    const prior=matrices.at(-1);key(code);tick(1100);release(code);flush();assert.notDeepEqual(matrices.at(-1),prior);
  }
  // Arrows move along world-up and turn about the camera's own position.
  click('reset');
  const arrowUploads=uploads.length;
  const close=(a,b)=>assert(Math.abs(a-b)<1e-4,`${a} != ${b}`);
  const yaw=m=>Math.atan2(-m[11],-m[3]);
  for(const [code,sign] of [['Space',1],['ShiftLeft',-1],['ShiftRight',-1]]) {
    const prior=matrices.at(-1),eye=eyeFromMatrix(prior);
    let prevented=false;key(code,{preventDefault(){prevented=true}});assert(prevented,'arrow must suppress page scroll');
    tick(2000);tick(2050);release(code);flush();
    const after=eyeFromMatrix(matrices.at(-1));
    close(after[0],eye[0]);close(after[2],eye[2]);
    close(after[1]-eye[1],sign*2.5*(1/60+.05));
    for(const i of [0,1,2,3,4,5,6,7,8,9,10,11])close(matrices.at(-1)[i],prior[i]);
  }
  for(const code of ['ArrowUp','ArrowDown']){
    const prior=matrices.at(-1),eye=eyeFromMatrix(prior);
    key(code);tick(2060);release(code);flush();
    eyeFromMatrix(matrices.at(-1)).forEach((v,i)=>close(v,eye[i]));
    assert.notDeepEqual(matrices.at(-1),prior,'vertical arrows change gaze only');
  }
  for(const [code,sign] of [['ArrowLeft',-1],['ArrowRight',1]]) {
    const prior=matrices.at(-1),eye=eyeFromMatrix(prior);
    key(code);tick(2100);tick(2150);release(code);flush();
    eyeFromMatrix(matrices.at(-1)).forEach((v,i)=>close(v,eye[i]));
    close(yaw(matrices.at(-1))-yaw(prior),sign*1.2*(1/60+.05));
  }
  const cancelled=matrices.at(-1);
  for(const code of ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'])key(code);
  tick(2200);tick(2250);
  for(const code of ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'])release(code);
  flush();assert.deepEqual(matrices.at(-1),cancelled,'opposite arrows cancel');
  const concurrent=eyeFromMatrix(matrices.at(-1)),priorYaw=yaw(matrices.at(-1));
  key('KeyW');key('Space');key('ArrowRight');
  nodes.canvas.listeners.pointerdown(event);
  nodes.canvas.listeners.pointermove({...event,clientX:120,clientY:100});tick(2300);
  nodes.canvas.listeners.pointerup(event);tick(2350);
  const afterConcurrent=eyeFromMatrix(matrices.at(-1));
  assert(afterConcurrent[1]>concurrent[1]);
  assert(Math.hypot(afterConcurrent[0]-concurrent[0],afterConcurrent[2]-concurrent[2])>.05);
  assert(yaw(matrices.at(-1))>priorYaw+.16,'mouse and arrow rotations accumulate');
  for(const code of ['KeyW','Space','ArrowRight'])release(code);
  flush();assert.equal(callbacks.length,0);
  assert.equal(uploads.length,arrowUploads,'arrows must not change apartment geometry');
  key('ArrowUp');tick(2400);win.listeners.blur();flush();assert.equal(callbacks.length,0);
  click('top');key('ArrowRight');tick(2500);release('ArrowRight');flush();
  assert.equal(nodes['[data-action="top"]'].attrs['aria-pressed'],'false','arrows restore saved 3D camera from plan');
  for(const extra of [{ctrlKey:true},{metaKey:true},{altKey:true},{isComposing:true},{target:{closest:()=>true}},{target:{}}]) {
    for(const code of ['KeyW','ArrowUp','ArrowDown','ArrowLeft','ArrowRight']) {
      key(code,extra);assert.equal(callbacks.length,0,'typing/shortcuts must not move camera');
    }
  }
  key('KeyW');tick(1200);win.listeners.blur();flush();assert.equal(callbacks.length,0);
  key('KeyD');tick(1300);document.hidden=true;document.listeners.visibilitychange();flush();
  key('KeyW');assert.equal(callbacks.length,0);document.hidden=false;
  key('KeyW');tick(1400);document.listeners.focusin({target:{closest:()=>true}});flush();assert.equal(callbacks.length,0);
  key('KeyW');tick(1500);document.listeners.pointerdown({target:{}});flush();assert.equal(callbacks.length,0);
  key('KeyW');tick(1600);key('Escape');flush();assert.equal(callbacks.length,0);
  click('top');const topBefore=matrices.at(-1);
  key('KeyW');tick(1700);release('KeyW');flush();
  assert(matrices.at(-1)[13]<topBefore[13],'W in top view moves toward plan north');
  const beforeD=matrices.at(-1);key('KeyD');tick(1800);release('KeyD');flush();
  assert(matrices.at(-1)[12]<beforeD[12],'D in top view moves east');
  key('Escape');flush();
  // Pick a complete table through a rendered top-view camera ray.
  click('reset');click('top');
  const table=win.APARTMENT_SCENE.elements.find(e=>e.name.startsWith('Furniture_DiningTable_top_'));
  // The fruit bowl now occupies the centre: click a clear part of the tabletop.
  const p=[table.position[0]+.25,table.position[1],table.position[2]],matrix=matrices.at(-1);
  const clip=[0,1,2,3].map(r=>matrix[r]*p[0]+matrix[4+r]*p[1]+matrix[8+r]*p[2]+matrix[12+r]);
  const nx=clip[0]/clip[3],ny=clip[1]/clip[3];
  assert.equal(win.ApartmentViewer.pickObject(win.APARTMENT_SCENE,{mode:'furniture',furniture:true,cutWalls:true,cutHeight:1.35},matrix,nx,ny),'table');
  const rect=nodes.canvas.getBoundingClientRect();
  const press={pointerId:88,clientX:(nx+1)*rect.width/2,clientY:(1-ny)*rect.height/2,button:0};
  nodes.canvas.listeners.pointerdown(press);nodes.canvas.listeners.pointerup(press);flush();
  assert.equal(nodes['[data-action="object"]'].value,'table');
  assert(nodes['.apt-inspection'].textContent.includes('900 × 900'));
  nodes['[data-action="object"]'].value='bed';nodes['[data-action="object"]'].listeners.change();flush();
  assert(nodes['.apt-inspection'].textContent.includes('1870 × 2000'));
  click('finished');assert.equal(nodes['[data-action="object"]'].value,'');
  assert.equal(nodes['[data-action="object"]'].disabled,true);
  click('furniture');assert.equal(nodes['[data-action="object"]'].disabled,false);
  const toy={materials:{m:{color:[1,1,1,1]}},elements:[
    {shape:'box',category:'wall',material:'m',position:[0,0,0],size:[1,1,.1]},
    {shape:'box',category:'furniture',material:'m',inspectId:'behind',position:[0,0,.5],size:[.5,.5,.1]}
  ]};
  const identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
  assert.equal(win.ApartmentViewer.pickObject(toy,{mode:'furniture',furniture:true},identity,0,0),null,'wall occludes furniture');
  toy.elements.shift();assert.equal(win.ApartmentViewer.pickObject(toy,{mode:'furniture',furniture:true},identity,0,0),'behind');
  assert.equal(win.ApartmentViewer.pickObject(toy,{mode:'finished'},identity,0,0),null);
  click('kitchen');
  const kitchenEye=eyeFromMatrix(matrices.at(-1));
  kitchenEye.forEach((v,i)=>assert(Math.abs(v-[6.45,1.50,8.50][i])<1e-4));
  assert.equal(nodes['[data-action="walls"]'].attrs['aria-pressed'],'true');
  assert.equal(nodes['[data-action="doors"]'].attrs['aria-pressed'],'true');
  assert.equal(nodes['[data-action="furniture"]'].attrs['aria-pressed'],'true');
  const dayMatrix=matrices.at(-1),dayUploads=uploads.length;
  assert.equal(uniforms.uEvening,0);
  assert.equal(uniforms.uDetailAmbient,1);
  assert.equal(uniforms.uInteriorLight,0);assert.equal(uniforms.uUpperLight,0);assert.equal(uniforms.uSmallLight,0);
  assert.equal(volumeUploads,0,'day never loads full lighting volumes');
  assert.equal(lightArrayUploads,0,'day mode never builds/uploads local-light or shadow arrays');
  click('evening');assert.equal(uniforms.uEvening,1);
  assert.equal(nodes['[data-action="evening"]'].attrs['aria-pressed'],'true');
  assert.deepEqual(matrices.at(-1),dayMatrix,'evening preserves camera');
  assert.equal(uploads.length,dayUploads,'evening changes lighting, not apartment meshes');
  assert.equal(volumeUploads,8,'two circuits, two directions, two door states, uploaded once');
  assert.equal(uniforms.uUpperLight,1);assert.equal(uniforms.uSmallLight,1);
  const stableUploads=uploads.length;
  click('upper-light');assert.equal(uniforms.uUpperLight,0);assert.equal(uniforms.uSmallLight,1);
  click('small-light');assert.equal(uniforms.uUpperLight,0);assert.equal(uniforms.uSmallLight,0);
  click('upper-light');assert.equal(uniforms.uUpperLight,1);assert.equal(uniforms.uSmallLight,0);
  click('small-light');assert.equal(uniforms.uSmallLight,1);
  assert.equal(uploads.length,stableUploads,'light circuits never rebuild geometry');
  assert(!shaders.some(s=>s.includes('bool blocked')||s.includes('uLights[')),'no per-pixel ray tracing');
  assert(shaders.some(s=>s.includes('bakedLight')&&s.includes('sampler3D')));
  click('bathroom');eyeFromMatrix(matrices.at(-1)).forEach((v,i)=>assert(Math.abs(v-[8.80,1.50,2.80][i])<1e-4));
  assert.equal(uniforms.uEvening,1,'bathroom preset preserves evening');
  const eveningUploads=lightArrayUploads;
  click('reset');assert.equal(lightArrayUploads,eveningUploads,'camera-only changes reuse light uniforms');
  click('doors');assert.equal(volumeUploads,8,'door change reuses precomputed textures');
  click('rough');assert.equal(uniforms.uInteriorLight,0);assert.equal(uniforms.uEvening,1);assert.equal(uniforms.uDetailAmbient,0);
  click('finished');assert.equal(uniforms.uInteriorLight,0);assert.equal(uniforms.uDetailAmbient,0);
  click('furniture');assert.equal(uniforms.uInteriorLight,1);
  click('evening');assert.equal(uniforms.uEvening,0);
  assert.equal(uniforms.uInteriorLight,0);assert.equal(uniforms.uUpperLight,0);assert.equal(uniforms.uSmallLight,0);
  const disabledUploads=lightArrayUploads;click('bathroom');click('reset');
  assert.equal(lightArrayUploads,disabledUploads,'day navigation keeps expensive lighting disabled');
  assert.equal(document.documentElement.attrs['data-apartment-theme'],'day');
  assert.equal(nodes['.apt-light-controls'].hidden,false,'day circuits remain accessible');
  const beforeDayLights=uploads.length;
  click('small-light');assert.equal(uniforms.uSmallLight,1);assert.equal(uniforms.uInteriorLight,1);
  click('upper-light');assert.equal(uniforms.uUpperLight,1);
  assert.equal(volumeUploads,8,'day lights reuse existing textures');
  assert.equal(uploads.length,beforeDayLights,'day circuits never rebuild geometry');
  click('evening');assert.equal(document.documentElement.attrs['data-apartment-theme'],'evening');
  click('small-light');click('evening');assert.equal(uniforms.uSmallLight,1,'day scenario survives evening edits');
  click('upper-light');click('small-light');
  click('kitchen');const beforeFloor=uploads.length;
  key('ShiftLeft');for(let t=10000;t<=11200;t+=50)tick(t);release('ShiftLeft');flush();
  close(eyeFromMatrix(matrices.at(-1))[1],.138);
  assert.equal(uploads.length,beforeFloor,'floor collision does not rebuild geometry');
  click('reset');
  assert.equal(textureUploads,2,'camera, selection, modes, doors and evening reuse both 2D textures');
  assert.equal(root.dataset.error,undefined);
  nodes['[data-action="object"]'].value='bath-cabinet';nodes['[data-action="object"]'].listeners.change();flush();
  assert.equal(nodes['[data-action="cabinet"]'].hidden,false);
  const closedCabinetPositions=[...uploads.at(-12)];
  click('cabinet');assert.equal(nodes['[data-action="cabinet"]'].attrs['aria-pressed'],'true');
  assert(nodes['.apt-inspection'].textContent.includes('61.83°'));
  assert.notDeepEqual([...uploads.at(-12)],closedCabinetPositions);
  click('cabinet');assert.deepEqual([...uploads.at(-12)],closedCabinetPositions);
  {
  click('bathroom');
  const matrix=matrices.at(-1),point=[7.60,1.0,3.602,1];
  const clip=[0,1,2,3].map(r=>point.reduce((sum,v,c)=>sum+v*matrix[c*4+r],0));
  const nx=clip[0]/clip[3],ny=clip[1]/clip[3];
  assert.equal(win.ApartmentViewer.pickObject(win.APARTMENT_SCENE,{mode:'furniture',furniture:true,doorsClosed:true,cutWalls:false},matrix,nx,ny),'bath-cabinet');
  const bounds=nodes.canvas.getBoundingClientRect(),tap={pointerId:99,button:0,clientX:(nx+1)*bounds.width/2,clientY:(1-ny)*bounds.height/2,preventDefault(){}};
  nodes.canvas.listeners.pointerdown(tap);nodes.canvas.listeners.pointerup(tap);flush();
  assert.equal(nodes['[data-action="cabinet"]'].attrs['aria-pressed'],'true','click on mesh opens cabinet');
  nodes.canvas.listeners.pointerdown(tap);nodes.canvas.listeners.pointerup(tap);flush();
  assert.equal(nodes['[data-action="cabinet"]'].attrs['aria-pressed'],'false','second click on mesh closes cabinet');
  }
  click('cabinet');
  nodes['[data-action="towels"]'].checked=false;nodes['[data-action="towels"]'].listeners.change();flush();
  assert(nodes['.apt-inspection'].textContent.includes('Нижний фасад: 61.83°'));
  for(const e of win.APARTMENT_SCENE.elements.filter(e=>e.name.startsWith('BathTowelDrape')))
    assert.equal(win.ApartmentViewer.adjustedElement(e,{mode:'furniture',furniture:true,towelsVisible:false}),null);
  nodes['[data-action="towels"]'].checked=true;nodes['[data-action="towels"]'].listeners.change();flush();
  assert(nodes['.apt-inspection'].textContent.includes('Нижний фасад: 61.83°'));
  for(const e of win.APARTMENT_SCENE.elements.filter(e=>e.towelPress)){
    const opened=win.ApartmentViewer.adjustedElement(e,{mode:'furniture',furniture:true,cabinetOpen:true});
    assert.deepEqual(opened.detail.press,e.towelPress,'opening displaces cloth');
    assert(!win.ApartmentViewer.adjustedElement(e,{mode:'furniture',furniture:true}).detail.press,'closing restores hanging cloth');
  }
  for(const e of win.APARTMENT_SCENE.elements.filter(e=>e.cabinetMotion)){
    const closed=win.ApartmentViewer.adjustedElement(e,{mode:'furniture',furniture:true});
    const opened=win.ApartmentViewer.adjustedElement(e,{mode:'furniture',furniture:true,cabinetOpen:true});
    assert(Math.abs(opened.rotation-closed.rotation-e.cabinetMotion.angle)<1e-8);
    const bare=win.ApartmentViewer.adjustedElement(e,{mode:'furniture',furniture:true,cabinetOpen:true,towelsVisible:false});
    assert(Math.abs(bare.rotation-closed.rotation-e.cabinetMotion.bareAngle)<1e-8);
    const p=e.cabinetMotion.pivot;
    assert(Math.abs(Math.hypot(opened.position[0]-p[0],opened.position[2]-p[2])-Math.hypot(closed.position[0]-p[0],closed.position[2]-p[2]))<1e-8);
  }
  click('rough');assert.equal(nodes['[data-action="cabinet"]'].hidden,true);
  assert.equal(JSON.stringify(win.APARTMENT_SCENE),immutableScene,'all model coordinates must remain immutable');
  return draws.length;
}
let count=0;for(const width of [360,736,1024])for(const dark of [false,true])count+=test(width,dark);
console.log(`Passed: picking, whole-object dimensions, dropdown, occlusion, 3 modes × 3 sizes × 2 themes; simultaneous mouse/WASD/arrows, vertical axis, yaw, doors, reset. ${count} draw calls. DOM/WebGL mocked.`);
