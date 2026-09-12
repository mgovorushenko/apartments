"""Compact parametric furniture meshes, shared with detailMesh in viewer-core.js.

Outputs unit-box vertices and inverse-scale-correct normals for GLB/USD, keeping
the approved element transforms and selection envelopes intact.
"""
import math


def mesh(e):
    kind=e.get('detail',{}).get('type')
    if not kind:return None
    size=e['size'];half=[s/2 for s in size];cfg=e['detail']
    points=[];normals=[];indices=[]
    def norm(v):
        length=math.sqrt(sum(t*t for t in v)) or 1
        return [t/length for t in v]
    def vertex(p,n):
        points.extend(p[i]/size[i] for i in range(3))
        normals.extend(norm([n[i]*size[i] for i in range(3)]))
    def patch(fn,us,vs,winding=None):
        start=len(points)//3
        for u in us:
            for v in vs:vertex(*fn(u,v))
        stride=len(vs)
        for i in range(len(us)-1):
            for j in range(len(vs)-1):
                a=start+i*stride+j;b=a+stride;c=b+1;d=a+1
                # Surface sample orientation determines winding.
                pa=points[a*3:a*3+3];pb=points[b*3:b*3+3];pc=points[c*3:c*3+3]
                ab=[pb[k]-pa[k] for k in range(3)];ac=[pc[k]-pa[k] for k in range(3)]
                cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
                sign=winding if winding is not None else sum(cross[k]*normals[a*3+k] for k in range(3))
                indices.extend([a,b,c,a,c,d] if sign>=0 else [a,c,b,a,d,c])
    if kind in ('rounded','pillow','bow'):
        radius=min(cfg.get('radius',.015),min(half)*.95)
        for axis in range(3):
            along=[i for i in range(3) if i!=axis]
            def grid(h):
                if kind in ('pillow','bow'):return [h*i/4 for i in range(-4,5)]
                if cfg.get('steps')==1:return [-h,-h+radius,h-radius,h]
                if radius<=.008:return [-h,-h+radius*.5,-h+radius,0,h-radius,h-radius*.5,h]
                return [-h,-h+radius*.3,-h+radius*.65,-h+radius,0,h-radius,h-radius*.65,h-radius*.3,h]
            for side in (-1,1):
                def sample(u,v):
                    p=[0.,0.,0.];p[axis]=side*half[axis];p[along[0]]=u;p[along[1]]=v
                    if kind=='pillow':
                        q=cfg.get('power',4);unit=[p[i]/half[i] for i in range(3)]
                        length=sum(abs(t)**q for t in unit)**(1/q)
                        p=[unit[i]/length*half[i] for i in range(3)]
                        n=norm([math.copysign(abs(p[i]/half[i])**(q-1),p[i])/half[i] for i in range(3)])
                    else:
                        inner=[max(-half[i]+radius,min(half[i]-radius,p[i])) for i in range(3)]
                        n=norm([p[i]-inner[i] for i in range(3)])
                        p=[inner[i]+radius*n[i] for i in range(3)]
                        if kind=='bow':
                            x=p[0]/half[0]
                            p[2]=p[2]*.5+half[2]*(x*x-.5)
                            n=norm([n[0]-n[2]*4*half[2]*x/half[0],n[1],n[2]*2])
                    return p,n
                patch(sample,grid(half[along[0]]),grid(half[along[1]]))
    elif kind=='lathe':
        profile=cfg['rings'];segments=cfg.get('segments',48)
        def sample(t,a):
            k=int(t);r,y=profile[k]
            prev=profile[max(0,k-1)];nxt=profile[min(len(profile)-1,k+1)]
            dr=nxt[0]-prev[0];dy=nxt[1]-prev[1]
            return [r*size[0]*math.cos(a),y*size[1],r*size[2]*math.sin(a)],norm([dy*math.cos(a)/size[0],-dr/size[1],dy*math.sin(a)/size[2]])
        patch(sample,list(range(len(profile))),[i*math.tau/segments for i in range(segments+1)])
    elif kind=='curtain':
        folds=cfg.get('folds',6);segments=folds*12
        for side in (-1,1):
            def sample(u,v):
                phase=u*math.tau*folds+.15*math.sin(v*3)
                z=half[2]*.90*math.sin(phase)
                dx=half[2]*.90*math.cos(phase)*math.tau*folds/size[0]
                dy=half[2]*.90*math.cos(phase)*.45*math.cos(v*3)/size[1]
                return [(u-.5)*size[0],(v-.5)*size[1],z+side*.0007],norm([-side*dx,-side*dy,side])
            patch(sample,[i/segments for i in range(segments+1)],[i/6 for i in range(7)])
    elif kind=='towel':
        phase=cfg.get('phase',0);lean=cfg.get('lean',0);offset=cfg.get('offset',.0007)
        def point(u,t):
            a=min(1,max(0,t/.70));spread=a*a*(3-2*a)
            width=.28+.72*spread
            x=(u-.5)*size[0]*width+lean*(1-spread)
            sag=.07*abs(2*u-1)**1.5*(1-t)
            hem=.015*math.sin(u*math.tau+phase)*t**6
            y=half[1]-size[1]*(.02+.94*t+sag+hem)
            z=size[2]*(.29*math.sin(u*math.tau*1.6+.65*t+phase)+.075*math.sin(u*math.tau*3.1-t*1.7)+.06*math.sin(t*math.pi))
            p=[x,y,z]
            if cfg.get('press'):
                n=cfg['press']['normal'];distance=sum(n[i]*p[i] for i in range(3))+cfg['press']['offset']
                if distance<0:p=[p[i]-distance*n[i] for i in range(3)]
            return p
        for side in (-1,1):
            def sample(u,t):
                p=point(u,t);eps=.00001
                du=[b-a for a,b in zip(point(u-eps,t),point(u+eps,t))]
                dt=[b-a for a,b in zip(point(u,t-eps),point(u,t+eps))]
                n=norm([dt[1]*du[2]-dt[2]*du[1],dt[2]*du[0]-dt[0]*du[2],dt[0]*du[1]-dt[1]*du[0]])
                p[2]+=side*offset
                return p,[side*v for v in n]
            lo,hi=cfg.get('tRange',[0,1]);rows=2 if cfg.get('tRange') else 28
            patch(sample,[i/24 for i in range(25)],[lo+(hi-lo)*i/rows for i in range(rows+1)],-side)
    elif kind=='rod':
        a=[cfg['start'][i]*size[i] for i in range(3)];b=[cfg['end'][i]*size[i] for i in range(3)]
        axis=norm([b[i]-a[i] for i in range(3)])
        def cross(u,v):return [u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        u=norm(cross(axis,[0,1,0] if abs(axis[1])<.95 else [1,0,0]));v=cross(axis,u)
        def sample(k,angle):
            t=0 if k<2 else 1;r=0 if k in (0,3) else cfg['radius']
            radial=[u[i]*math.cos(angle)+v[i]*math.sin(angle) for i in range(3)]
            return [a[i]+(b[i]-a[i])*t+r*radial[i] for i in range(3)],([-axis[i] for i in range(3)] if k==0 else axis if k==3 else radial)
        patch(sample,list(range(4)),[i*math.tau/12 for i in range(13)])
    elif kind=='leaf':
        leaf_size=cfg.get('leafSize',size);leaf_half=[s/2 for s in leaf_size]
        tilt=cfg.get('tilt',0);ct,st=math.cos(tilt),math.sin(tilt)
        def tilt_point(p):return [p[0],p[1]*ct-p[2]*st,p[1]*st+p[2]*ct]
        for side in (-1,1):
            def sample(t,v):
                sn=math.sin(math.pi*t);cs=math.cos(math.pi*t)
                p=[leaf_half[0]*sn*v,(t-.5)*leaf_size[1],leaf_size[2]*sn*(.23-.25*v*v)+side*.0002]
                dt=[leaf_half[0]*math.pi*cs*v,leaf_size[1],leaf_size[2]*math.pi*cs*(.23-.25*v*v)]
                dv=[leaf_half[0]*sn,0,-leaf_size[2]*sn*.5*v]
                n=norm([dv[1]*dt[2]-dv[2]*dt[1],dv[2]*dt[0]-dv[0]*dt[2],dv[0]*dt[1]-dv[1]*dt[0]])
                if sn<1e-8:n=[0,0,1]
                return tilt_point(p),tilt_point([side*x for x in n])
            patch(sample,[i/8 for i in range(9)],[-1,-.5,0,.5,1])
    else:raise ValueError(kind)
    return points,normals,indices
