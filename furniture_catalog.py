"""Selection groups and source-aware dimensions. PDF readings never overwrite geometry.

Designer PDF, sheet 8 (page 2); only clearly dimensioned axes are entered.
Review pending: replacement of prior explicit user choices, wall finish datum.
"""
import math

SOURCE = '07-08 План расстановки мебели 4.pdf · лист 8'


def build(api):
    # Longest/specific prefixes first; accessories share their parent's selection.
    specs=[
        ('study-art','Картина',('StudyArt',),0,None),
        ('memo-board','Пробковая доска',('EntryMemo',),math.pi/2,None),
        ('pet-feeding','Миски на подставке',('PetFeeding',),0,None),
        ('bath-shelves','Полочки',('BathShelf_',),math.pi/2,None),
        ('study-central','Центральный светильник кабинета',('PlanCentral_',),0,None),
        ('study-sconce','Бра кабинета',('StudySconce_',),0,None),
        ('entry-mirror','Зеркало с подсветкой в прихожей',('EntryMirror_',),0,None),
        ('bath-lighting','Общий свет ванной',('BathCeilingLight',),0,None),
        ('room-lighting','Общий свет спальни и кабинета',('RoomCeilingLight',),0,None),
        ('bath-apron','Облицованный экран ванны',('BathApron',),0,None),
        ('bath-installation-finish','Облицовка короба инсталляции',('BathInstallationTile','BathFlushButton'),math.pi/2,None),
        ('bath-towel-warmer','Вертикальный полотенцесушитель · примерка',('BathTowelWarmer','BathTowelDrape'),math.pi/2,None),
        ('kitchen-light','Бра над обеденным столом',('KitchenSconce',),math.pi/2,None),
        ('kitchen-art','Картина над диваном',('KitchenArt',),math.pi/2,None),
        ('kitchen-rug','Тканый ковёр кухни',('KitchenRug',),0,None),
        ('kitchen-decor','Декор кухни',('KitchenCoffeeDecor','KitchenTVDecor','KitchenCounterDecor','KitchenCoffeeBook','KitchenDiningFruit'),0,None),
        ('kitchen-lighting','Потолочный свет и рабочая подсветка',('KitchenCeilingLight','KitchenLED'),0,None),
        ('kitchen-backsplash','Каменный фартук кухни',('KitchenBacksplash',),0,None),
        ('light-left','Светильник над тумбой у окна',('BedsideLeft_Light',),0,None),
        ('light-right','Светильник над тумбой у шкафа',('BedsideRight_Light',),0,None),
        ('bed','Кровать',('Bed_',),0,'Кровать 1870 × 2000 мм; ширина матраса 1800 мм; борта по 35 мм'),
        ('bedside-left','Тумба у окна',('BedsideLeft',),0,'Ширина 650 мм'),
        ('bedside-right','Тумба у шкафа',('BedsideRight',),0,'Ширина 650 мм'),
        ('bedroom-wardrobe','Шкаф-купе в спальне',('BedroomWardrobe',),math.pi/2,'1700 × 600 мм в плане'),
        ('hall-wardrobe','Поперечный шкаф-купе прихожей',('HallWardrobe',),0,'1350 × 600 мм в плане'),
        ('entry-wardrobe','Продольный шкаф-купе прихожей',('EntryWardrobe',),math.pi/2,'Закрытая секция 1800 мм; рядом открытая секция 750 мм'),
        ('outdoor-bedroom','Наружная корзина кондиционера спальни',('BedroomOutdoorBasket',),math.pi/2,None),
        ('outdoor-kitchen','Наружная корзина кондиционера кухни',('KitchenOutdoorBasket',),0,None),
        ('entry-shoes','Открытая секция для верхней одежды',('EntryShoe','EntryCoat'),math.pi/2,'Длина 750 мм; наполнение обновлено по просьбе пользователя'),
        ('laundry','Шкаф постирочной',('Laundry',),math.pi/2,None),
        ('washer','Стиральная машина',('Washer',),math.pi/2,None),
        ('dryer','Сушильная машина',('Dryer',),math.pi/2,None),
        ('bath-cabinet','Пенал в ванной',('BathTallCabinet',),0,None),
        ('bath-shower-curtain','Шторка ванны',('BathCurtainRail','BathShowerCurtain'),0,None),
        ('mirror','Зеркало с подсветкой в ванной',('BathroomMirror','BathMirrorLED'),math.pi/2,None),
        ('basin','Тумба с раковиной',('Basin','BathroomVanity'),math.pi/2,'Ширина тумбы 700 мм'),
        ('toilet','Инсталляция и подвесной унитаз',('Toilet',),math.pi/2,None),
        ('shower','Душевой комплект',('Shower','BathShowerNozzle'),math.pi/2,None),
        ('bath','Ванна',('BathBase','BathWest','BathEast','BathNorth','BathSouth','BathInner','BathDrain','BathOverflow','BathApron'),0,'1800 × 750 мм в плане'),
        ('tv-console','Тумба под ТВ',('TVConsole',),math.pi/2,'Длина 1500 мм'),
        ('tv','Телевизор',('TV_',),math.pi/2,None),
        ('kitchen-ac','Кондиционер кухни',('KitchenAC',),math.pi/2,None),
        ('kitchen-sofa','Диван кухни',('KitchenSofa',),math.pi/2,'Длина 1500 мм'),
        ('table','Обеденный стол',('DiningTable','Furniture_DiningTable'),0,'Круглый, Ø900 мм'),
        ('coffee-table','Журнальный стол кухни',('Furniture_CoffeeTable',),0,None),
        ('dog-bed','Лежанка',('DogBed',),0,None),
        ('pet-feeding','Металлические миски на подставке',('PetFeeding',),0,None),
        ('entry-router','Wi-Fi роутер',('EntryRouter',),0,None),
        ('entry-panel','Распределительный щиток',('EntryElectricalPanel',),0,None),
        ('study-sofa','Диван кабинета',('StudySofa',),0,'Длина 2000 мм'),
        ('study-shelf','Стеллаж кабинета',('StudyOpenShelf','StudyShelfBook'),0,'Ширина 700 мм'),
        ('desk','Рабочий стол',('ComputerDesk','DeskLeg'),0,'1400 × 600 мм в плане; форма выемки условная'),
        ('study-pc','Системный блок',('StudyPC_',),0,'Компактный корпус: примерка 190 × 400 × 360 мм'),
        ('study-keyboard','Клавиатура',('StudyKeyboard_',),0,None),
        ('study-mouse','Мышь и коврик',('StudyMouse',),0,None),
        ('study-cables','Кабельный лоток',('StudyCable_',),0,None),
        ('study-rug','Ковёр кабинета',('StudyRug',),0,'2150 × 1250 мм · примерка'),
        ('study-blind-west','Рулонная штора у стола',('StudyBlind_StudyWest_',),math.pi/2,None),
        ('study-blind-south','Рулонная штора кабинета',('StudyBlind_StudySouth_',),0,None),
        ('monitor1','Первый монитор',('Monitor1',),0,None),
        ('monitor2','Второй монитор',('Monitor2',),0,None),
        ('study-chair','Рабочее кресло',('Furniture_Study',),0,None),
        ('piano','Пианино',('Piano',),math.pi/2,'Длина 1400 мм'),
        ('guitar','Гитара на напольной стойке',('Guitar',),math.pi/2,None),
        ('fridge','Холодильник',('Fridge',),0,None),
        ('fridge-niche','Боковины ниши холодильника',('KitchenFridgeNiche',),0,None),
        ('freezer','Нижний модуль у холодильника',('Freezer',),0,None),
        ('microwave','Микроволновая печь',('Microwave',),0,None),
        ('sink-unit','Модуль мойки',('SinkUnit','KitchenSink','KitchenTap'),math.pi/2,'600 × 600 мм в плане'),
        ('dishwasher','Модуль посудомойки',('Dishwasher',),math.pi/2,'600 × 600 мм в плане'),
        ('oven','Модуль плиты и духовки',('OvenUnit','OvenDoor','Cooktop','HobRing'),math.pi/2,'600 × 600 мм в плане'),
        ('end-unit','Крайний нижний модуль',('EndUnit',),math.pi/2,'450 × 600 мм в плане'),
        ('corner','Угловой нижний модуль',('KettleCorner','Kettle_'),math.pi/2,'600 × 600 мм в плане'),
        ('hood','Вытяжка',('Hood',),math.pi/2,None),
    ]
    for name in ('Fridge','Freezer','CornerReturn','Corner','Sink','Dishwasher','Hood','End'):
        specs.append(('upper-'+name,'Верхний шкаф: '+{'Fridge':'холодильник','Freezer':'у холодильника','CornerReturn':'угол, возврат','Corner':'угол','Sink':'мойка','Dishwasher':'посудомойка','Hood':'вытяжка','End':'крайний'}[name],('KitchenUpper'+name+'_',),0 if name in ('Fridge','Freezer','CornerReturn') else math.pi/2,None))
    for i in range(1,5):
        prefix='Furniture_DiningChair'+str(i)+'_'
        seat=next((api.resolved(e) for e in api.ELEMENTS if e['name'].startswith(prefix+'seat_')),None)
        specs.append(('chair-'+str(i),'Обеденный стул '+str(i),(prefix,),seat.get('rotation',0) if seat else 0,None))
    for name,label in [('BedroomWest','Шторы спальни'),('StudyWest','Шторы кабинета у стола'),('StudySouth','Шторы кабинета'),('KitchenSouth','Шторы кухни')]:
        specs.append(('curtain-'+name,label,('Curtain_'+name+'_',),math.pi/2 if name.endswith('West') else 0,None))
    for prefix,label in [('BedroomAC','Кондиционер спальни'),('BedroomRug','Ковёр спальни'),
                          ('BedroomRadiator','Радиатор спальни'),('StudyWestRadiator','Радиатор у стола'),
                          ('StudySouthRadiator','Радиатор кабинета'),('KitchenRadiator','Радиатор кухни')]:
        specs.append((prefix,label,(prefix,),0,None))
    for side in ('Headboard','SouthLeft','SouthRight'):
        specs.append(('art-'+side,'Картина в спальне',('BedroomArt'+side,),0,None))
    room_labels={'Kitchen':'кухня','Central':'центральная зона','Entry':'прихожая','Laundry':'постирочная','Bedroom':'спальня','Study':'кабинет','Bath':'ванная'}
    rows=getattr(api,'LIGHTING_LAYOUT',[])
    specs=[(r['id'],'Спот · '+room_labels[r['room']]+' · '+r['id'].split('-')[-1],tuple(r['elements']),0,None)
           for r in rows if r['kind']=='spot']+specs
    catalog=[]
    for ident,label,prefixes,angle,pdf in specs:
        members=[e for e in api.ELEMENTS if e['category']=='furniture' and not e.get('inspectId') and e['name'].startswith(prefixes)]
        if not members:continue
        for e in members:e['inspectId']=ident
        c,s=math.cos(angle),math.sin(angle)
        corners=[]
        nominal={'bed':'Bed_Frame_','bedside-left':'BedsideLeft_Top_','bedside-right':'BedsideRight_Top_',
                 'bath-towel-warmer':'BathTowelWarmer_',
                 'tv-console':('TVConsole_001','TVConsole_002','TVConsole_003'),
                 'bedroom-wardrobe':'BedroomWardrobeCrown_','hall-wardrobe':('HallWardrobe_001','HallWardrobeCase_'),
                 'entry-wardrobe':('EntryWardrobe_001','EntryWardrobeCase_'),'entry-shoes':('EntryShoe','EntryCoatCase_'),
                 'fridge':'Fridge_001','freezer':'FreezerBase_001','bath-cabinet':('BathTallCabinet_001','BathTallCabinetCase_'),
                 'desk':'ComputerDesk_001','kitchen-sofa':'KitchenSofa_Base_','study-sofa':'StudySofa_Base_',
                 'sink-unit':'SinkUnit_001','dishwasher':'Dishwasher_001','oven':'OvenUnit_001','end-unit':'EndUnit_001','corner':'KettleCorner_001'}
        dimension_members=[e for e in members if e['name'].startswith(nominal[ident])] if ident in nominal else [e for e in members if '_Handle_' not in e['name']]
        if ident=='bath':dimension_members += [e for e in api.ELEMENTS if e['name'].startswith('BathApronLip_')]
        for original in dimension_members or members:
            e=api.resolved(original);x,y,z=e['position'];sx,sy,sz=e['size'];a=e.get('rotation',0)
            for u in (-sx/2,sx/2):
                for v in (-sz/2,sz/2):
                    wx=x+u*math.cos(a)+v*math.sin(a);wz=z-u*math.sin(a)+v*math.cos(a)
                    for wy in (y-sy/2,y+sy/2):corners.append((wx*c-wz*s,wy,wx*s+wz*c))
        lo=[min(p[i] for p in corners) for i in range(3)]
        hi=[max(p[i] for p in corners) for i in range(3)]
        # x,z,y ordering for width × depth × height, in millimetres.
        dims=[round((hi[i]-lo[i])*1000) for i in (0,2,1)]
        # Height covers the full object, while plan dimensions exclude pulls/overhangs.
        vertical=[api.resolved(e) for e in members if ident!='bath-towel-warmer' or e['name'].startswith('BathTowelWarmer')]
        dims[2]=round(1000*(max(e['position'][1]+e['size'][1]/2 for e in vertical)-min(e['position'][1]-e['size'][1]/2 for e in vertical)))
        catalog.append(dict(id=ident,label=label,dimensionsMm=dims,pdf=pdf,source=SOURCE if pdf else None,
                            note='Ш × Г — корпус; В — габарит модели, в PDF не задана.'))
    api.FURNITURE_CATALOG=catalog
    for item in catalog:
        if item['id'].startswith('spot-'):
            row=next(r for r in rows if r['id']==item['id']);x,y,z=row['position']
            item['note']=f'По пропорциям плана освещения. Центр X={x:.3f} м, Z={z:.3f} м. Диаметр и высота прибора предварительные; это не размерная привязка для монтажа.'
        if item['id'] in ('bedroom-wardrobe','hall-wardrobe','entry-wardrobe'):
            item['note']='Два раздвижных фасада на параллельных направляющих; перехлёст 35 мм. Корпус сохранён. Профиль и система купе предварительные, движение створок не анимировано.'
        if item['id'].startswith('outdoor-'):
            item['note']='Снаружи за гранью фасада, по центру окна, верх на 50 мм ниже подоконной грани. Высота и крепление условные; согласование с фасадным проектом необходимо.'
        if item['id']=='bath-towel-warmer':
            item['note']='Три трубы: 185 × 100 × 1200 мм, низ 550 мм от чистого пола. По центру простенка. Душевые полотенца 700 × 1400 мм, присборены суммарно примерно до 470 мм по ширине. Открывание пенала ограничено сушителем; ткань условно отводится фасадом. Монтажные требования ещё не выбраны.'
        if item['id']=='bath-cabinet':
            item['note']='Полностью закрытый пенал: основной и верхний распашные фасады, петли со стороны стены. Клик по пеналу открывает/закрывает до первого препятствия. Размеры указаны в закрытом виде. Цвет дерева общий с тумбой раковины.'
        if item['id']=='fridge':
            item['note']='Условный отдельностоящий корпус шириной 600 мм в выделенном месте 700 мм. Боковины по 18 мм, боковые зазоры по 32 мм. Модель холодильника, вентиляция и открывание требуют проверки по паспорту изделия.'
