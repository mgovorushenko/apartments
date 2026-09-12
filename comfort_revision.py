"""Later user styling overrides: pet corner, relocated bowls and slim skirting."""
import math


def build(api):
    floor=api.FINISH_SETTINGS['dry_floor']
    # The old circles at the entrance were pet bowls. Replace that entire group.
    api.ELEMENTS[:]=[e for e in api.ELEMENTS if not e['name'].startswith('PetBowl')]
    for name,color in [('dog_coat',[.65,.42,.23,1]),('dog_ear',[.32,.20,.12,1]),
                       ('pet_water',[.22,.48,.60,1]),('pet_food',[.30,.17,.09,1])]:
        api.MATERIALS[name]=dict(color=color,roughness=.9,metallic=0)

    def oval(name,material,x,z,width,depth,height,base,angle=0):
        api.add_cylinder(name,material,x,z,width,height,base=base)
        e=api.ELEMENTS[-1];e['size'][2]=depth;e['rotation']=angle;e['noEdges']=True

    # Raised rim, soft inset, and a curled, resting dog in the former chair corner.
    oval('DogBedBase','bedroom_navy',.77,5.13,1.08,.76,.12,floor)
    oval('DogBedCushion','fabric_light',.77,5.13,.92,.60,.04,floor+.12)
    def rounded(name,mat,x,y,z,width,height,depth,angle=0):
        # Low-poly ellipsoid assembled from narrow, overlapping oval slices;
        # every primitive is shared by WebGL, GLB and USD exports.
        for i in range(10):
            t=-1+(i+.5)*.2
            scale=math.sqrt(1-t*t)
            oval(name,mat,x,z,width*scale,depth*scale,height/10+.001,
                 y-height/2+i*height/10,angle)
    rounded('DogBody','dog_coat',.77,floor+.285,5.12,.61,.27,.38,-.18)
    rounded('DogHindLeg','dog_coat',1.00,floor+.25,5.23,.25,.18,.21)
    rounded('DogPaw','bedroom_ivory',.59,floor+.195,5.36,.26,.07,.09,-.12)
    rounded('DogPaw','bedroom_ivory',.80,floor+.195,5.37,.22,.07,.085,.10)
    rounded('DogHead','dog_coat',.53,floor+.31,5.20,.25,.24,.24)
    rounded('DogMuzzle','bedroom_ivory',.47,floor+.28,5.33,.18,.105,.14)
    rounded('DogNose','dark',.46,floor+.30,5.39,.065,.045,.045)
    rounded('DogEar','dog_ear',.42,floor+.31,5.17,.095,.20,.16,-.2)
    rounded('DogEar','dog_ear',.64,floor+.31,5.18,.09,.19,.15,.2)
    for x in (.475,.575):rounded('DogEye','dark',x,floor+.36,5.292,.025,.025,.02)
    for i in range(7):
        a=-.6+i*.22
        rounded('DogTail','dog_coat',.94+.19*math.cos(a),floor+.23,5.08+.19*math.sin(a),.09,.09,.09)

    # Hall face beside the bedroom opening, beyond the wardrobe and door swing.
    api.add_box('PetFeedingMat','bedroom_navy',4.96,4.12,.34,.62,.006,base=floor)
    for i,z in enumerate((3.965,4.275)):
        oval('PetFeedingBowl','ceramic',4.96,z,.235,.235,.075,floor+.006)
        oval('PetFeedingRim','metal',4.96,z,.245,.245,.012,floor+.081)
        oval('PetFeedingInset','pet_water' if i==0 else 'pet_food',4.96,z,.205,.205,.008,floor+.090)
        if i:
            for j in range(8):
                a=j*math.tau/8
                oval('PetFeedingKibble','dog_coat',4.96+.06*math.cos(a),z+.06*math.sin(a),.027,.027,.012,floor+.098)

    # Follow finished dry-room faces after the PDF warp. Lintels and door
    # openings get no skirting. Tile-backed bathroom faces are excluded.
    for e in list(api.ELEMENTS):
        f=api.resolved(e);name=f['name']
        if not name.startswith(('WallFinish_','FinishBeige_')):continue
        if f['position'][1]-f['size'][1]/2>floor+.001:continue
        if name.startswith('FinishBeige_'):
            surface=f['surface'];normal=0 if surface['axis']=='x' else 2;sign=surface['sign']
        else:
            normal=0 if f['size'][0]<f['size'][2] else 2
            sign=-1 if any(s in name for s in ('East','South')) else 1
        p=list(f['position']);size=list(f['size'])
        p[normal]+=sign*(size[normal]/2+.004)
        size[normal]=.008
        api.add_box('Skirting_'+name,'door_ivory',p[0],p[2],size[0],size[2],.04,
                    base=floor,category='finish_wall')
