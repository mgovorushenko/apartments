"""Manually read symbol centres in the lighting plan's 1630 x 1536 frame.
Proportional registration, not measured electrical setting-out. Both axes reverse.
Wall-line anchors retain the room geometry and accommodate raster distortions.
"""
X_ANCHORS=[(63,9.075),(344,7.275),(366,7.155),(558,5.925),(583,5.795),
           (620,5.565),(750,4.690),(1235,1.599915),(1494,.015)]
Z_ANCHORS=[(104,8.755),(579,5.725),(607,5.615),(837,4.175),(915,3.605),
           (1058,2.715),(1278,1.335),(1295,1.225),(1486,.015)]
SPOTS={
 'Kitchen':[(175,242),(175,274),(447,242),(447,274),(175,478),(175,510),
            (447,478),(447,510),(175,667),(175,698),(447,698)],
 'Central':[(644,698),(447,855),(447,887),(613,887),(645,887)],
 'Entry':[(447,1045),(447,1201),(447,1233),(447,1389)],
 'Laundry':[(259,1389),(290,1389)],
 'Bedroom':[(945,680),(1155,680),(1187,680),(1396,680),(945,830),(1396,830),(945,980),(1396,980)],
 'Study':[(1098,183),(1130,183),(659,293),(659,325)],
 'Bath':[(154,977),(285,977),(154,1095),(285,1095),(205,1217),(237,1217)],
}
SCONCES={'Kitchen':(554,414),'Study':(1048,578),'BedsideLeft':(1370,1054),'BedsideRight':(972,1054)}
CENTRAL=(909,343)
SUPPLIES={'entry-mirror':(267,1302),'bath-mirror':(70,1095),'kitchen-led':(90,729)}


def interpolate(value,anchors):
    for (a,b),(c,d) in zip(anchors,anchors[1:]):
        if value<=c:return b+(value-a)*(d-b)/(c-a)
    (a,b),(c,d)=anchors[-2:]
    return b+(value-a)*(d-b)/(c-a)


def position(pixel):return [interpolate(pixel[0],X_ANCHORS),interpolate(pixel[1],Z_ANCHORS)]


def inverse(x,z):
    return [interpolate(x,sorted((b,a) for a,b in X_ANCHORS)),
            interpolate(z,sorted((b,a) for a,b in Z_ANCHORS))]
