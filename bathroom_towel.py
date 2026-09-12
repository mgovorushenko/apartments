"""Centred three-post warmer and broad draped towels; not installation design."""
import math


def build(api):
    def node(prefix):return api.resolved(next(e for e in api.ELEMENTS if e['name'].startswith(prefix)))
    casing=node('DoorCasing_Bathroom_B_Right_');wall=node('Tile_BathWestLower_')
    wall_x=wall['position'][0]+wall['size'][0]/2
    casing_edge=casing['position'][2]+casing['size'][2]/2
    cabinet_front=min(api.resolved(e)['position'][2]-api.resolved(e)['size'][2]/2 for e in api.ELEMENTS if e['name'].startswith('BathTallCabinetCase_'))
    center_z=(casing_edge+cabinet_front)/2
    base=api.FINISH_SETTINGS['wet_floor']+.55
    api.MATERIALS['bath_warmer_white']=dict(color=[.96,.955,.94,1],roughness=.42,metallic=.15)
    api.MATERIALS['bath_towel_sage']=dict(color=[.48,.53,.43,1],roughness=.95,metallic=0,pattern=2)
    api.MATERIALS['bath_towel_linen']=dict(color=[.83,.80,.73,1],roughness=.95,metallic=0,pattern=2)
    for mat in ('bath_towel_linen','bath_towel_sage'):
        api.MATERIALS[mat+'_hem']={**api.MATERIALS[mat],'color':[v*.91 for v in api.MATERIALS[mat]['color'][:3]]+[1]}

    def box(name,mat,p,s,detail=None,rotation=0):
        api.add_box(name,mat,p[0],p[2],s[0],s[2],s[1],base=p[1]-s[1]/2,rotation=rotation)
        e=api.ELEMENTS[-1];e.update(position=p,size=s,rotation=rotation,noEdges=True)
        if detail:e['detail']=detail
        return e
    def rod(name,a,b,r):
        p=[(a[i]+b[i])/2 for i in range(3)];s=[abs(a[i]-b[i])+r*2 for i in range(3)]
        return box(name,'bath_warmer_white',p,s,dict(type='rod',start=[(a[i]-p[i])/s[i] for i in range(3)],end=[(b[i]-p[i])/s[i] for i in range(3)],radius=r))
    for dz in (-.075,0,.075):
        api.add_cylinder('BathTowelWarmer_Upright','bath_warmer_white',wall_x+.065,center_z+dz,.035,1.2,base=base)
        api.ELEMENTS[-1].update(noEdges=True,position=[wall_x+.065,base+.6,center_z+dz])
        rod('BathTowelWarmer_Hook',[wall_x+.067,base+1.10,center_z+dz],[wall_x+.090,base+1.10,center_z+dz],.010)
    for y in (base+.10,base+1.08):
        rod('BathTowelWarmer_Crossbar',[wall_x+.052,y,center_z-.075],[wall_x+.052,y,center_z+.075],.012)
        for dz in (-.06,.06):
            box('BathTowelWarmer_Mount','bath_warmer_white',[wall_x+.025,y,center_z+dz],[.05,.035,.035],dict(type='rounded',radius=.007))
    box('BathTowelWarmer_Control','bath_warmer_white',[wall_x+.068,base+.075,center_z+.075],[.030,.08,.027],dict(type='rounded',radius=.006))
    # Nominal bath towels 700 x 1400 mm, hanging along their length and gathered
    # to about 230 mm each in width. This is illustrative draping, not cloth physics.
    for i,(dz,h,mat) in enumerate(((-.120,1.4,'bath_towel_linen'),(.120,1.4,'bath_towel_sage'))):
        top=base+1.118
        p=[wall_x+.122,top-h/2,center_z+dz];s=[.230,h,.065]
        cfg=dict(type='towel',lean=math.copysign(.045,dz),phase=i*1.3)
        box('BathTowelDrape_'+str(i),mat,p,s,cfg,math.pi/2)
        box('BathTowelDrape_Hem'+str(i),mat+'_hem',p,s,{**cfg,'tRange':[.91,.935],'offset':.0011},math.pi/2)
