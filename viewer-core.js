(function (global) {
  "use strict";

  function cssColor(root, token, alpha) {
    const probe = document.createElement("span");
    probe.style.color = `var(${token})`;
    probe.style.display = "none";
    root.appendChild(probe);
    const value = getComputedStyle(probe).color;
    probe.remove();
    const match = value.match(/[\d.]+/g);
    if (!match || match.length < 3) return [0.2, 0.2, 0.2, alpha];
    return [Number(match[0]) / 255, Number(match[1]) / 255, Number(match[2]) / 255, alpha];
  }

  function createBatch() {
    return { positions: [], normals: [], colors: [], surfaces: [] };
  }

  function pushVertex(batch, point, normal, color) {
    batch.positions.push(point[0], point[1], point[2]);
    batch.normals.push(normal[0], normal[1], normal[2]);
    batch.colors.push(color[0], color[1], color[2], color[3]);
    if (!batch.surfaces) batch.surfaces=[];
    if(batch.artwork){
      const e=batch.artwork,along=e.artwork.along,a=e.rotation||0;
      const q=rotateY(point.map((v,i)=>v-e.position[i]),-a);
      const flip= (e.artwork.axis===0?-e.artwork.sign:e.artwork.sign);
      const ratio=e.size[along]/e.size[1]/(e.artwork.ratio||1);
      let u=.5+q[along]/e.size[along]*flip,v=.5-q[1]/e.size[1];
      if(ratio>1)v=.5+(v-.5)/ratio;else u=.5+(u-.5)*ratio;
      const region=e.artwork.region||[0,0,1,1];
      batch.surfaces.push(7,region[0]+u*region[2],region[1]+v*region[3],0);
    }else batch.surfaces.push(...(batch.surface || [0,0,0,0]));
  }

  function rotateY(point, angle) {
    const c = Math.cos(angle);
    const s = Math.sin(angle);
    return [point[0] * c + point[2] * s, point[1], -point[0] * s + point[2] * c];
  }

  function worldPoint(local, center, angle) {
    const rotated = rotateY(local, angle);
    return [rotated[0] + center[0], rotated[1] + center[1], rotated[2] + center[2]];
  }

  function addBox(triangles, lines, element, color, edgeColor) {
    const center = element.position;
    const half = [element.size[0] / 2, element.size[1] / 2, element.size[2] / 2];
    const angle = element.rotation || 0;
    const corners = [
      [-half[0], -half[1], -half[2]],
      [half[0], -half[1], -half[2]],
      [half[0], half[1], -half[2]],
      [-half[0], half[1], -half[2]],
      [-half[0], -half[1], half[2]],
      [half[0], -half[1], half[2]],
      [half[0], half[1], half[2]],
      [-half[0], half[1], half[2]],
    ];
    const faces = [
      [[4, 5, 6, 7], [0, 0, 1]],
      [[1, 0, 3, 2], [0, 0, -1]],
      [[0, 4, 7, 3], [-1, 0, 0]],
      [[5, 1, 2, 6], [1, 0, 0]],
      [[3, 7, 6, 2], [0, 1, 0]],
      [[0, 1, 5, 4], [0, -1, 0]],
    ];
    for (const [indices, localNormal] of faces) {
      if (element.category === 'ceiling' && localNormal[1] !== -1) continue;
      if (element.bevel) {
        const radius=Math.min(element.bevel,...half.map(v=>v*.9));
        const a=corners[indices[0]],b=corners[indices[1]],d=corners[indices[3]];
        const u=b.map((v,i)=>v-a[i]),v=d.map((t,i)=>t-a[i]);
        const gu=[0,radius/Math.hypot(...u),1-radius/Math.hypot(...u),1];
        const gv=[0,radius/Math.hypot(...v),1-radius/Math.hypot(...v),1];
        function sample(s,t) {
          const p=a.map((q,i)=>q+u[i]*s+v[i]*t);
          const inner=p.map((q,i)=>Math.max(-half[i]+radius,Math.min(half[i]-radius,q)));
          const n=normalize(p.map((q,i)=>q-inner[i]));
          return [worldPoint(inner.map((q,i)=>q+n[i]*radius),center,angle),rotateY(n,angle)];
        }
        for(let i=0;i<3;i++)for(let j=0;j<3;j++){
          const pts=[sample(gu[i],gv[j]),sample(gu[i+1],gv[j]),sample(gu[i+1],gv[j+1]),sample(gu[i],gv[j+1])];
          for(const k of [0,1,2,0,2,3])pushVertex(triangles,pts[k][0],pts[k][1],color);
        }
        continue;
      }
      const normal = rotateY(localNormal, angle);
      const order = [0, 1, 2, 0, 2, 3];
      for (const index of order) pushVertex(triangles, worldPoint(corners[indices[index]], center, angle), normal, color);
    }

    if (element.noEdges || element.category === 'ceiling' || (element.category === "window" && element.material === "glass")) return;
    const edgePairs = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]];
    for (const pair of edgePairs) {
      pushVertex(lines, worldPoint(corners[pair[0]], center, angle), [0, 1, 0], edgeColor);
      pushVertex(lines, worldPoint(corners[pair[1]], center, angle), [0, 1, 0], edgeColor);
    }
  }

  function addCylinder(triangles, lines, element, color, edgeColor) {
    const center = element.position;
    const radius = element.size[0] / 2;
    const radiusZ = element.size[2] / 2;
    const angle = element.rotation || 0;
    const point = (a,y) => worldPoint([radius*Math.cos(a),y,radiusZ*Math.sin(a)],center,angle);
    const normal = a => {
      const x=Math.cos(a)/radius,z=Math.sin(a)/radiusZ,l=Math.hypot(x,z);
      return rotateY([x/l,0,z/l],angle);
    };
    const halfHeight = element.size[1] / 2;
    const segments = 40;
    for (let i = 0; i < segments; i += 1) {
      const a0 = Math.PI * 2 * i / segments;
      const a1 = Math.PI * 2 * (i + 1) / segments;
      const p0 = point(a0,-halfHeight),p1=point(a1,-halfHeight);
      const p2 = point(a1,halfHeight),p3=point(a0,halfHeight);
      const n0 = normal(a0),n1=normal(a1);
      pushVertex(triangles, p0, n0, color); pushVertex(triangles, p2, n1, color); pushVertex(triangles, p1, n1, color);
      pushVertex(triangles, p0, n0, color); pushVertex(triangles, p3, n0, color); pushVertex(triangles, p2, n1, color);
      const topCenter = [center[0], center[1] + halfHeight, center[2]];
      const bottomCenter = [center[0], center[1] - halfHeight, center[2]];
      pushVertex(triangles, topCenter, [0, 1, 0], color); pushVertex(triangles, p2, [0, 1, 0], color); pushVertex(triangles, p3, [0, 1, 0], color);
      pushVertex(triangles, bottomCenter, [0, -1, 0], color); pushVertex(triangles, p0, [0, -1, 0], color); pushVertex(triangles, p1, [0, -1, 0], color);
      if (!element.noEdges) {
        pushVertex(lines, p3, [0, 1, 0], edgeColor); pushVertex(lines, p2, [0, 1, 0], edgeColor);
        pushVertex(lines, p0, [0, 1, 0], edgeColor); pushVertex(lines, p1, [0, 1, 0], edgeColor);
      }
    }
  }

  function addHexagon(triangles, lines, e, color, edgeColor) {
    const outline = [[0,-.5],[.5,-.313],[.5,.307],[0,.5],[-.5,.307],[-.5,-.313]];
    const world = (x,y,z) => worldPoint([x*e.size[0],y*e.size[1],z*e.size[2]],e.position,e.rotation||0);
    for (let i=0;i<6;i++) {
      const [x,z]=outline[i], [nx,nz]=outline[(i+1)%6];
      const dx=(nx-x)*e.size[0], dz=(nz-z)*e.size[2], l=Math.hypot(dx,dz);
      const n=rotateY([dz/l,0,-dx/l],e.rotation||0);
      const a=world(x,-.5,z), b=world(nx,-.5,nz), c=world(nx,.5,nz), d=world(x,.5,z);
      for (const p of [a,c,b,a,d,c]) pushVertex(triangles,p,n,color);
      for (const p of [world(0,.5,0),c,d]) pushVertex(triangles,p,[0,1,0],color);
      for (const p of [world(0,-.5,0),a,b]) pushVertex(triangles,p,[0,-1,0],color);
      for (const p of [d,c,a,b,a,d]) pushVertex(lines,p,[0,1,0],edgeColor);
    }
  }

  // Same bounded parametric meshes as detail_geometry.py (GLB/USD/CPU QA).
  // Generated only on geometry changes; camera motion reuses GPU buffers.
  const detailMeshCache=new Map();
  function detailMesh(e) {
    const cacheKey=JSON.stringify([e.detail,e.size]);
    if(detailMeshCache.has(cacheKey))return detailMeshCache.get(cacheKey);
    const cfg=e.detail,kind=cfg.type,size=e.size,half=size.map(s=>s/2);
    const points=[],normals=[],indices=[];
    function patch(fn,us,vs,winding=null) {
      const start=points.length;
      for(const u of us)for(const v of vs){const [p,n]=fn(u,v);points.push(p);normals.push(n)}
      const stride=vs.length;
      for(let i=0;i<us.length-1;i++)for(let j=0;j<vs.length-1;j++){
        const a=start+i*stride+j,b=a+stride,c=b+1,d=a+1;
        const ab=points[b].map((x,k)=>x-points[a][k]),ac=points[c].map((x,k)=>x-points[a][k]);
        indices.push(...((winding??dot(cross(ab,ac),normals[a]))>=0?[a,b,c,a,c,d]:[a,c,b,a,d,c]));
      }
    }
    if(kind==='coverlet'){
      const top=cfg.top??.14,drop=cfg.drop??.32,rise=cfg.pillowRise??.105;
      const point=(x,z)=>{
        const bumps=[-1,1].reduce((s,sign)=>s+Math.exp(-(((x-sign*size[0]*.23)/(.24*size[0]))**4)),0);
        const pillow=rise*Math.min(1,bumps)*Math.exp(-(((z+size[2]*.34)/.23)**4));
        return [x,top+pillow+.002*Math.sin(x*24+z*8)*Math.sin(z*13),z];
      };
      const normal=(x,z)=>{const eps=.00001;return normalize([-(point(x+eps,z)[1]-point(x-eps,z)[1])/(2*eps),1,-(point(x,z+eps)[1]-point(x,z-eps)[1])/(2*eps)])};
      const xs=Array.from({length:33},(_,i)=>-half[0]+size[0]*i/32),zs=Array.from({length:41},(_,i)=>-half[2]+size[2]*i/40);
      patch((x,z)=>[point(x,z),normal(x,z)],xs,zs);
      for(const axis of [0,2])for(const side of [-1,1]){
        const along=2-axis;
        patch((u,t)=>{let p=[0,0,0];p[axis]=side*half[axis];p[along]=u;p=point(p[0],p[2]);p[1]-=(axis===2&&side===-1?.025:drop)*t;const n=[0,0,0];n[axis]=side;return [p,n]},along===0?xs:zs,[0,.25,.5,.75,1]);
      }
    }else if(kind==='desktop'){
      const cut=cfg.cutout??.065,xs=Array.from({length:33},(_,i)=>-half[0]+size[0]*i/32);
      const front=x=>-half[2]+cut*(1+Math.cos(Math.PI*x/half[0]))/2;
      for(const side of [-1,1])patch((x,t)=>[[x,side*half[1],front(x)+(half[2]-front(x))*t],[0,side,0]],xs,[0,1]);
      patch((x,y)=>[[x,y,front(x)],normalize([-cut*Math.PI*Math.sin(Math.PI*x/half[0])/(2*half[0]),0,-1])],xs,[-half[1],half[1]]);
      patch((x,y)=>[[x,y,half[2]],[0,0,1]],[-half[0],half[0]],[-half[1],half[1]]);
      for(const side of [-1,1])patch((z,y)=>[[side*half[0],y,z],[side,0,0]],[-half[2],half[2]],[-half[1],half[1]]);
    }else if(kind==='miter'){
      const poly=cfg.outline.map(([x,z])=>[x*size[0],z*size[2]]);
      for(let i=0;i<4;i++){
        const a=poly[i],b=poly[(i+1)%4],dx=b[0]-a[0],dz=b[1]-a[1],n=normalize([dz,0,-dx]);
        patch((t,y)=>[[a[0]+dx*t,y,a[1]+dz*t],n],[0,1],[-half[1],half[1]]);
      }
      for(const side of [-1,1])patch((u,v)=>{
        const w=[(1-u)*(1-v),u*(1-v),u*v,(1-u)*v];
        return [[poly.reduce((s,p,i)=>s+w[i]*p[0],0),side*half[1],poly.reduce((s,p,i)=>s+w[i]*p[1],0)],[0,side,0]];
      },[0,1],[0,1]);
    }else if(['rounded','pillow','bow'].includes(kind)){
      const radius=Math.min(cfg.radius??.015,...half.map(h=>h*.95));
      const grid=h=>kind!=='rounded'?Array.from({length:9},(_,i)=>h*(i-4)/4):cfg.steps===1?[-h,-h+radius,h-radius,h]:radius<=.008?[-h,-h+radius*.5,-h+radius,0,h-radius,h-radius*.5,h]:[-h,-h+radius*.3,-h+radius*.65,-h+radius,0,h-radius,h-radius*.65,h-radius*.3,h];
      for(let axis=0;axis<3;axis++){
        const along=[0,1,2].filter(i=>i!==axis);
        for(const side of [-1,1])patch((u,v)=>{
          let p=[0,0,0],n;p[axis]=side*half[axis];p[along[0]]=u;p[along[1]]=v;
          if(kind==='pillow'){
            const q=cfg.power??4,unit=p.map((t,i)=>t/half[i]),length=unit.reduce((s,t)=>s+Math.abs(t)**q,0)**(1/q);
            p=unit.map((t,i)=>t/length*half[i]);
            n=normalize(p.map((t,i)=>Math.sign(t)*Math.abs(t/half[i])**(q-1)/half[i]));
          }else{
            const inner=p.map((t,i)=>Math.max(-half[i]+radius,Math.min(half[i]-radius,t)));
            n=normalize(p.map((t,i)=>t-inner[i]));p=inner.map((t,i)=>t+radius*n[i]);
            if(kind==='bow'){
              const x=p[0]/half[0];p[2]=p[2]*.5+half[2]*(x*x-.5);
              n=normalize([n[0]-n[2]*4*half[2]*x/half[0],n[1],n[2]*2]);
            }
          }
          return [p,n];
        },grid(half[along[0]]),grid(half[along[1]]));
      }
    }else if(kind==='lathe'){
      const profile=cfg.rings,segments=cfg.segments??48;
      patch((k,a)=>{
        const [r,y]=profile[k],prev=profile[Math.max(0,k-1)],next=profile[Math.min(profile.length-1,k+1)],dr=next[0]-prev[0],dy=next[1]-prev[1];
        return [[r*size[0]*Math.cos(a),y*size[1],r*size[2]*Math.sin(a)],normalize([dy*Math.cos(a)/size[0],-dr/size[1],dy*Math.sin(a)/size[2]])];
      },profile.map((_,i)=>i),Array.from({length:segments+1},(_,i)=>i*Math.PI*2/segments));
    }else if(kind==='curtain'){
      const folds=cfg.folds??6,segments=folds*12;
      for(const side of [-1,1])patch((u,v)=>{
        const phase=u*Math.PI*2*folds+.15*Math.sin(v*3),z=half[2]*.90*Math.sin(phase);
        const dx=half[2]*.90*Math.cos(phase)*Math.PI*2*folds/size[0],dy=half[2]*.90*Math.cos(phase)*.45*Math.cos(v*3)/size[1];
        return [[(u-.5)*size[0],(v-.5)*size[1],z+side*.0007],normalize([-side*dx,-side*dy,side])];
      },Array.from({length:segments+1},(_,i)=>i/segments),Array.from({length:7},(_,i)=>i/6));
    }else if(kind==='towel'){
      const phase=cfg.phase||0,lean=cfg.lean||0,offset=cfg.offset??.0007;
      const point=(u,t)=>{
        const a=Math.min(1,Math.max(0,t/.70)),spread=a*a*(3-2*a),width=.28+.72*spread;
        const x=(u-.5)*size[0]*width+lean*(1-spread),sag=.07*Math.abs(2*u-1)**1.5*(1-t),hem=.015*Math.sin(u*Math.PI*2+phase)*t**6;
        const y=half[1]-size[1]*(.02+.94*t+sag+hem);
        const z=size[2]*(.29*Math.sin(u*Math.PI*2*1.6+.65*t+phase)+.075*Math.sin(u*Math.PI*2*3.1-t*1.7)+.06*Math.sin(t*Math.PI));
        let p=[x,y,z];
        if(cfg.press){const n=cfg.press.normal,distance=dot(n,p)+cfg.press.offset;if(distance<0)p=p.map((v,i)=>v-distance*n[i]);}
        return p;
      };
      const [lo,hi]=cfg.tRange||[0,1],rows=cfg.tRange?2:28;
      for(const side of [-1,1])patch((u,t)=>{
        const p=point(u,t),eps=.00001,ua=point(u-eps,t),ub=point(u+eps,t),ta=point(u,t-eps),tb=point(u,t+eps);
        const du=ub.map((v,i)=>v-ua[i]),dt=tb.map((v,i)=>v-ta[i]),n=normalize(cross(dt,du));p[2]+=side*offset;
        return [p,n.map(v=>side*v)];
      },Array.from({length:25},(_,i)=>i/24),Array.from({length:rows+1},(_,i)=>lo+(hi-lo)*i/rows),-side);
    }else if(kind==='rod'){
      const a=cfg.start.map((t,i)=>t*size[i]),b=cfg.end.map((t,i)=>t*size[i]),axis=normalize(b.map((t,i)=>t-a[i]));
      const u=normalize(cross(axis,Math.abs(axis[1])<.95?[0,1,0]:[1,0,0])),v=cross(axis,u);
      patch((k,angle)=>{
        const t=k<2?0:1,r=k===0||k===3?0:cfg.radius,radial=u.map((q,i)=>q*Math.cos(angle)+v[i]*Math.sin(angle));
        return [a.map((q,i)=>q+(b[i]-q)*t+r*radial[i]),k===0?axis.map(q=>-q):k===3?axis:radial];
      },[0,1,2,3],Array.from({length:13},(_,i)=>i*Math.PI*2/12));
    }else if(kind==='leaf'){
      const leafSize=cfg.leafSize||size,leafHalf=leafSize.map(s=>s/2),tilt=cfg.tilt||0,ct=Math.cos(tilt),st=Math.sin(tilt);
      const tiltPoint=p=>[p[0],p[1]*ct-p[2]*st,p[1]*st+p[2]*ct];
      for(const side of [-1,1])patch((t,v)=>{
        const sn=Math.sin(Math.PI*t),cs=Math.cos(Math.PI*t);
        const p=[leafHalf[0]*sn*v,(t-.5)*leafSize[1],leafSize[2]*sn*(.23-.25*v*v)+side*.0002];
        const dt=[leafHalf[0]*Math.PI*cs*v,leafSize[1],leafSize[2]*Math.PI*cs*(.23-.25*v*v)],dv=[leafHalf[0]*sn,0,-leafSize[2]*sn*.5*v];
        const n=sn<1e-8?[0,0,1]:normalize(cross(dv,dt));return [tiltPoint(p),tiltPoint(n.map(q=>side*q))];
      },Array.from({length:9},(_,i)=>i/8),[-1,-.5,0,.5,1]);
    }
    const result={points,normals,indices};detailMeshCache.set(cacheKey,result);return result;
  }

  function addDetail(triangles,e,color) {
    const mesh=detailMesh(e),angle=e.rotation||0;
    const points=mesh.points.map(p=>worldPoint(p,e.position,angle)),normals=mesh.normals.map(n=>rotateY(n,angle));
    for(const i of mesh.indices)pushVertex(triangles,points[i],normals[i],color);
  }

  function adjustedElement(element, state) {
    if(state.towelsVisible===false&&element.name.startsWith('BathTowelDrape'))return null;
    const mode = state.mode || 'furniture';
    if (element.rawOnly && mode !== 'rough') return null;
    if (mode === 'rough' && (element.category.startsWith('finish_') || (element.category === 'ceiling' && !element.rawOnly))) return null;
    if (mode !== 'furniture' && element.category === 'furniture') return null;
    if (mode === 'rough' && element.category === 'door' && !element.name.startsWith('Door_Entry_')) return null;
    if (mode === 'rough' && element.category === 'door_hardware') return null;
    const baseElement = element;
    if (mode !== 'rough' && element.finished) element = { ...element, ...element.finished };
    if(state.cabinetOpen&&element.towelPress)element={...element,detail:{...element.detail,press:element.towelPress}};
    if (state.cabinetOpen && element.cabinetMotion) {
      const motion=element.cabinetMotion,p=motion.pivot,a=state.towelsVisible===false?motion.bareAngle:motion.angle;
      const dx=element.position[0]-p[0],dz=element.position[2]-p[2],c=Math.cos(a),s=Math.sin(a);
      element={...element,position:[p[0]+dx*c+dz*s,element.position[1],p[2]-dx*s+dz*c],rotation:(element.rotation||0)+a};
    }
    if (state.doorsClosed && ['door','door_hardware'].includes(element.category) && element.closed) {
      const rise = element.finished && element.finished.closed && mode !== 'rough' ? 0 : element.position[1] - baseElement.position[1];
      element = { ...element, ...element.closed, position: [element.closed.position[0], element.closed.position[1]+rise, element.closed.position[2]] };
    }
    if (!state.furniture && element.category === "furniture") return null;
    // Finish panels and wall solids form continuous surfaces, not wireframe blocks.
    if(mode!=='rough'&&['wall','finish_wall'].includes(element.category))element={...element,noEdges:true};
    if (state.cutWalls && (element.category === "window" || element.category === 'ceiling')) return null;
    if (state.cutWalls && (element.category === "wall" || element.category === "door" || element.category === 'finish_wall')) {
      const base = element.position[1] - element.size[1] / 2;
      const height = Math.min(element.size[1], state.cutHeight - base);
      if (height <= 0) return null;
      return {
        ...element,
        position: [element.position[0], base + height / 2, element.position[2]],
        size: [element.size[0], height, element.size[2]],
      };
    }
    return element;
  }

  function invertMatrix(m) {
    const rows=Array.from({length:4},(_,r)=>Array.from({length:8},(_,c)=>c<4?m[c*4+r]:Number(c-4===r)));
    for(let c=0;c<4;c++) {
      let pivot=c;for(let r=c+1;r<4;r++)if(Math.abs(rows[r][c])>Math.abs(rows[pivot][c]))pivot=r;
      if(Math.abs(rows[pivot][c])<1e-12)return null;
      [rows[c],rows[pivot]]=[rows[pivot],rows[c]];
      const d=rows[c][c];for(let k=0;k<8;k++)rows[c][k]/=d;
      for(let r=0;r<4;r++)if(r!==c){const f=rows[r][c];for(let k=0;k<8;k++)rows[r][k]-=f*rows[c][k];}
    }
    return Array.from({length:16},(_,i)=>rows[i%4][4+Math.floor(i/4)]);
  }

  function pickObject(model,state,matrix,nx,ny) {
    const inv=invertMatrix(matrix);if(!inv)return null;
    function unproject(z) {
      const v=[nx,ny,z,1],p=[0,0,0,0];
      for(let r=0;r<4;r++)for(let c=0;c<4;c++)p[r]+=inv[c*4+r]*v[c];
      return p.slice(0,3).map(x=>x/p[3]);
    }
    const origin=unproject(-1),end=unproject(1),direction=end.map((x,i)=>x-origin[i]);
    let nearest=Infinity,selected=null;
    for(const raw of model.elements) {
      const e=adjustedElement(raw,state);if(!e)continue;
      if(model.materials[e.material].color[3]<.5)continue;
      const o=rotateY(origin.map((x,i)=>x-e.position[i]),-(e.rotation||0));
      const d=rotateY(direction,-(e.rotation||0));
      let near=0,far=Infinity;
      if(e.category==='ceiling') {
        if(d[1]<=0)continue; // ceiling underside only, matching the renderer
        near=(-e.size[1]/2-o[1])/d[1];
        if(near<0||Math.abs(o[0]+near*d[0])>e.size[0]/2||Math.abs(o[2]+near*d[2])>e.size[2]/2)continue;
      } else {
        for(let i=0;i<3;i++) {
          const h=e.size[i]/2;
          if(Math.abs(d[i])<1e-12){if(Math.abs(o[i])>h){far=-1;break;}continue;}
          const a=(-h-o[i])/d[i],b=(h-o[i])/d[i];
          near=Math.max(near,Math.min(a,b));far=Math.min(far,Math.max(a,b));
        }
        if(far<near)continue;
        if(e.shape==='cylinder') {
          // Unit-circle ray after scaling the two radii; supports oval cylinders.
          const rx=e.size[0]/2,rz=e.size[2]/2;
          const ox=o[0]/rx,oz=o[2]/rz,dx=d[0]/rx,dz=d[2]/rz;
          const A=dx*dx+dz*dz,B=2*(ox*dx+oz*dz),C=ox*ox+oz*oz-1;
          const candidates=[];
          const disc=B*B-4*A*C;
          if(A>1e-15&&disc>=0)for(const t of [(-B-Math.sqrt(disc))/(2*A),(-B+Math.sqrt(disc))/(2*A)])if(t>=0&&Math.abs(o[1]+t*d[1])<=e.size[1]/2)candidates.push(t);
          if(Math.abs(d[1])>1e-12)for(const h of [-e.size[1]/2,e.size[1]/2]){const t=(h-o[1])/d[1];if(t>=0&&(ox+t*dx)**2+(oz+t*dz)**2<=1)candidates.push(t);}
          if(!candidates.length)continue;near=Math.min(...candidates);
        }
      }
      if(near<nearest){nearest=near;selected=e.inspectId||null;}
    }
    return selected;
  }

  function buildGeometry(model, state, edgeColor) {
    const opaque = createBatch();
    const transparent = createBatch();
    const lines = createBatch();
    const selected=[];
    opaque.surface=[9,1,0,0];
    addBox(opaque,lines,{position:[4.3,-.006,4.3],size:[50,.008,50],noEdges:true},[.88,.88,.86,1],edgeColor);
    for (const original of model.elements) {
      const element = adjustedElement(original, state);
      if (!element) continue;
      const spec = model.materials[element.material];
      if (!spec) continue;
      const isSelected=state.selected&&element.inspectId===state.selected;
      if(isSelected)selected.push(element);
      const color = isSelected ? spec.color.map((v,i)=>i===3?v:v*.65+[.15,.78,1][i]*.35) : spec.color;
      const target = color[3] < 0.98 ? transparent : opaque;
      const pattern=element.category==='window'&&element.name.includes('_glass')?5:(spec.pattern||0);
      const circuit=pattern===4?(element.name.startsWith('PlanSpot_')||element.name.startsWith('PlanCentral_')?1:2):0;
      target.surface=[pattern,spec.roughness??.8,spec.metallic||0,circuit];
      target.artwork=element.artwork?element:null;
      if (element.detail) addDetail(target, element, color);
      else if (element.shape === "cylinder") addCylinder(target, lines, element, color, edgeColor);
      else if (element.shape === "hexagon") addHexagon(target, lines, element, color, edgeColor);
      else addBox(target, lines, element, color, edgeColor);
    }
    opaque.artwork=null;
    if(selected.length){
      const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
      for(const e of selected)for(const x of [-.5,.5])for(const y of [-.5,.5])for(const z of [-.5,.5]){
        const p=worldPoint([x*e.size[0],y*e.size[1],z*e.size[2]],e.position,e.rotation||0);
        p.forEach((v,i)=>{lo[i]=Math.min(lo[i],v-.012);hi[i]=Math.max(hi[i],v+.012)});
      }
      opaque.surface=[10,1,0,0];
      // Short solid corner brackets stay visible on light furniture in WebGL.
      for(const x of [0,1])for(const y of [0,1])for(const z of [0,1])for(let axis=0;axis<3;axis++){
        const bits=[x,y,z],p=bits.map((b,i)=>b?hi[i]:lo[i]),s=[.006,.006,.006];
        const len=Math.min(.16,(hi[axis]-lo[axis])*.25);s[axis]=len;
        p[axis]+=(bits[axis]?-1:1)*len/2;
        addBox(opaque,lines,{position:p,size:s,noEdges:true},[.12,.72,1,1],edgeColor);
      }
    }
    return { opaque, transparent, lines };
  }

  function compileShader(gl, type, source) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      const message = gl.getShaderInfoLog(shader);
      gl.deleteShader(shader);
      throw new Error(message || "Shader compilation failed");
    }
    return shader;
  }

  function createProgram(gl) {
    const vertexSource = `#version 300 es
      precision highp float;
      layout(location=0) in vec3 aPosition;
      layout(location=1) in vec3 aNormal;
      layout(location=2) in vec4 aColor;
      layout(location=3) in vec4 aSurface;
      uniform mat4 uViewProjection;
      out vec3 vNormal;
      out vec4 vColor;
      out vec3 vPosition;
      out vec4 vSurface;
      void main() {
        gl_Position = uViewProjection * vec4(aPosition, 1.0);
        vNormal = aNormal;
        vColor = aColor;
        vPosition=aPosition;
        vSurface=aSurface;
      }`;
    const fragmentSource = `#version 300 es
      precision highp float;
      in vec3 vNormal;
      in vec4 vColor;
      in vec3 vPosition;
      in vec4 vSurface;
      uniform float uUnlit;
      uniform float uInteriorLight;
      uniform float uEvening;
      uniform vec3 uEye;
      uniform sampler2D uAmbientMap;
      uniform sampler2D uArtwork;
      uniform float uDetailAmbient;
      precision highp sampler3D;
      uniform sampler3D uUpperPositive;
      uniform sampler3D uUpperNegative;
      uniform sampler3D uSmallPositive;
      uniform sampler3D uSmallNegative;
      uniform vec3 uBakeOrigin;
      uniform vec3 uBakeExtent;
      uniform float uUpperLight;
      uniform float uSmallLight;
      out vec4 outColor;
      float grainNoise(vec2 p){
        vec2 cell=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);
        vec4 h=fract(sin(vec4(dot(cell,vec2(127.1,311.7)),dot(cell+vec2(1,0),vec2(127.1,311.7)),dot(cell+vec2(0,1),vec2(127.1,311.7)),dot(cell+vec2(1,1),vec2(127.1,311.7))))*43758.5453);
        return mix(mix(h.x,h.y,f.x),mix(h.z,h.w,f.x),f.y);
      }
      float contactAmbient(vec3 p,vec3 n){
        if(uDetailAmbient<.5)return 1.0;
        vec2 uv=vec2(-1.0);vec2 tile=vec2(0.0);
        if(n.y>.98&&p.y<.07&&p.y>.0){
          uv=(p.xz-vec2(-.55,-.05))/vec2(9.9,9.40);
          if(any(lessThan(uv,vec2(0.0)))||any(greaterThan(uv,vec2(1.0))))return 1.0;
          return texture(uAmbientMap,vec2(clamp(uv.x,.5/256.0,255.5/256.0),.5+.5*clamp(uv.y,.5/256.0,255.5/256.0))).r;
        }
        else if(n.x<-.98&&abs(p.x-9.058)<.025){uv=vec2((p.z-4.10)/4.69,p.y/2.76);tile.x=1.0;}
        else if(n.x>.98&&abs(p.x-5.945)<.025){uv=vec2((p.z-5.60)/3.19,p.y/2.76);tile.y=1.0;}
        else if(n.z>.98&&abs(p.z-4.197)<.025){uv=vec2((p.x-7.17)/1.92,p.y/2.76);tile=vec2(1.0);}
        if(any(lessThan(uv,vec2(0.0)))||any(greaterThan(uv,vec2(1.0))))return 1.0;
        // Clamp inside a tile to avoid atlas-neighbour filtering at edges.
        return texture(uAmbientMap,(tile+clamp(uv,vec2(.5/128.0),vec2(127.5/128.0)))*vec2(.5,.25)).r;
      }
      float bakedLight(sampler3D positive,sampler3D negative,vec3 uv,vec3 n) {
        vec3 a=texture(positive,uv).rgb,b=texture(negative,uv).rgb;
        return 4.0*(dot(a*a,max(n,vec3(0.0))*max(n,vec3(0.0)))+
                    dot(b*b,min(n,vec3(0.0))*min(n,vec3(0.0))));
      }
      vec3 srgbToLinear(vec3 c) {
        return mix(c/12.92,pow((c+vec3(.055))/1.055,vec3(2.4)),step(vec3(.04045),c));
      }
      vec3 eveningDisplay(vec3 linearColor) {
        vec3 c=max(linearColor,vec3(0.0));
        // Compress luminance uniformly to preserve material hue/chroma.
        c/=1.0+dot(c,vec3(.2126,.7152,.0722));
        return mix(c*12.92,1.055*pow(c,vec3(1.0/2.4))-vec3(.055),step(vec3(.0031308),c));
      }
      void main() {
        vec3 n=normalize(vNormal),p=vPosition;
        bool detailed=p.x>-.55&&p.x<9.09&&p.z>-.05&&p.z<8.79;
        vec3 lightDirection=normalize(vec3(-.35,.70,.72));
        float diffuse=max(dot(n,lightDirection),0.0);
        float texFactor=1.0;
        // World-space procedural materials: no external downloads or image maps.
        vec2 uv=abs(n.y)>.5?p.xz:(abs(n.x)>.5?p.zy:p.xy);
        if(vSurface.x>.5&&vSurface.x<1.5){
          float flow=grainNoise(uv*vec2(14.0,.9));
          float grain=sin(uv.x*380.0+9.0*flow+2.0*sin(uv.y*3.7));
          float aa=1.0-smoothstep(.003,.018,max(length(dFdx(uv)),length(dFdy(uv))));
          texFactor=detailed ? .96+.12*grainNoise(uv*vec2(70.0,2.0))+.023*aa*grain+.025*sin(uv.x*42.0+6.0*flow) : .985+.027*sin(uv.x*380.0+3.0*sin(uv.y*4.7)+sin(uv.x*27.0))+.018*sin(uv.x*62.0+sin(uv.y*2.8));
        } else if(vSurface.x>1.5&&vSurface.x<2.5){
          float scale=1800.0;
          float aa=1.0-smoothstep(.002,.012,max(length(dFdx(uv)),length(dFdy(uv))));
          texFactor=detailed ? .985+.055*aa*sin(uv.x*scale)*sin(uv.y*scale)+.014*sin(uv.x*95.0)*sin(uv.y*110.0) : 1.0+.035*aa*sin(uv.x*scale)*sin(uv.y*scale);
        } else if(vSurface.x>2.5&&vSurface.x<3.5){
          texFactor=.99+.017*sin(uv.x*12.0+sin(uv.y*15.0))+.012*sin(uv.y*71.0+sin(uv.x*33.0));
        } else if(vSurface.x>11.5&&vSurface.x<12.5){
          float aa=1.0-smoothstep(.005,.025,max(length(dFdx(uv)),length(dFdy(uv))));
          float weave=sin(uv.x*780.0)*sin(uv.y*640.0);
          texFactor=.92+.17*aa*weave+.10*grainNoise(uv*90.0)+.055*sin(uv.x*55.0)*sin(uv.y*48.0);
        } else if(vSurface.x>7.5&&vSurface.x<8.5){
          vec2 brick=vec2(uv.x/.26,uv.y/.075);brick.x+=mod(floor(brick.y),2.0)*.5;
          vec2 f=fract(brick),aa=fwidth(brick);
          float joint=1.0-smoothstep(.025,.045+max(aa.x,aa.y),min(min(f.x,1.0-f.x),min(f.y,1.0-f.y)));
          texFactor=mix(.91+.15*grainNoise(floor(brick))+.035*grainNoise(uv*90.0),1.22,joint);
        }
        float ao=mix(1.0,contactAmbient(p,n),mix(.55,.30,uEvening));
        float daylight=detailed ? .67+.13*n.y+.15*diffuse : .66+diffuse*.24;
        vec3 lighting=mix(vec3(daylight*ao),vec3(.004,.005,.008)*mix(1.0,ao,.6),uEvening);
        // Four filtered volume samples replace all per-pixel ray/fixture loops.
        // Static walls and both door states were baked offline once.
        if(uInteriorLight>.5&&uUnlit<.5&&(vSurface.x<4.5||vSurface.x>5.5)){
          // Clamp the sample away from the coarse volume's ceiling boundary.
          // This avoids a spurious dark band where ceiling and wall meet.
          vec3 receiver=p+n*.08;receiver.y=min(receiver.y,2.57);
          vec3 uv=(receiver-uBakeOrigin)/uBakeExtent;
          if(all(greaterThanEqual(uv,vec3(0.0)))&&all(lessThanEqual(uv,vec3(1.0)))) {
            float energy=0.0;
            if(uUpperLight>.5)energy+=bakedLight(uUpperPositive,uUpperNegative,uv,n)*mix(1.0,.75,uEvening);
            if(uSmallLight>.5)energy+=bakedLight(uSmallPositive,uSmallNegative,uv,n);
            lighting+=vec3(1.0,.94,.85)*energy*mix(.28,ao,uEvening);
          }
        }
        vec3 halfway=normalize(lightDirection+normalize(uEye-p));
        float fresnel=.04+.20*pow(1.0-max(dot(n,normalize(uEye-p)),0.0),5.0);
        bool photo=vSurface.x>6.5&&vSurface.x<7.5;
        float rough=photo?.9:vSurface.y,metal=photo?0.0:vSurface.z;
        float spec=pow(max(dot(n,halfway),0.0),mix(100.0,8.0,rough))*(.12*metal+fresnel*(1.0-rough))*(1.0-uEvening*.92);
        // Palette values are display-space sRGB. Decode before multiplying by
        // linear irradiance; applying output gamma directly to palette values
        // was lifting blacks and washing out wood and coloured materials.
        vec3 base=photo?texture(uArtwork,vSurface.yz).rgb*vColor.rgb:vColor.rgb;
        if(vSurface.x>7.5&&vSurface.x<8.5&&n.y>.5){base=vec3(.95,.945,.93);texFactor=1.0;}
        vec3 albedo=uEvening>.5?srgbToLinear(base):base;
        vec3 rgb=albedo*texFactor*lighting+vec3(spec*(1.0-uEvening));
        if(vSurface.x>3.5&&vSurface.x<4.5){
          float enabled=vSurface.w<1.5?uUpperLight:uSmallLight;
          // Unpowered opal diffusers remain ordinary light-coloured surfaces.
          // Room lighting still illuminates them; only emission switches off.
          rgb=enabled>.5?vColor.rgb:albedo*lighting;
          if(enabled<.5&&uEvening>.5)rgb=eveningDisplay(rgb);
        }
        if(vSurface.x>5.5&&vSurface.x<6.5){ // A neutral mirror proxy, not a rendered reflection.
          rgb*=.85+.15*smoothstep(.8,2.2,p.y);
        }
        // Evening irradiance is linear. Compress highlights then convert to
        // display space so white diffuse ceilings retain detail without bloom.
        // Keep the established daytime appearance unchanged.
        if(vSurface.x<3.5||vSurface.x>5.5){
          if(uEvening>.5)rgb=eveningDisplay(rgb);
          else rgb=min(rgb,vec3(.6))+.4*(1.0-exp(-max(rgb-vec3(.6),vec3(0.0))/.4));
        }
        float alpha=vColor.a;
        if(vSurface.x>4.5&&vSurface.x<5.5){
          rgb=mix(rgb,vec3(.025,.039,.070)+vec3(.015,.018,.021)*max(n.y,0.0),uEvening);
          // Both sides transmit the already-rendered lit interior at night.
          // Retain a subtle reflection tint rather than an opaque night pane.
          alpha=mix(alpha,.12,uEvening);
        }
        outColor=vec4(mix(rgb,vColor.rgb*mix(1.0,.28,uEvening),uUnlit),alpha);
        if(vSurface.x>8.5&&vSurface.x<9.5)outColor=vec4(mix(vec3(.87,.87,.845),vec3(.051,.057,.067),uEvening),1.0);
        if(vSurface.x>9.5&&vSurface.x<10.5)outColor=vec4(vColor.rgb,1.0);
      }`;
    const program = gl.createProgram();
    gl.attachShader(program, compileShader(gl, gl.VERTEX_SHADER, vertexSource));
    gl.attachShader(program, compileShader(gl, gl.FRAGMENT_SHADER, fragmentSource));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program) || "Program link failed");
    return program;
  }

  function uploadBatch(gl, batch) {
    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    const buffers = [];
    const attributes = [
      [0, batch.positions, 3],
      [1, batch.normals, 3],
      [2, batch.colors, 4],
      [3, batch.surfaces, 4],
    ];
    for (const [location, values, size] of attributes) {
      const buffer = gl.createBuffer();
      buffers.push(buffer);
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(values), gl.STATIC_DRAW);
      gl.enableVertexAttribArray(location);
      gl.vertexAttribPointer(location, size, gl.FLOAT, false, 0, 0);
    }
    gl.bindVertexArray(null);
    return { vao, buffers, count: batch.positions.length / 3 };
  }

  function deleteGpuBatch(gl, gpuBatch) {
    if (!gpuBatch) return;
    gl.deleteVertexArray(gpuBatch.vao);
    for (const buffer of gpuBatch.buffers) gl.deleteBuffer(buffer);
  }

  function normalize(vector) {
    const length = Math.hypot(vector[0], vector[1], vector[2]) || 1;
    return [vector[0] / length, vector[1] / length, vector[2] / length];
  }

  function cross(a, b) {
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  }

  function dot(a, b) {
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  }

  function perspective(fov, aspect, near, far) {
    const f = 1 / Math.tan(fov / 2);
    const nf = 1 / (near - far);
    return new Float32Array([
      f / aspect, 0, 0, 0,
      0, f, 0, 0,
      0, 0, (far + near) * nf, -1,
      0, 0, 2 * far * near * nf, 0,
    ]);
  }

  function lookAt(eye, target, up) {
    const z = normalize([eye[0] - target[0], eye[1] - target[1], eye[2] - target[2]]);
    const x = normalize(cross(up, z));
    const y = cross(z, x);
    return new Float32Array([
      x[0], y[0], z[0], 0,
      x[1], y[1], z[1], 0,
      x[2], y[2], z[2], 0,
      -dot(x, eye), -dot(y, eye), -dot(z, eye), 1,
    ]);
  }

  function multiply(a, b) {
    const out = new Float32Array(16);
    for (let column = 0; column < 4; column += 1) {
      for (let row = 0; row < 4; row += 1) {
        out[column * 4 + row] =
          a[row] * b[column * 4] +
          a[4 + row] * b[column * 4 + 1] +
          a[8 + row] * b[column * 4 + 2] +
          a[12 + row] * b[column * 4 + 3];
      }
    }
    return out;
  }

  function mount(rootId, model) {
    const root = document.getElementById(rootId);
    if (!root || !model) return;
    const stage = root.querySelector(".apt-stage");
    const canvas = root.querySelector("canvas");
    const live = root.querySelector("[aria-live]");
    const error = root.querySelector(".apt-error");
    const wallsButton = root.querySelector('[data-action="walls"]');
    const furnitureButton = root.querySelector('[data-action="furniture"]');
    const roughButton = root.querySelector('[data-action="rough"]');
    const finishedButton = root.querySelector('[data-action="finished"]');
    const buildUpLabel = root.querySelector('.apt-buildup');
    const buildUpValues = root.querySelector('.apt-layer-values');
    const inspection = root.querySelector('.apt-inspection');
    const objectSelect = root.querySelector('[data-action="object"]');
    const cabinetButton = root.querySelector('[data-action="cabinet"]');
    const towelsToggle = root.querySelector('[data-action="towels"]');
    const towelsLabel = root.querySelector('[data-action="towels-label"]');
    const resetButton = root.querySelector('[data-action="reset"]');
    const topButton = root.querySelector('[data-action="top"]');
    const doorsButton = root.querySelector('[data-action="doors"]');
    const kitchenButton = root.querySelector('[data-action="kitchen"]');
    const bathroomButton = root.querySelector('[data-action="bathroom"]');
    const eveningButton = root.querySelector('[data-action="evening"]');
    const upperButton = root.querySelector('[data-action="upper-light"]');
    const smallButton = root.querySelector('[data-action="small-light"]');
    const lightControls = root.querySelector('.apt-light-controls');
    const gl = canvas.getContext("webgl2", { antialias: true, alpha: true, premultipliedAlpha: false });
    if (!gl) {
      root.dataset.error = "true";
      error.textContent = "Для просмотра модели нужен браузер с WebGL 2.";
      return;
    }

    try {
      const program = createProgram(gl);
      const matrixLocation = gl.getUniformLocation(program, "uViewProjection");
      const unlitLocation = gl.getUniformLocation(program, "uUnlit");
      const interiorLightLocation=gl.getUniformLocation(program,"uInteriorLight");
      const eyeLocation=gl.getUniformLocation(program,"uEye");
      const ambientLocation=gl.getUniformLocation(program,"uDetailAmbient");
      const ambientSamplerLocation=gl.getUniformLocation(program,'uAmbientMap');
      const artworkLocation=gl.getUniformLocation(program,'uArtwork');
      const artworkTexture=gl.createTexture();
      gl.activeTexture(gl.TEXTURE0+5);gl.bindTexture(gl.TEXTURE_2D,artworkTexture);
      const art=model.artwork,artPixels=art?Uint8Array.from(atob(art.pixels),c=>c.charCodeAt(0)):new Uint8Array([220,220,215]);
      gl.pixelStorei(gl.UNPACK_ALIGNMENT,1);
      gl.texImage2D(gl.TEXTURE_2D,0,gl.RGB8,art?.width||1,art?.height||1,0,gl.RGB,gl.UNSIGNED_BYTE,artPixels);
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
      const ambientTexture=gl.createTexture();
      gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,ambientTexture);
      const ambient=model.detailAmbient;
      const ambientPixels=ambient?Uint8Array.from(atob(ambient.pixels),c=>c.charCodeAt(0)):new Uint8Array([255]);
      gl.pixelStorei(gl.UNPACK_ALIGNMENT,1);
      gl.texImage2D(gl.TEXTURE_2D,0,gl.R8,ambient?.width||1,ambient?.height||1,0,gl.RED,gl.UNSIGNED_BYTE,ambientPixels);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
      const eveningLocation=gl.getUniformLocation(program,'uEvening');
      const lightLocations=Object.fromEntries(['uUpperPositive','uUpperNegative','uSmallPositive','uSmallNegative','uBakeOrigin','uBakeExtent','uUpperLight','uSmallLight'].map(n=>[n,gl.getUniformLocation(program,n)]));
      const lightTextures={};
      // Distinct, complete sampler bindings are required even during the day.
      for(let i=0;i<4;i++){
        gl.activeTexture(gl.TEXTURE0+1+i);gl.bindTexture(gl.TEXTURE_3D,gl.createTexture());
        gl.texImage3D(gl.TEXTURE_3D,0,gl.RGB8,1,1,1,0,gl.RGB,gl.UNSIGNED_BYTE,new Uint8Array(3));
        gl.texParameteri(gl.TEXTURE_3D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_3D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
      }
      gl.activeTexture(gl.TEXTURE0);
      function loadLightTextures(){
        if(lightTextures.open)return;
        if(!model.lightBake)throw new Error('Отсутствуют подготовленные карты освещения. Пересоберите модель.');
        const b=model.lightBake;
        for(const variant of ['open','closed'])lightTextures[variant]=['upper_positive','upper_negative','small_positive','small_negative'].map((key,i)=>{
          const t=gl.createTexture();gl.activeTexture(gl.TEXTURE0+1+i);gl.bindTexture(gl.TEXTURE_3D,t);
          const pixels=Uint8Array.from(atob(b.variants[variant][key]),c=>c.charCodeAt(0));
          gl.texImage3D(gl.TEXTURE_3D,0,gl.RGB8,...b.size,0,gl.RGB,gl.UNSIGNED_BYTE,pixels);
          for(const param of [gl.TEXTURE_MIN_FILTER,gl.TEXTURE_MAG_FILTER])gl.texParameteri(gl.TEXTURE_3D,param,gl.LINEAR);
          for(const param of [gl.TEXTURE_WRAP_S,gl.TEXTURE_WRAP_T,gl.TEXTURE_WRAP_R])gl.texParameteri(gl.TEXTURE_3D,param,gl.CLAMP_TO_EDGE);
          return t;
        });
        gl.uniform3fv(lightLocations.uBakeOrigin,b.origin);gl.uniform3fv(lightLocations.uBakeExtent,b.extent);
        ['uUpperPositive','uUpperNegative','uSmallPositive','uSmallNegative'].forEach((name,i)=>gl.uniform1i(lightLocations[name],i+1));
        gl.activeTexture(gl.TEXTURE0);
      }
      const state = { cutWalls: true, cutHeight: 1.35, furniture: true, doorsClosed: false, mode: 'furniture', evening:false, upperLight:false,smallLight:false,cabinetOpen:false,towelsVisible:true };
      const lightScenarios={day:[false,false],evening:[true,true]};
      const floorColliders=model.elements.filter(e=>e.name.startsWith('Finish_Floor')).map(e=>({...e,...e.finished}));
      function clampCameraFloor(){
        let minimum=.10;
        for(const floor of floorColliders){
          const p=floor.position,s=floor.size;
          if(Math.abs(camera.eye[0]-p[0])<=s[0]/2&&Math.abs(camera.eye[2]-p[2])<=s[2]/2)
            minimum=Math.max(minimum,(state.mode==='rough'?0:p[1]+s[1]/2+.0004)+.12);
        }
        camera.eye[1]=Math.max(minimum,camera.eye[1]);
      }
      let lastLightingKey=null;
      const camera = { yaw: 1.02, pitch: 1.02, distance: 17.5, target: [4.25, 0.58, 4.65], top: false };
      camera.eye = [
        camera.target[0]+camera.distance*Math.cos(camera.pitch)*Math.cos(camera.yaw),
        camera.target[1]+camera.distance*Math.sin(camera.pitch),
        camera.target[2]+camera.distance*Math.cos(camera.pitch)*Math.sin(camera.yaw),
      ];
      const initialCamera = JSON.parse(JSON.stringify(camera));
      const pointers = new Map();
      let pinchDistance = 0;
      let pinchMidpoint = null;
      let gpu = null;
      let framePending = false;
      let lastViewProjection=null;
      let pointerClick=null;
      const heldKeys = new Set();
      let lastMoveTime = null;

      function stopKeyboard() {
        heldKeys.clear(); lastMoveTime = null;
      }

      function selectObject(id) {
        state.selected=id||null;
        if(objectSelect)objectSelect.value=id||'';
        const item=(model.objects||[]).find(x=>x.id===id);
        if(inspection)inspection.textContent=item ? `${item.label} · Ш × Г × В: ${item.dimensionsMm.join(' × ')} мм` : 'Нажмите на предмет, чтобы увидеть размеры.';
        if(cabinetButton){
          cabinetButton.hidden=id!=='bath-cabinet'||state.mode!=='furniture';
          cabinetButton.textContent=state.cabinetOpen?'Закрыть пенал':'Открыть пенал';
          cabinetButton.setAttribute('aria-pressed',String(state.cabinetOpen));
        }
        if(towelsLabel)towelsLabel.hidden=id!=='bath-cabinet'||state.mode!=='furniture';
        if(id==='bath-cabinet'&&inspection&&model.cabinetMotion){
          const main=model.cabinetMotion.groups.find(g=>g.group==='main');
          const angle=state.towelsVisible?main.limitDegrees:main.bareDegrees;
          inspection.textContent+=` Нижний фасад: ${state.cabinetOpen?angle:0}°. Упор в сушитель: ${main.limitDegrees}°. ${model.cabinetMotion.note}`;
        }
        rebuild();
      }
      if(cabinetButton)cabinetButton.addEventListener('click',()=>{
        if(state.mode!=='furniture')return;
        state.cabinetOpen=!state.cabinetOpen;selectObject('bath-cabinet');
        live.textContent=state.cabinetOpen?'Пенал открыт до первого препятствия.':'Пенал закрыт.';
      });
      if(towelsToggle)towelsToggle.addEventListener('change',()=>{
        state.towelsVisible=towelsToggle.checked;selectObject('bath-cabinet');
      });
      if(objectSelect) {
        for(const item of model.objects||[]) {
          const option=document.createElement('option');option.value=item.id;option.textContent=item.label;objectSelect.appendChild(option);
        }
        objectSelect.addEventListener('change',()=>selectObject(objectSelect.value));
      }

      function moveWithKeys(timestamp) {
        if (!heldKeys.size) { lastMoveTime = null; return; }
        const dt = lastMoveTime === null ? 1/60 : Math.max(0, Math.min(.05,(timestamp-lastMoveTime)/1000));
        lastMoveTime = timestamp;
        const side = Number(heldKeys.has('KeyD'))-Number(heldKeys.has('KeyA'));
        const forward = Number(heldKeys.has('KeyW'))-Number(heldKeys.has('KeyS'));
        const vertical = Number(heldKeys.has('Space'))-Number(heldKeys.has('ShiftLeft')||heldKeys.has('ShiftRight'));
        const tilt = Number(heldKeys.has('ArrowDown'))-Number(heldKeys.has('ArrowUp'));
        const turn = Number(heldKeys.has('ArrowRight'))-Number(heldKeys.has('ArrowLeft'));
        const length = Math.hypot(side,forward) || 1;
        const step = 2.5*dt/length;
        if (camera.top) {
          camera.target[0] += side*step; camera.target[2] -= forward*step;
        } else {
          camera.yaw += turn*1.2*dt;
          camera.pitch=Math.max(-1.53,Math.min(1.53,camera.pitch+tilt*1.0*dt));
          // Height is the world-up axis (Y in this renderer), independent of gaze.
          camera.eye[1] += vertical*2.5*dt;
          camera.eye[0] += (side*Math.sin(camera.yaw)-forward*Math.cos(camera.yaw))*step;
          camera.eye[2] += (-side*Math.cos(camera.yaw)-forward*Math.sin(camera.yaw))*step;
        }
      }

      function edgeColor() {
        return [.18,.18,.17,.20];
      }

      function rebuild() {
        if (gpu) {
          deleteGpuBatch(gl, gpu.opaque);
          deleteGpuBatch(gl, gpu.transparent);
          deleteGpuBatch(gl, gpu.lines);
        }
        const geometry = buildGeometry(model, state, edgeColor());
        gpu = {
          opaque: uploadBatch(gl, geometry.opaque),
          transparent: uploadBatch(gl, geometry.transparent),
          lines: uploadBatch(gl, geometry.lines),
        };
        requestRender();
      }

      function resize() {
        const bounds = stage.getBoundingClientRect();
        const ratio = Math.min(global.devicePixelRatio || 1, 1.5);
        const width = Math.max(1, Math.round(bounds.width * ratio));
        const height = Math.max(1, Math.round(bounds.height * ratio));
        if (canvas.width !== width || canvas.height !== height) {
          canvas.width = width;
          canvas.height = height;
          gl.viewport(0, 0, width, height);
        }
      }

      function drawBatch(gpuBatch, mode, unlit) {
        if (!gpuBatch || !gpuBatch.count) return;
        gl.uniform1f(unlitLocation, unlit ? 1 : 0);
        gl.bindVertexArray(gpuBatch.vao);
        gl.drawArrays(mode, 0, gpuBatch.count);
      }

      function render(timestamp = 0) {
        framePending = false;
        moveWithKeys(timestamp);
        clampCameraFloor();
        resize();
        const cosPitch = Math.cos(camera.pitch);
        // Free look: only the viewing direction changes during a mouse drag.
        // Eye position is independent of yaw/pitch; all world geometry stays fixed.
        const gaze = [
          camera.eye[0] - cosPitch * Math.cos(camera.yaw),
          camera.eye[1] - Math.sin(camera.pitch),
          camera.eye[2] - cosPitch * Math.sin(camera.yaw),
        ];
        const aspect = canvas.width/canvas.height;
        const halfHeight = camera.distance * .35 / Math.min(1, aspect);
        const halfWidth = halfHeight * aspect;
        const projection = camera.top ? new Float32Array([
          1/halfWidth,0,0,0, 0,1/halfHeight,0,0, 0,0,-2/80,0, 0,0,-1,1
        ]) : perspective(camera.fov || Math.PI / 4.2, aspect, 0.08, 80);
        const view = camera.top
          ? lookAt([camera.target[0],30,camera.target[2]], [camera.target[0],0,camera.target[2]], [0,0,-1])
          : lookAt(camera.eye, gaze, [0, 1, 0]);
        const viewProjection = multiply(projection, view);
        lastViewProjection=viewProjection;

        gl.clearColor(...(state.evening?[18/255,20/255,23/255,1]:[235/255,235/255,230/255,1]));
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        gl.enable(gl.DEPTH_TEST);
        gl.enable(gl.CULL_FACE);
        gl.cullFace(gl.BACK);
        gl.useProgram(program);
        gl.uniform1i(ambientSamplerLocation,0);
        gl.uniform1i(artworkLocation,5);
        ['uUpperPositive','uUpperNegative','uSmallPositive','uSmallNegative'].forEach((name,i)=>gl.uniform1i(lightLocations[name],i+1));
        gl.uniform1f(ambientLocation,ambient&&state.mode==='furniture'?1:0);
        gl.uniformMatrix4fv(matrixLocation, false, viewProjection);
        gl.uniform3fv(eyeLocation,camera.eye);
        const localLights=state.mode==='furniture'&&(state.upperLight||state.smallLight);
        gl.uniform1f(interiorLightLocation,localLights?1:0);
        gl.uniform1f(eveningLocation,state.evening?1:0);
        gl.uniform1f(lightLocations.uUpperLight,localLights&&state.upperLight?1:0);
        gl.uniform1f(lightLocations.uSmallLight,localLights&&state.smallLight?1:0);
        // Day mode skips volume sampling; camera motion never uploads light data.
        // Door changes only select another already-uploaded static volume set.
        const lightingKey=localLights?`evening:${state.doorsClosed}`:'off';
        if(lightingKey!==lastLightingKey){
          if(localLights){
            loadLightTextures();
            lightTextures[state.doorsClosed?'closed':'open'].forEach((t,i)=>{gl.activeTexture(gl.TEXTURE0+1+i);gl.bindTexture(gl.TEXTURE_3D,t)});
            gl.activeTexture(gl.TEXTURE0);
          }
          lastLightingKey=lightingKey;
        }

        gl.disable(gl.BLEND);
        gl.depthMask(true);
        drawBatch(gpu.opaque, gl.TRIANGLES, false);

        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        gl.depthMask(false);
        drawBatch(gpu.transparent, gl.TRIANGLES, false);
        drawBatch(gpu.lines, gl.LINES, true);
        gl.depthMask(true);
        gl.bindVertexArray(null);
        if (heldKeys.size) requestRender();
      }

      function requestRender() {
        if (framePending) return;
        framePending = true;
        global.requestAnimationFrame(render);
      }

      function updateControls() {
        root.dataset.evening=String(state.evening);
        document.documentElement.setAttribute('data-apartment-theme',state.evening?'evening':'day');
        if(eveningButton)eveningButton.setAttribute('aria-pressed',String(state.evening));
        if(lightControls)lightControls.hidden=false;
        if(upperButton)upperButton.setAttribute('aria-pressed',String(state.upperLight));
        if(smallButton)smallButton.setAttribute('aria-pressed',String(state.smallLight));
        wallsButton.textContent = state.cutWalls ? "Срез стен" : "Полные стены";
        wallsButton.setAttribute("aria-pressed", String(!state.cutWalls));
        for (const [button,mode] of [[roughButton,'rough'],[finishedButton,'finished'],[furnitureButton,'furniture']]) {
          if (button) button.setAttribute('aria-pressed',String(state.mode===mode));
        }
        if (buildUpLabel) {
          const f=model.metadata.finishes;
          buildUpLabel.textContent=state.mode==='rough' ? 'Черновая высота 2,800 м · без отделки и мебели' :
            `Высота модели ${(f.dry_clear_height).toFixed(3).replace('.',',')} м · ванная ${f.wet_clear_height.toFixed(3).replace('.',',')} м · толщины отделки предварительные`;
          if (buildUpValues) buildUpValues.textContent=`Стяжка ${f.screed*1000} мм · ламинат с подложкой ${f.laminate_underlay*1000} мм · штукатурка с обоями ${f.plaster_wallpaper*1000} мм · плитка с клеем ${f.tile_adhesive*1000} мм · опуск потолка ${f.ceiling_drop*1000} мм`;
          if (buildUpValues&&f.reference) buildUpValues.textContent+=' · '+f.reference;
        }
        if (topButton) topButton.setAttribute("aria-pressed", String(camera.top));
        if (doorsButton) {
          doorsButton.textContent = state.doorsClosed ? "Открыть двери" : "Закрыть двери";
          doorsButton.setAttribute("aria-pressed", String(state.doorsClosed));
        }
      }

      function pan(dx, dy) {
        if (camera.top) {
          const scale = camera.distance*.7/Math.min(canvas.clientWidth,canvas.clientHeight);
          camera.target[0] -= dx*scale; camera.target[2] -= dy*scale;
          return;
        }
        const scale = camera.distance * 0.00155;
        const right = [Math.sin(camera.yaw), 0, -Math.cos(camera.yaw)];
        const outward = [Math.cos(camera.yaw), 0, Math.sin(camera.yaw)];
        camera.eye[0] -= right[0] * dx * scale;
        camera.eye[2] -= right[2] * dx * scale;
        camera.eye[0] += outward[0] * dy * scale;
        camera.eye[2] += outward[2] * dy * scale;
      }

      function zoom(factor) {
        if (camera.top) {
          camera.distance = Math.max(5.5, Math.min(29, camera.distance*factor));
          return;
        }
        // Dolly the camera along its gaze. Wheel input remains useful after WASD
        // movement and does not orbit or rescale the apartment.
        const step = Math.max(-3, Math.min(3, (factor-1)*camera.distance));
        camera.eye[0] += step*Math.cos(camera.pitch)*Math.cos(camera.yaw);
        camera.eye[1] += step*Math.sin(camera.pitch);
        camera.eye[2] += step*Math.cos(camera.pitch)*Math.sin(camera.yaw);
      }

      wallsButton.addEventListener("click", function () {
        state.cutWalls = !state.cutWalls;
        updateControls();
        rebuild();
        live.textContent = state.cutWalls ? "Стены показаны в срезе 1,35 метра." : "Полная высота. Потолок виден снизу, сверху квартира открыта для обзора.";
      });
      for (const [button,mode] of [[roughButton,'rough'],[finishedButton,'finished'],[furnitureButton,'furniture']]) {
        if (button) button.addEventListener('click',function () {
          state.mode=mode;state.furniture=mode==='furniture';
          if(mode!=='furniture') {
            state.selected=null;if(objectSelect)objectSelect.value='';
            if(inspection)inspection.textContent='Для выбора предметов включите режим «Мебель».';
          } else if(!state.selected&&inspection) inspection.textContent='Нажмите на предмет, чтобы увидеть размеры.';
          if(objectSelect)objectSelect.disabled=mode!=='furniture';
          if(cabinetButton)cabinetButton.hidden=mode!=='furniture'||state.selected!=='bath-cabinet';
          if(towelsLabel)towelsLabel.hidden=mode!=='furniture'||state.selected!=='bath-cabinet';
          stopKeyboard();updateControls();rebuild();
          live.textContent={rough:'Черновой: исходные стены и плита без отделки и мебели.',finished:'Чистовой: отделка, потолок и двери, без мебели и оборудования.',furniture:'Чистовая отделка с мебелью и оборудованием.'}[mode];
        });
      }
      resetButton.addEventListener("click", function () {
        stopKeyboard();
        camera.top = false;
        camera.yaw = initialCamera.yaw;
        camera.pitch = initialCamera.pitch;
        camera.distance = initialCamera.distance;
        camera.target = initialCamera.target.slice();
        camera.eye = initialCamera.eye.slice();
        camera.fov=initialCamera.fov;
        updateControls();
        requestRender();
        live.textContent = "Исходный ракурс восстановлен.";
      });
      if(kitchenButton)kitchenButton.addEventListener('click',function(){
        stopKeyboard();
        camera.eye=[6.45,1.50,8.50];
        camera.yaw=Math.atan2(3.1,-1.4);camera.pitch=.075;camera.distance=3.4;camera.fov=1.10;camera.top=false;
        state.cutWalls=false;state.mode='furniture';state.furniture=true;state.doorsClosed=true;
        if(objectSelect)objectSelect.disabled=false;
        updateControls();rebuild();
        live.textContent='Кухня: материалы по согласованной визуализации, геометрия по плану.';
      });
      if(bathroomButton)bathroomButton.addEventListener('click',function(){
        stopKeyboard();camera.eye=[8.80,1.50,2.80];camera.yaw=-.30;
        camera.pitch=.14;camera.distance=2.0;camera.fov=1.25;camera.top=false;
        state.cutWalls=false;state.mode='furniture';state.furniture=true;state.doorsClosed=true;
        if(objectSelect)objectSelect.disabled=false;
        updateControls();rebuild();live.textContent='Ванная: простенок между дверным наличником и пеналом, примерка узкого вертикального полотенцесушителя.';
      });
      if(eveningButton)eveningButton.addEventListener('click',function(){
        lightScenarios[state.evening?'evening':'day']=[state.upperLight,state.smallLight];
        state.evening=!state.evening;
        [state.upperLight,state.smallLight]=lightScenarios[state.evening?'evening':'day'];
        updateControls();requestRender();
        live.textContent=state.evening?'Вечер: за окнами темно. Свет включён в режиме «Мебель»; оценка освещения приблизительная.':'Дневное освещение восстановлено.';
      });
      for(const [button,key] of [[upperButton,'upperLight'],[smallButton,'smallLight']])if(button)button.addEventListener('click',()=>{
        state[key]=!state[key];updateControls();requestRender();
      });
      if (doorsButton) doorsButton.addEventListener("click", function () {
        state.doorsClosed = !state.doorsClosed;
        updateControls(); rebuild();
        live.textContent = state.doorsClosed ? "Все четыре двери закрыты." : "Все четыре двери открыты.";
      });
      if (topButton) topButton.addEventListener("click", function () {
        stopKeyboard();
        camera.top = !camera.top;
        camera.target = initialCamera.target.slice();
        camera.distance = initialCamera.distance;
        updateControls(); requestRender();
        live.textContent = camera.top ? "Ортографический вид сверху: вход наверху, как на схеме." : "Трёхмерный вид.";
      });

      function editable(target) {
        return Boolean(target && target.closest && target.closest('input, textarea, select, [contenteditable]'));
      }
      // The canvas need not steal focus from a button while the mouse is held.
      // Keyboard and pointer input update the same camera concurrently. The
      // document is local to this viewer/iframe; no activation switch is needed.
      document.addEventListener('keydown', function (event) {
        if (editable(event.target) || event.ctrlKey || event.metaKey || event.altKey || event.isComposing || document.hidden) return;
        if (event.target && !root.contains(event.target) && event.target !== document.body && event.target !== document.documentElement) return;
        if (event.code === 'Escape') { event.preventDefault(); stopKeyboard(); if(state.selected)selectObject(null); return; }
        if (!['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space','ShiftLeft','ShiftRight'].includes(event.code)) return;
        // Height and yaw are perspective controls: return from the fixed plan
        // view to the saved 3D camera so their effect is immediately visible.
        if (camera.top && (event.code.startsWith('Arrow')||event.code==='Space'||event.code.startsWith('Shift'))) {
          camera.top=false; updateControls();
          live.textContent='Трёхмерный вид: стрелки — взгляд, Space и Shift — высота.';
        }
        event.preventDefault(); heldKeys.add(event.code); requestRender();
      });
      document.addEventListener('keyup', function (event) {
        heldKeys.delete(event.code);
        if (!heldKeys.size) lastMoveTime = null;
      });
      document.addEventListener('focusin', function (event) {
        if (editable(event.target) || !root.contains(event.target) && event.target !== document.body && event.target !== document.documentElement) stopKeyboard();
      });
      global.addEventListener('blur', function () { stopKeyboard(); });
      document.addEventListener('visibilitychange', function () { if (document.hidden) stopKeyboard(); });
      document.addEventListener('pointerdown', function (event) { if (!root.contains(event.target)) stopKeyboard(); });

      canvas.addEventListener("contextmenu", function (event) { event.preventDefault(); });
      canvas.addEventListener("pointerdown", function (event) {
        pointerClick = pointers.size===0&&event.button===0&&!event.shiftKey&&!heldKeys.size ? {id:event.pointerId,x:event.clientX,y:event.clientY} : null;
        canvas.setPointerCapture(event.pointerId);
        pointers.set(event.pointerId, { x: event.clientX, y: event.clientY, mode: event.button === 2 ? "pan" : "rotate" });
        if (pointers.size === 2) {
          pointerClick=null;
          const points = Array.from(pointers.values());
          pinchDistance = Math.hypot(points[1].x - points[0].x, points[1].y - points[0].y);
          pinchMidpoint = [(points[0].x + points[1].x) / 2, (points[0].y + points[1].y) / 2];
        }
      });
      canvas.addEventListener("pointermove", function (event) {
        if(pointerClick&&Math.hypot(event.clientX-pointerClick.x,event.clientY-pointerClick.y)>5)pointerClick=null;
        const previous = pointers.get(event.pointerId);
        if (!previous) return;
        const dx = event.clientX - previous.x;
        const dy = event.clientY - previous.y;
        pointers.set(event.pointerId, { ...previous, x: event.clientX, y: event.clientY });
        if (pointers.size === 1) {
          if (previous.mode === "pan" || camera.top) pan(dx, dy);
          else {
            camera.yaw += dx * 0.008;
            camera.pitch = Math.max(-1.53, Math.min(1.53, camera.pitch + dy * 0.007));
          }
        } else if (pointers.size === 2) {
          const points = Array.from(pointers.values());
          const distance = Math.hypot(points[1].x - points[0].x, points[1].y - points[0].y);
          const midpoint = [(points[0].x + points[1].x) / 2, (points[0].y + points[1].y) / 2];
          if (pinchDistance > 0) zoom(pinchDistance / Math.max(distance, 1));
          if (pinchMidpoint) pan(midpoint[0] - pinchMidpoint[0], midpoint[1] - pinchMidpoint[1]);
          pinchDistance = distance;
          pinchMidpoint = midpoint;
        }
        requestRender();
      });
      function releasePointer(event) {
        pointers.delete(event.pointerId);
        if (pointers.size < 2) {
          pinchDistance = 0;
          pinchMidpoint = null;
        }
      }
      canvas.addEventListener("pointerup", function(event) {
        if(pointerClick&&pointerClick.id===event.pointerId&&lastViewProjection&&!heldKeys.size) {
          const r=canvas.getBoundingClientRect();
          const id=pickObject(model,state,lastViewProjection,2*(event.clientX-r.left)/r.width-1,1-2*(event.clientY-r.top)/r.height);
          if(id==='bath-cabinet')state.cabinetOpen=!state.cabinetOpen;
          selectObject(id);
        }
        pointerClick=null;releasePointer(event);
      });
      canvas.addEventListener("pointercancel", function(event){pointerClick=null;releasePointer(event);});
      canvas.addEventListener("wheel", function (event) {
        event.preventDefault();
        zoom(Math.exp(event.deltaY * 0.001));
        requestRender();
      }, { passive: false });

      const resizeObserver = new ResizeObserver(requestRender);
      resizeObserver.observe(stage);
      const themeObserver = new MutationObserver(function () { rebuild(); });
      themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["class", "style", "data-theme"] });
      const colorScheme = global.matchMedia ? global.matchMedia("(prefers-color-scheme: dark)") : null;
      if (colorScheme && colorScheme.addEventListener) colorScheme.addEventListener("change", rebuild);

      updateControls();
      rebuild();
    } catch (caught) {
      root.dataset.error = "true";
      error.textContent = "Модель не удалось открыть: " + (caught && caught.message ? caught.message : "неизвестная ошибка");
    }
  }

  global.ApartmentViewer = { mount, pickObject, adjustedElement };
})(window);
