const THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js';
const GSAP_URL = 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/index.js';
const SCROLL_TRIGGER_URL = 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/ScrollTrigger.js';

const sensorInfo = {
    'air-temp': ['DHT11 · температура воздуха', 'Измерение температуры рядом с растениями.'],
    'air-humidity': ['DHT11 · влажность воздуха', 'Относительная влажность воздуха в зоне выращивания.'],
    'water-temp': ['DS18B20 · температура воды', 'Погружной датчик температуры в аквариуме.'],
    'water-level': ['Датчик уровня воды', 'Контроль уровня воды в аквариумном контуре.'],
    turbidity: ['Датчик мутности', 'Оптическое измерение прозрачности воды.'],
    ph: ['pH-зонд', 'Контроль кислотности воды в аквариуме.'],
};

const stageInfo = [
    ['Электроника', 'Контроллер, реле и соединения занимают свои места в системе.'],
    ['Датчики', 'Измерительные элементы устанавливаются в воздухе и водном контуре.'],
    ['Аквариум', 'Прозрачные панели и внутренние элементы собираются вокруг резервуара.'],
    ['Вода и жизнь', 'Вода наполняет аквариум; рыбы и аэрация входят в контур.'],
    ['Циркуляция', 'Насос, фильтр и трубки соединяют аквариум с растениями.'],
    ['Выращивание', 'Лоток, субстрат, корни и зелень образуют верхний ярус.'],
    ['Камера', 'Кронштейн и ESP32-CAM наводятся на растения.'],
    ['Система собрана', 'Все компоненты интегрированы в единую аквапонную систему.'],
];

const finalTransforms = {
    'GLASS_FRONT': [0, 1.28, 1.27],
    'GLASS_BACK': [0, 1.28, -1.27],
    'GLASS_LEFT': [-2.04, 1.28, 0],
    'GLASS_RIGHT': [2.04, 1.28, 0],
    'GLASS_BASE': [0, .08, 0],
    'WATER_VOLUME': [0, .95, 0],
    'WATER_SURFACE': [0, 1.83, 0],
    'SUBSTRATE': [0, .19, 0],
    'UNDERWATER_PLANTS': [-.42, .3, .15],
    'FISH_GROUP_A': [-.75, 1.02, .25],
    'FISH_GROUP_B': [.63, 1.26, -.28],
    'FISH_GROUP_C': [.35, .76, .36],
    'WATER_PUMP': [1.32, .48, .72],
    'FILTER': [2.58, 1.04, .42],
    'WATER_PIPES': [0, 0, 0],
    'AERATION': [.45, .55, .7],
    'GROW_CONTAINER': [0, 2.9, 0],
    'GROWING_MEDIA': [0, 3.27, 0],
    'ROOT_SYSTEM': [0, 2.65, 0],
    'GREEN_PLANTS': [0, 3.31, 0],
    'CAMERA_MOUNT': [-1.86, 0, -.62],
    'ESP32_CAM': [-.14, 5.55, -.62],
    'ESP32_BOARD': [3.18, 1.45, .15],
    'RELAY_MODULE': [3.05, .49, .43],
    'WIRES': [0, 0, 0],
    'CONNECTORS': [3.18, .94, .15],
    'AIR_DHT11': [-1.62, 3.65, 1.17],
    'WATER_DS18B20': [.92, 1.1, 1.1],
    'WATER_LEVEL': [1.7, 1.62, .8],
    'TURBIDITY': [.18, .83, 1.02],
    'PH_SENSOR': [-.57, .81, 1.03],
};

function box(THREE, parent, size, position, material, name = '') {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
    mesh.name = name;
    mesh.position.set(...position);
    parent.add(mesh);
    return mesh;
}

function tube(THREE, parent, points, radius, material, name = '') {
    const path = new THREE.CatmullRomCurve3(points.map(point => new THREE.Vector3(...point)));
    const mesh = new THREE.Mesh(new THREE.TubeGeometry(path, 32, radius, 8, false), material);
    mesh.name = name;
    parent.add(mesh);
    return mesh;
}

function cylinder(THREE, parent, radiusTop, radiusBottom, height, position, material, name = '', radialSegments = 20) {
    const mesh = new THREE.Mesh(
        new THREE.CylinderGeometry(radiusTop, radiusBottom, height, radialSegments),
        material,
    );
    mesh.name = name;
    mesh.position.set(...position);
    parent.add(mesh);
    return mesh;
}

function createFish(THREE, parent, materials, name) {
    const fish = new THREE.Group();
    fish.name = name;
    const body = new THREE.Mesh(new THREE.SphereGeometry(.22, 16, 10), materials.fish);
    body.scale.set(1.35, .68, .68);
    body.castShadow = true;
    fish.add(body);
    const tail = new THREE.Mesh(new THREE.ConeGeometry(.13, .26, 4), materials.fish);
    tail.rotation.z = Math.PI / 2;
    tail.position.x = -.3;
    fish.add(tail);
    const fin = new THREE.Mesh(new THREE.ConeGeometry(.1, .2, 4), materials.fishLight);
    fin.position.set(0, -.1, 0);
    fin.rotation.z = Math.PI;
    fish.add(fin);
    const eye = new THREE.Mesh(new THREE.SphereGeometry(.025, 8, 8), materials.ink);
    eye.position.set(.19, .035, .105);
    fish.add(eye);
    parent.add(fish);
    return fish;
}

function createPlant(THREE, parent, materials, x, z, index) {
    const plant = new THREE.Group();
    plant.name = `LEAF_CLUSTER_${String(index).padStart(2, '0')}`;
    plant.position.set(x, 0, z);
    const height = .55 + (index % 3) * .1;
    cylinder(THREE, plant, .018, .035, height, [0, height / 2, 0], materials.stem, `STEM_${index}`, 8);

    for (let leaf = 0; leaf < 5; leaf += 1) {
        const angle = leaf * 2.4 + index;
        const reach = .19 + (leaf % 2) * .07;
        const leafMesh = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), materials.leaves[leaf % materials.leaves.length]);
        leafMesh.name = `LEAF_${index}_${leaf}`;
        leafMesh.scale.set(reach, .07, .14);
        leafMesh.position.set(Math.cos(angle) * reach * .56, height * (.55 + (leaf % 3) * .12), Math.sin(angle) * reach * .56);
        leafMesh.rotation.y = -angle;
        leafMesh.rotation.z = Math.cos(angle) * .36;
        leafMesh.castShadow = true;
        plant.add(leafMesh);
    }

    parent.add(plant);
    return plant;
}

function describeUnavailable(section, error) {
    const fallback = section.querySelector('[data-scene-fallback]');
    if (fallback) fallback.hidden = false;
    console.warn('Aquaponics 3D scene could not be initialized.', error);
}

export async function initializeAquaponicsScene(section, { onSensorSelect } = {}) {
    const canvas = section.querySelector('[data-aqua-canvas]');
    if (!canvas) return;

    let THREE;
    let gsap;
    let ScrollTrigger;
    try {
        [THREE, { gsap }, { ScrollTrigger }] = await Promise.all([
            import(THREE_URL),
            import(GSAP_URL),
            import(SCROLL_TRIGGER_URL),
        ]);
    } catch (error) {
        describeUnavailable(section, error);
        return;
    }

    gsap.registerPlugin(ScrollTrigger);
    let renderer;
    try {
        renderer = new THREE.WebGLRenderer({
            canvas,
            antialias: true,
            alpha: true,
            powerPreference: 'high-performance',
        });
    } catch (error) {
        describeUnavailable(section, error);
        return;
    }

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x0a1713, .022);

    const camera = new THREE.PerspectiveCamera(36, 1, .1, 70);
    const lookTarget = new THREE.Vector3(0, 5.1, 0);
    camera.position.set(19, 16.7, 23);
    camera.lookAt(lookTarget);
    const cameraPosition = camera.position.clone();

    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.6));
    renderer.setSize(canvas.clientWidth || window.innerWidth, canvas.clientHeight || window.innerHeight, false);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.22;
    renderer.shadowMap.enabled = false;

    scene.add(new THREE.HemisphereLight(0xd6f3df, 0x183029, 2.05));
    const keyLight = new THREE.DirectionalLight(0xffedcf, 3.1);
    keyLight.position.set(-5, 9, 7);
    scene.add(keyLight);
    const rimLight = new THREE.DirectionalLight(0x8be4c2, 2.3);
    rimLight.position.set(5, 6, -6);
    scene.add(rimLight);
    const fillLight = new THREE.PointLight(0x55c5bf, 1.1, 16);
    fillLight.position.set(-3, 2.2, 3.6);
    scene.add(fillLight);

    const materials = {
        frame: new THREE.MeshStandardMaterial({ color: 0x25332f, metalness: .67, roughness: .32 }),
        darkFrame: new THREE.MeshStandardMaterial({ color: 0x15231f, metalness: .55, roughness: .4 }),
        glass: new THREE.MeshPhysicalMaterial({
            color: 0xc3f4e8,
            metalness: .08,
            roughness: .08,
            transparent: true,
            opacity: .21,
            transmission: .45,
            thickness: .28,
            side: THREE.DoubleSide,
            depthWrite: false,
        }),
        glassEdge: new THREE.MeshStandardMaterial({ color: 0x86cfc0, metalness: .48, roughness: .22 }),
        water: new THREE.MeshPhysicalMaterial({
            color: 0x35b9ba,
            metalness: .12,
            roughness: .16,
            transparent: true,
            opacity: .5,
            transmission: .16,
            thickness: .55,
            side: THREE.DoubleSide,
        }),
        waterSurface: new THREE.MeshPhysicalMaterial({
            color: 0x8debe1,
            metalness: .32,
            roughness: .16,
            transparent: true,
            opacity: .72,
        }),
        substrate: new THREE.MeshStandardMaterial({ color: 0x756348, roughness: .94 }),
        stone: new THREE.MeshStandardMaterial({ color: 0xc5ac7f, roughness: .88 }),
        leaves: [
            new THREE.MeshStandardMaterial({ color: 0x53a969, roughness: .7, side: THREE.DoubleSide }),
            new THREE.MeshStandardMaterial({ color: 0x84c66f, roughness: .72, side: THREE.DoubleSide }),
            new THREE.MeshStandardMaterial({ color: 0x3f925f, roughness: .75, side: THREE.DoubleSide }),
        ],
        stem: new THREE.MeshStandardMaterial({ color: 0x518a51, roughness: .72 }),
        roots: new THREE.MeshStandardMaterial({ color: 0xb5a179, roughness: .88 }),
        board: new THREE.MeshStandardMaterial({ color: 0x187052, metalness: .13, roughness: .56 }),
        chip: new THREE.MeshStandardMaterial({ color: 0x273333, metalness: .5, roughness: .35 }),
        gold: new THREE.MeshStandardMaterial({ color: 0xd3b96f, metalness: .75, roughness: .26 }),
        wireRed: new THREE.MeshStandardMaterial({ color: 0xd77960, metalness: .18, roughness: .42 }),
        wireYellow: new THREE.MeshStandardMaterial({ color: 0xe7c45e, metalness: .12, roughness: .42 }),
        wireBlue: new THREE.MeshStandardMaterial({ color: 0x65a9c5, metalness: .18, roughness: .4 }),
        pipe: new THREE.MeshStandardMaterial({ color: 0x9cae9c, metalness: .34, roughness: .4 }),
        flow: new THREE.MeshStandardMaterial({
            color: 0x8cf5de,
            emissive: 0x34bcab,
            emissiveIntensity: 1.35,
            transparent: true,
            opacity: .05,
        }),
        fish: new THREE.MeshStandardMaterial({ color: 0xe6a765, metalness: .12, roughness: .4 }),
        fishLight: new THREE.MeshStandardMaterial({ color: 0xf3cb8b, metalness: .08, roughness: .38 }),
        ink: new THREE.MeshStandardMaterial({ color: 0x10201e, roughness: .25 }),
        sensor: new THREE.MeshStandardMaterial({ color: 0xdbe2d5, metalness: .65, roughness: .29 }),
        sensorDark: new THREE.MeshStandardMaterial({ color: 0x283a34, metalness: .42, roughness: .4 }),
        camera: new THREE.MeshStandardMaterial({ color: 0x202c2b, metalness: .72, roughness: .24 }),
        lens: new THREE.MeshPhysicalMaterial({ color: 0x5da89f, metalness: .25, roughness: .08, clearcoat: 1 }),
        highlight: new THREE.MeshBasicMaterial({ color: 0x9bf2cc, transparent: true, opacity: .88 }),
        ground: new THREE.MeshStandardMaterial({ color: 0x0c1714, roughness: .8, metalness: .1 }),
    };

    const system = new THREE.Group();
    system.name = 'AQUAPONICS_SYSTEM';
    scene.add(system);
    const aquarium = new THREE.Group();
    aquarium.name = 'AQUARIUM';
    system.add(aquarium);
    const glassTank = new THREE.Group();
    glassTank.name = 'GLASS_TANK';
    aquarium.add(glassTank);
    const growBed = new THREE.Group();
    growBed.name = 'GROW_BED';
    system.add(growBed);
    const electronics = new THREE.Group();
    electronics.name = 'ELECTRONICS';
    system.add(electronics);
    const waterSystem = new THREE.Group();
    waterSystem.name = 'WATER_SYSTEM';
    system.add(waterSystem);
    const sensorsGroup = new THREE.Group();
    sensorsGroup.name = 'SENSORS';
    system.add(sensorsGroup);
    const cameraSystem = new THREE.Group();
    cameraSystem.name = 'CAMERA_SYSTEM';
    system.add(cameraSystem);

    const registered = new Map();
    const sensorRoots = [];

    function register(name, object, home, explode, stage, { parent = system, sensorId = null, scale = 1 } = {}) {
        object.name = name;
        object.position.set(...home);
        object.scale.setScalar(scale);
        object.userData.homePosition = new THREE.Vector3(...home);
        object.userData.homeRotation = object.rotation.clone();
        object.userData.explodedPosition = new THREE.Vector3(...explode);
        object.userData.explodedRotation = new THREE.Euler(
            name.length % 2 ? .07 : -.05,
            name.length % 3 ? -.12 : .12,
            name.length % 2 ? -.06 : .08,
        );
        object.userData.assemblyStage = stage;
        if (sensorId) {
            object.userData.sensorId = sensorId;
            sensorRoots.push(object);
        }
        parent.add(object);
        registered.set(name, object);
        object.position.copy(object.userData.explodedPosition);
        object.rotation.copy(object.userData.explodedRotation);
        return object;
    }

    function registerSensor(name, sensorId, home, explode, build) {
        const part = new THREE.Group();
        build(part);
        const arrivalRing = new THREE.Mesh(
            new THREE.TorusGeometry(.12, .012, 5, 24),
            materials.highlight.clone(),
        );
        arrivalRing.name = 'SENSOR_ARRIVAL_HIGHLIGHT';
        arrivalRing.position.y = .48;
        arrivalRing.rotation.x = Math.PI / 2;
        arrivalRing.scale.setScalar(.25);
        arrivalRing.material.opacity = 0;
        part.userData.arrivalRing = arrivalRing;
        part.add(arrivalRing);
        register(name, part, home, explode, 2, { parent: sensorsGroup, sensorId });
        return part;
    }

    const ground = new THREE.Mesh(new THREE.CircleGeometry(3.7, 64), materials.ground);
    ground.name = 'TECHNICAL_DISPLAY_PLINTH';
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -.08;
    ground.receiveShadow = true;
    system.add(ground);

    const aquariumPanelSpecs = [
        ['GLASS_FRONT', [0, 1.28, 1.27], [3.9, 2.38, .045], [0, 0, 0]],
        ['GLASS_BACK', [0, 1.28, -1.27], [3.9, 2.38, .045], [0, 0, 0]],
        ['GLASS_LEFT', [-2.04, 1.28, 0], [.045, 2.38, 2.5], [0, 0, 0]],
        ['GLASS_RIGHT', [2.04, 1.28, 0], [.045, 2.38, 2.5], [0, 0, 0]],
        ['GLASS_BASE', [0, .08, 0], [3.95, .09, 2.55], [0, 0, 0]],
    ];
    aquariumPanelSpecs.forEach(([name, home, size, offset], index) => {
        const part = new THREE.Group();
        box(THREE, part, size, offset, name === 'GLASS_BASE' ? materials.glassEdge : materials.glass, name);
        const exploded = [
            [-4.6, 2.4, 1.6],
            [4.5, 2.4, -1.1],
            [-3.1, 4.6, -.3],
            [3.3, 4.8, .5],
            [0, .25, 4.4],
        ][index];
        register(name, part, home, exploded, 3, { parent: glassTank });
    });

    const glassFrame = new THREE.Group();
    const frameCorners = [
        [-2.08, -1.31], [-2.08, 1.31], [2.08, -1.31], [2.08, 1.31],
    ];
    frameCorners.forEach(([x, z], index) => {
        tube(THREE, glassFrame, [[x, .08, z], [x, 2.92, z]], .035, materials.frame, `TANK_SUPPORT_${index + 1}`);
    });
    for (const y of [.12, 2.74]) {
        tube(THREE, glassFrame, [[-2.08, y, -1.31], [2.08, y, -1.31]], .035, materials.pipe, `TANK_CROSSBAR_FRONT_${y}`);
        tube(THREE, glassFrame, [[-2.08, y, 1.31], [2.08, y, 1.31]], .035, materials.pipe, `TANK_CROSSBAR_REAR_${y}`);
        tube(THREE, glassFrame, [[-2.08, y, -1.31], [-2.08, y, 1.31]], .035, materials.pipe, `TANK_CROSSBAR_LEFT_${y}`);
        tube(THREE, glassFrame, [[2.08, y, -1.31], [2.08, y, 1.31]], .035, materials.pipe, `TANK_CROSSBAR_RIGHT_${y}`);
    }
    register('AQUAPONICS_FRAME', glassFrame, [0, 0, 0], [0, 4.5, -3.4], 3, { parent: glassTank });

    const water = new THREE.Group();
    const waterMesh = new THREE.Mesh(new THREE.BoxGeometry(3.84, 1.78, 2.4), materials.water);
    waterMesh.position.y = 0;
    waterMesh.name = 'WATER_VOLUME_MESH';
    waterMesh.castShadow = false;
    waterMesh.receiveShadow = true;
    water.add(waterMesh);
    register('WATER_VOLUME', water, finalTransforms.WATER_VOLUME, [-3.7, 1.3, 2.9], 4, { parent: aquarium, scale: .03 });

    const waterSurface = new THREE.Group();
    const surfaceMesh = new THREE.Mesh(new THREE.PlaneGeometry(3.78, 2.34, 24, 16), materials.waterSurface);
    surfaceMesh.rotation.x = -Math.PI / 2;
    surfaceMesh.name = 'WATER_SURFACE_MESH';
    waterSurface.add(surfaceMesh);
    register('WATER_SURFACE', waterSurface, finalTransforms.WATER_SURFACE, [3.8, 4.1, -2.4], 4, { parent: aquarium, scale: .03 });

    const substrate = new THREE.Group();
    box(THREE, substrate, [3.72, .16, 2.3], [0, 0, 0], materials.substrate, 'AQUARIUM_SUBSTRATE');
    const stoneGeometry = new THREE.DodecahedronGeometry(.095, 0);
    const stones = new THREE.InstancedMesh(stoneGeometry, materials.stone, 42);
    stones.name = 'DECORATIVE_STONES_INSTANCED';
    const stoneTransform = new THREE.Object3D();
    for (let index = 0; index < 42; index += 1) {
        const x = -1.7 + ((index * 37) % 35) / 10;
        const z = -1.05 + ((index * 17) % 21) / 10;
        stoneTransform.position.set(x, .12 + (index % 3) * .025, z);
        stoneTransform.rotation.set(index * .13, index * .27, index * .17);
        const size = .55 + (index % 4) * .13;
        stoneTransform.scale.set(size, size * .72, size);
        stoneTransform.updateMatrix();
        stones.setMatrixAt(index, stoneTransform.matrix);
    }
    stones.instanceMatrix.needsUpdate = true;
    substrate.add(stones);
    register('SUBSTRATE', substrate, finalTransforms.SUBSTRATE, [-.1, -1.5, 4.2], 3, { parent: aquarium });

    const underwater = new THREE.Group();
    const underwaterStem = new THREE.MeshStandardMaterial({ color: 0x4f9764, roughness: .72, side: THREE.DoubleSide });
    for (let index = 0; index < 6; index += 1) {
        const stem = tube(
            THREE,
            underwater,
            [[-.7 + index * .21, .08, -.3], [-.72 + index * .2, .54 + (index % 3) * .16, -.32], [-.9 + index * .23, .86 + (index % 3) * .16, -.3]],
            .018,
            underwaterStem,
            `UNDERWATER_STEM_${index}`,
        );
        stem.userData.animationPhase = index * .9;
    }
    register('UNDERWATER_PLANTS', underwater, finalTransforms.UNDERWATER_PLANTS, [-2.9, .8, -3.2], 3, { parent: aquarium });

    const fishPositions = [
        ['FISH_GROUP_A', finalTransforms.FISH_GROUP_A, [4.5, 1.2, 2.7]],
        ['FISH_GROUP_B', finalTransforms.FISH_GROUP_B, [-4.3, 1.7, -2.5]],
        ['FISH_GROUP_C', finalTransforms.FISH_GROUP_C, [3.1, 3.3, 3.5]],
    ];
    const fishParts = fishPositions.map(([name, home, explode], index) => {
        const fishGroup = new THREE.Group();
        createFish(THREE, fishGroup, materials, `FISH_${String(index + 1).padStart(2, '0')}`);
        register(name, fishGroup, home, explode, 4, { parent: aquarium, scale: .28 });
        return fishGroup;
    });

    const growContainer = new THREE.Group();
    box(THREE, growContainer, [4.4, .18, 2.9], [0, 0, 0], materials.darkFrame, 'GROW_BED_BASE');
    box(THREE, growContainer, [4.4, .38, .12], [0, .25, 1.39], materials.frame, 'GROW_BED_FRONT_RIM');
    box(THREE, growContainer, [4.4, .38, .12], [0, .25, -1.39], materials.frame, 'GROW_BED_REAR_RIM');
    box(THREE, growContainer, [.12, .38, 2.68], [-2.14, .25, 0], materials.frame, 'GROW_BED_LEFT_RIM');
    box(THREE, growContainer, [.12, .38, 2.68], [2.14, .25, 0], materials.frame, 'GROW_BED_RIGHT_RIM');
    register('GROW_CONTAINER', growContainer, finalTransforms.GROW_CONTAINER, [0, 6.9, .2], 6, { parent: growBed });

    const media = new THREE.Group();
    const mediaGeometry = new THREE.IcosahedronGeometry(.09, 0);
    const mediaMaterial = new THREE.MeshStandardMaterial({ color: 0xc3ae7e, roughness: .95 });
    const mediaStones = new THREE.InstancedMesh(mediaGeometry, mediaMaterial, 70);
    mediaStones.name = 'GROWING_MEDIA_INSTANCED';
    for (let index = 0; index < 70; index += 1) {
        const x = -1.95 + ((index * 19) % 39) / 10;
        const z = -1.15 + ((index * 11) % 23) / 10;
        stoneTransform.position.set(x, (index % 3) * .035, z);
        stoneTransform.rotation.set(index * .1, index * .26, index * .17);
        stoneTransform.scale.setScalar(.6 + (index % 4) * .13);
        stoneTransform.updateMatrix();
        mediaStones.setMatrixAt(index, stoneTransform.matrix);
    }
    mediaStones.instanceMatrix.needsUpdate = true;
    media.add(mediaStones);
    register('GROWING_MEDIA', media, finalTransforms.GROWING_MEDIA, [0, 5.6, 3.2], 6, { parent: growBed, scale: .08 });

    const roots = new THREE.Group();
    for (let plant = 0; plant < 7; plant += 1) {
        const x = -1.55 + plant * .52;
        for (let rootIndex = 0; rootIndex < 4; rootIndex += 1) {
            const sway = (rootIndex - 1.5) * .085;
            tube(
                THREE,
                roots,
                [
                    [x, 0, -.75 + rootIndex * .45],
                    [x + sway, -.34, -.72 + rootIndex * .45],
                    [x - sway * 1.6, -.72 - (rootIndex % 2) * .18, -.69 + rootIndex * .45],
                    [x + sway, -1.07, -.65 + rootIndex * .45],
                ],
                .013,
                materials.roots,
                `ROOT_${plant}_${rootIndex}`,
            );
        }
    }
    register('ROOT_SYSTEM', roots, finalTransforms.ROOT_SYSTEM, [0, 4.8, -3], 6, { parent: growBed, scale: .12 });

    const plants = new THREE.Group();
    const plantGroups = [];
    for (let index = 0; index < 7; index += 1) {
        plantGroups.push(createPlant(THREE, plants, materials, -1.55 + index * .52, -.65 + (index % 2) * 1.25, index));
    }
    register('GREEN_PLANTS', plants, finalTransforms.GREEN_PLANTS, [0, 7.4, -1.3], 6, { parent: growBed, scale: .14 });

    const pump = new THREE.Group();
    box(THREE, pump, [.68, .43, .52], [0, 0, 0], materials.darkFrame, 'PUMP_HOUSING');
    const pumpRing = cylinder(THREE, pump, .18, .18, .16, [.35, .02, 0], materials.pipe, 'PUMP_OUTLET');
    pumpRing.rotation.z = Math.PI / 2;
    cylinder(THREE, pump, .23, .23, .06, [-.22, .23, 0], materials.frame, 'PUMP_CAP');
    register('WATER_PUMP', pump, finalTransforms.WATER_PUMP, [-4.6, .3, .9], 5, { parent: waterSystem });

    const filter = new THREE.Group();
    cylinder(THREE, filter, .34, .4, 1.22, [0, .12, 0], materials.darkFrame, 'FILTER_BODY', 24);
    cylinder(THREE, filter, .38, .38, .12, [0, .78, 0], materials.frame, 'FILTER_HEAD', 24);
    cylinder(THREE, filter, .4, .4, .1, [0, -.5, 0], materials.frame, 'FILTER_FOOT', 24);
    for (let band = 0; band < 3; band += 1) {
        const ring = new THREE.Mesh(new THREE.TorusGeometry(.355, .023, 6, 24), materials.pipe);
        ring.name = `FILTER_RIB_${band}`;
        ring.rotation.x = Math.PI / 2;
        ring.position.y = -.2 + band * .3;
        filter.add(ring);
    }
    register('FILTER', filter, finalTransforms.FILTER, [4.7, 2.8, -.8], 5, { parent: waterSystem });

    const pipes = new THREE.Group();
    const pipeRoutes = [
        [[1.05, .52, .72], [1.72, .52, .72], [2.06, .82, .72], [2.25, 1.7, .72], [2.25, 2.52, .72], [1.67, 2.62, .72], [1.42, 2.78, .72]],
        [[-1.6, 2.57, .95], [-2.28, 2.38, .95], [-2.48, 1.52, .95], [-2.48, .5, .95], [-1.8, .39, .95], [-1.4, .4, .95]],
        [[2.55, 1.16, .43], [2.1, 1.16, .43], [1.85, .95, .43], [1.55, .74, .43]],
    ];
    pipeRoutes.forEach((points, index) => {
        const pipeMesh = tube(THREE, pipes, points, index === 2 ? .065 : .09, materials.pipe, `WATER_PIPE_${index + 1}`);
        pipeMesh.material.side = THREE.DoubleSide;
        tube(THREE, pipes, points, index === 2 ? .034 : .045, materials.flow, `WATER_FLOW_${index + 1}`);
    });
    register('WATER_PIPES', pipes, finalTransforms.WATER_PIPES, [0, 3.8, 4.1], 5, { parent: waterSystem });

    const aeration = new THREE.Group();
    cylinder(THREE, aeration, .18, .22, .22, [0, 0, 0], materials.sensorDark, 'AIR_STONE', 16);
    tube(THREE, aeration, [[0, .1, 0], [.1, .45, -.03], [.18, .7, -.05]], .035, materials.pipe, 'AIR_HOSE');
    register('AERATION', aeration, [.52, .24, .65], [2.6, .5, 3.1], 4, { parent: waterSystem });

    const sensorBuilders = {
        'air-temp': part => {
            box(THREE, part, [.38, .34, .2], [0, 0, 0], materials.sensorDark, 'DHT11_HOUSING');
            for (let slot = 0; slot < 4; slot += 1) {
                box(THREE, part, [.055, .2, .025], [-.115 + slot * .077, .01, .115], materials.sensor, `DHT11_VENT_${slot}`);
            }
            const pin = cylinder(THREE, part, .025, .025, .28, [0, -.28, 0], materials.gold, 'DHT11_PIN');
            pin.rotation.z = Math.PI / 2;
        },
        'air-humidity': part => {
            box(THREE, part, [.34, .32, .19], [0, 0, 0], materials.sensorDark, 'HUMIDITY_HOUSING');
            for (let slot = 0; slot < 3; slot += 1) {
                box(THREE, part, [.045, .18, .025], [-.075 + slot * .075, 0, .108], materials.sensor, `HUMIDITY_VENT_${slot}`);
            }
        },
        'water-temp': part => {
            cylinder(THREE, part, .075, .075, .88, [0, -.32, 0], materials.sensor, 'DS18B20_PROBE', 16);
            cylinder(THREE, part, .11, .11, .12, [0, .15, 0], materials.sensorDark, 'DS18B20_CAP', 16);
            tube(THREE, part, [[0, .2, 0], [0, .45, .02], [.22, .56, .08]], .025, materials.wireBlue, 'DS18B20_CABLE');
        },
        'water-level': part => {
            cylinder(THREE, part, .14, .14, .16, [0, -.45, 0], materials.sensorDark, 'LEVEL_WEIGHT', 14);
            cylinder(THREE, part, .24, .21, .25, [0, -.08, 0], materials.sensor, 'LEVEL_FLOAT', 14);
            cylinder(THREE, part, .035, .035, .65, [0, .34, 0], materials.gold, 'LEVEL_ROD', 10);
            tube(THREE, part, [[0, .64, 0], [.2, .82, -.02], [.4, .9, -.06]], .023, materials.wireRed, 'LEVEL_CABLE');
        },
        turbidity: part => {
            cylinder(THREE, part, .075, .12, .65, [0, 0, 0], materials.sensorDark, 'TURBIDITY_PROBE', 16);
            const optic = new THREE.Mesh(new THREE.SphereGeometry(.1, 12, 8), materials.lens);
            optic.name = 'TURBIDITY_OPTICAL_WINDOW';
            optic.scale.z = .38;
            optic.position.set(0, -.22, .06);
            part.add(optic);
        },
        ph: part => {
            cylinder(THREE, part, .09, .12, .82, [0, 0, 0], materials.sensor, 'PH_GLASS_ELECTRODE', 16);
            cylinder(THREE, part, .13, .13, .18, [0, .47, 0], materials.sensorDark, 'PH_PROBE_CAP', 16);
            const tip = new THREE.Mesh(new THREE.SphereGeometry(.09, 12, 8), materials.lens);
            tip.name = 'PH_SENSING_TIP';
            tip.position.y = -.42;
            part.add(tip);
            tube(THREE, part, [[0, .55, 0], [.2, .77, -.03], [.38, .84, -.08]], .024, materials.wireBlue, 'PH_PROBE_CABLE');
        },
    };
    const sensorPositions = [
        ['AIR_DHT11', 'air-temp', [-1.62, 3.65, 1.17], [-5.1, 5.8, 1.4]],
        ['AIR_HUMIDITY', 'air-humidity', [-1.4, 3.66, 1.15], [5.1, 5.5, 1.4]],
        ['WATER_DS18B20', 'water-temp', [.92, 1.1, 1.1], [4.6, .8, 2.7]],
        ['WATER_LEVEL', 'water-level', [1.7, 1.62, .8], [-4.3, 2.6, 2.1]],
        ['TURBIDITY', 'turbidity', [.18, .83, 1.02], [4.1, 1.1, -2.9]],
        ['PH_SENSOR', 'ph', [-.57, .81, 1.03], [-4.2, .7, -2.6]],
    ];
    sensorPositions.forEach(([name, id, home, explode]) => registerSensor(name, id, home, explode, sensorBuilders[id]));
    const sensorParts = sensorRoots;

    const cameraMount = new THREE.Group();
    tube(THREE, cameraMount, [[0, 2.65, 0], [0, 4.1, 0], [0, 5.4, 0], [1.5, 5.4, 0]], .07, materials.frame, 'CAMERA_VERTICAL_ARM');
    tube(THREE, cameraMount, [[-1.88, 5.35, 0], [-.6, 5.4, 0], [.2, 5.4, 0], [1.55, 5.4, 0]], .055, materials.pipe, 'CAMERA_CROSS_ARM');
    const mountFoot = box(THREE, cameraMount, [.48, .12, .54], [0, 2.65, 0], materials.darkFrame, 'CAMERA_MOUNT_FOOT');
    mountFoot.rotation.y = .12;
    register('CAMERA_MOUNT', cameraMount, finalTransforms.CAMERA_MOUNT, [-4.1, 7.6, -.5], 7, { parent: cameraSystem });

    const cameraUnit = new THREE.Group();
    box(THREE, cameraUnit, [.64, .37, .39], [0, 0, 0], materials.camera, 'ESP32_CAM_BOARD');
    const cameraLens = cylinder(THREE, cameraUnit, .17, .2, .2, [0, -.015, .27], materials.lens, 'ESP32_CAM_LENS', 24);
    cameraLens.rotation.x = Math.PI / 2;
    cylinder(THREE, cameraUnit, .105, .105, .08, [0, -.015, .39], materials.ink, 'ESP32_CAM_APERTURE', 24).rotation.x = Math.PI / 2;
    box(THREE, cameraUnit, [.22, .03, .12], [0, -.205, 0], materials.board, 'ESP32_CAM_CONNECTOR');
    cameraUnit.rotation.x = .18;
    register('ESP32_CAM', cameraUnit, finalTransforms.ESP32_CAM, [0, 8.2, 1.4], 7, { parent: cameraSystem });

    const board = new THREE.Group();
    box(THREE, board, [1.35, .1, 1.5], [0, 0, 0], materials.board, 'ESP32_PCB');
    box(THREE, board, [.52, .16, .48], [-.19, .12, -.18], materials.chip, 'ESP32_MODULE');
    box(THREE, board, [.3, .09, .3], [.36, .1, .32], materials.chip, 'ESP32_CONTROLLER');
    box(THREE, board, [.31, .12, .2], [-.36, .1, .49], materials.sensor, 'ESP32_USB_PORT');
    box(THREE, board, [.18, .11, .18], [.42, .1, -.48], materials.sensorDark, 'ESP32_REGULATOR');
    for (let pin = 0; pin < 14; pin += 1) {
        const x = -.58 + (pin % 7) * .19;
        const z = pin < 7 ? -.67 : .67;
        const header = box(THREE, board, [.055, .14, .055], [x, .1, z], materials.ink, `ESP32_HEADER_${pin}`);
        box(THREE, board, [.035, .17, .035], [x, .23, z], materials.gold, `ESP32_PIN_${pin}`);
        header.castShadow = false;
    }
    const antenna = new THREE.Mesh(new THREE.BoxGeometry(.52, .025, .32), materials.gold);
    antenna.name = 'ESP32_ANTENNA';
    antenna.position.set(.3, .095, -.16);
    board.add(antenna);
    register('ESP32_BOARD', board, finalTransforms.ESP32_BOARD, [4.9, 4.3, 2.6], 1, { parent: electronics });

    const relay = new THREE.Group();
    box(THREE, relay, [.92, .1, .76], [0, 0, 0], materials.board, 'RELAY_PCB');
    box(THREE, relay, [.44, .31, .39], [-.11, .2, -.06], materials.chip, 'RELAY_SWITCH');
    box(THREE, relay, [.2, .16, .22], [.3, .15, .16], materials.darkFrame, 'RELAY_TERMINAL');
    for (let pin = 0; pin < 6; pin += 1) {
        box(THREE, relay, [.045, .12, .045], [-.35 + (pin % 3) * .13, .09, pin < 3 ? .32 : -.32], materials.gold, `RELAY_PIN_${pin}`);
    }
    register('RELAY_MODULE', relay, finalTransforms.RELAY_MODULE, [5.1, 2.3, -2.7], 1, { parent: electronics });

    const connectors = new THREE.Group();
    for (let pin = 0; pin < 8; pin += 1) {
        box(THREE, connectors, [.075, .16, .08], [-.3 + (pin % 4) * .2, 0, pin < 4 ? -.15 : .15], materials.gold, `CONNECTOR_${pin}`);
    }
    register('CONNECTORS', connectors, finalTransforms.CONNECTORS, [5.7, 1, .2], 1, { parent: electronics });

    const wires = new THREE.Group();
    const wirePaths = [
        [[3.18, 1.45, .2], [2.25, 1.5, 1.42], [-2.28, 1.5, 1.42], [-2.28, 3.45, 1.42], [-1.62, 3.65, 1.17]],
        [[3.18, 1.45, .2], [2.3, 1.28, 1.42], [.92, 1.1, 1.42], [.92, 1.1, 1.1]],
        [[3.18, 1.45, .2], [2.3, 1.05, 1.42], [-.57, .81, 1.42], [-.57, .81, 1.03]],
        [[3.18, 1.45, .2], [2.3, 1.62, 1.42], [1.7, 1.62, 1.42], [1.7, 1.62, .8]],
        [[3.18, 1.45, .2], [2.3, .72, 1.42], [.18, .83, 1.42], [.18, .83, 1.02]],
    ];
    wirePaths.forEach((path, index) => {
        tube(THREE, wires, path, .018, [materials.wireRed, materials.wireYellow, materials.wireBlue, materials.wireRed, materials.wireYellow][index], `SENSOR_SIGNAL_WIRE_${index + 1}`);
    });
    register('WIRES', wires, finalTransforms.WIRES, [0, 6.2, -3.8], 2, { parent: electronics });

    const bubbles = new THREE.Group();
    const bubbleGeometry = new THREE.SphereGeometry(.045, 8, 8);
    const bubbleMaterial = new THREE.MeshBasicMaterial({ color: 0xb1fff0, transparent: true, opacity: .65 });
    for (let index = 0; index < 12; index += 1) {
        const bubble = new THREE.Mesh(bubbleGeometry, bubbleMaterial);
        bubble.name = `AERATION_BUBBLE_${index}`;
        bubble.position.set(.35 + Math.sin(index * 2.1) * .13, .2 + (index % 5) * .25, .68 + Math.cos(index) * .1);
        bubble.scale.setScalar(.55 + (index % 3) * .2);
        bubbles.add(bubble);
    }
    register('AERATION_BUBBLES', bubbles, [.42, .58, .63], [3, 4, 2], 4, { parent: waterSystem, scale: .01 });

    const floorShadow = new THREE.Mesh(
        new THREE.CircleGeometry(3.3, 48),
        new THREE.MeshBasicMaterial({ color: 0x173229, transparent: true, opacity: .08, depthWrite: false }),
    );
    floorShadow.name = 'SOFT_FLOOR_SHADOW';
    floorShadow.rotation.x = -Math.PI / 2;
    floorShadow.position.set(.25, -.045, 0);
    floorShadow.scale.set(1.12, .67, 1);
    system.add(floorShadow);

    registered.forEach(object => {
        object.traverse(child => {
            if (child.material && 'emissive' in child.material) {
                child.userData.baseEmissive = child.material.emissive.clone();
                child.userData.baseEmissiveIntensity = child.material.emissiveIntensity;
            }
        });
    });

    let progress = 0;
    let selectedSensor = null;
    let destroyed = false;
    let userDragging = false;
    let downPoint = null;
    const dragState = { x: 0, y: 0 };
    const pointer = new THREE.Vector2();
    const raycaster = new THREE.Raycaster();
    const cameraTarget = lookTarget.clone();
    const rotateRoot = new THREE.Group();
    rotateRoot.name = 'ASSEMBLY_ROTATION_PIVOT';
    scene.add(rotateRoot);
    scene.remove(system);
    rotateRoot.add(system);

    function highlightSensor(id) {
        if (selectedSensor) {
            selectedSensor.traverse(child => {
                if (child.material && child.userData.baseEmissive) {
                    child.material.emissive.copy(child.userData.baseEmissive);
                    child.material.emissiveIntensity = child.userData.baseEmissiveIntensity;
                }
            });
        }
        selectedSensor = sensorRoots.find(sensor => sensor.userData.sensorId === id) || null;
        if (selectedSensor) {
            selectedSensor.traverse(child => {
                if (child.material && 'emissive' in child.material) {
                    child.material.emissive.set(0x64d9a1);
                    child.material.emissiveIntensity = .75;
                }
            });
            const [name, description] = sensorInfo[id];
            section.querySelector('[data-sensor-name]').textContent = name;
            section.querySelector('[data-sensor-description]').textContent = description;
        }
    }

    function selectSensorAt(event) {
        const bounds = canvas.getBoundingClientRect();
        pointer.set(
            ((event.clientX - bounds.left) / bounds.width) * 2 - 1,
            -((event.clientY - bounds.top) / bounds.height) * 2 + 1,
        );
        raycaster.setFromCamera(pointer, camera);
        const intersections = raycaster.intersectObjects(sensorRoots, true);
        for (const hit of intersections) {
            let object = hit.object;
            while (object && !object.userData.sensorId) object = object.parent;
            if (object?.userData.sensorId) {
                highlightSensor(object.userData.sensorId);
                onSensorSelect?.(object.userData.sensorId);
                return;
            }
        }
    }

    function onPointerDown(event) {
        downPoint = { x: event.clientX, y: event.clientY };
        userDragging = false;
        dragState.x = event.clientX;
        dragState.y = event.clientY;
    }

    function onPointerMove(event) {
        if (!userDragging && downPoint && progress >= .999 && event.pointerType === 'mouse'
            && Math.hypot(event.clientX - downPoint.x, event.clientY - downPoint.y) > 4) {
            userDragging = true;
            canvas.setPointerCapture(event.pointerId);
        }
        if (userDragging) {
            rotateRoot.rotation.y += (event.clientX - dragState.x) * .006;
            rotateRoot.rotation.x = THREE.MathUtils.clamp(
                rotateRoot.rotation.x + (event.clientY - dragState.y) * .003,
                -.24,
                .24,
            );
            dragState.x = event.clientX;
            dragState.y = event.clientY;
            return;
        }
        if (downPoint) return;
        const bounds = canvas.getBoundingClientRect();
        pointer.set(
            ((event.clientX - bounds.left) / bounds.width) * 2 - 1,
            -((event.clientY - bounds.top) / bounds.height) * 2 + 1,
        );
        raycaster.setFromCamera(pointer, camera);
        canvas.style.cursor = raycaster.intersectObjects(sensorRoots, true).length
            ? 'pointer'
            : progress >= .999 ? 'grab' : 'default';
    }

    function onPointerUp(event) {
        if (!downPoint) return;
        if (!userDragging && Math.hypot(event.clientX - downPoint.x, event.clientY - downPoint.y) < 7) {
            selectSensorAt(event);
        }
        userDragging = false;
        downPoint = null;
        canvas.style.cursor = progress >= .999 ? 'grab' : 'default';
    }

    canvas.addEventListener('pointerdown', onPointerDown);
    canvas.addEventListener('pointermove', onPointerMove);
    canvas.addEventListener('pointerup', onPointerUp);
    canvas.addEventListener('pointercancel', onPointerUp);
    const externalSensorSelect = event => highlightSensor(event.detail.id);
    window.addEventListener('aqua:sensor-select', externalSensorSelect);

    const cameraKeys = [
        { position: [19, 16.7, 23], target: [0, 5.1, 0] },
        { position: [5.8, 4.4, 8.3], target: [2.6, 1.42, 0] },
        { position: [7.2, 4.7, 9.2], target: [-.2, 2.05, 0] },
        { position: [7.8, 4.2, 9.6], target: [0, 1.35, 0] },
        { position: [7.4, 3.9, 8.8], target: [0, 1.45, 0] },
        { position: [8.3, 4.7, 9.2], target: [.7, 1.65, 0] },
        { position: [6.8, 6.7, 9.5], target: [0, 3.4, 0] },
        { position: [5.5, 6.6, 8.4], target: [-.2, 4.5, -.2] },
        { position: [8.4, 6.8, 11], target: [.25, 2.55, 0] },
    ];
    const timeline = gsap.timeline({ paused: true });
    registered.forEach(object => {
        const stage = object.userData.assemblyStage;
        const start = stage - 1;
        const home = object.userData.homePosition;
        const homeRotation = object.userData.homeRotation;
        timeline.to(object.position, {
            x: home.x,
            y: home.y,
            z: home.z,
            duration: 1,
            ease: 'power2.inOut',
        }, start);
        timeline.to(object.rotation, {
            x: homeRotation.x,
            y: homeRotation.y,
            z: homeRotation.z,
            duration: 1,
            ease: 'power2.inOut',
        }, start);
        timeline.to(object.scale, { x: 1, y: 1, z: 1, duration: 1, ease: 'power2.out' }, start);
    });

    cameraKeys.slice(1).forEach((key, index) => {
        const time = index;
        timeline.to(cameraPosition, {
            x: key.position[0],
            y: key.position[1],
            z: key.position[2],
            duration: 1,
            ease: 'sine.inOut',
        }, time);
        timeline.to(cameraTarget, {
            x: key.target[0],
            y: key.target[1],
            z: key.target[2],
            duration: 1,
            ease: 'sine.inOut',
        }, time);
    });

    sensorParts.forEach((sensor, index) => {
        const ring = sensor.userData.arrivalRing;
        const time = 1.42 + index * .055;
        timeline.to(ring.scale, { x: 1.8, y: 1.8, z: 1.8, duration: .32, ease: 'back.out(2)' }, time);
        timeline.to(ring.material, { opacity: .85, duration: .1 }, time);
        timeline.to(ring.material, { opacity: 0, duration: .24 }, time + .42);
    });

    fishParts.forEach((fish, index) => {
        timeline.to(fish.rotation, {
            z: index % 2 ? -.16 : .16,
            duration: .32,
            yoyo: true,
            repeat: 1,
            ease: 'sine.inOut',
        }, 3.42 + index * .12);
    });

    bubbles.children.forEach((bubble, index) => {
        timeline.to(bubble.position, {
            y: bubble.position.y + .42,
            duration: .72,
            ease: 'none',
        }, 3.18 + (index % 5) * .1);
    });

    const flowMaterials = [];
    pipes.traverse(object => {
        if (object.name.startsWith('WATER_FLOW_')) flowMaterials.push(object.material);
    });
    timeline.to(flowMaterials.map(material => material), {
        opacity: .85,
        duration: 1,
        ease: 'power1.inOut',
    }, 4);
    timeline.to(waterMesh.material, { opacity: .52, duration: 1, ease: 'sine.out' }, 3);
    timeline.to(waterSurface.scale, { x: 1, y: 1, z: 1, duration: 1 }, 3);
    timeline.to(bubbleMaterial, { opacity: .62, duration: 1 }, 3.3);

    const finalTitle = section.querySelector('[data-final-title]');
    timeline.to(finalTitle, { opacity: 1, y: -8, duration: .6, ease: 'power1.out' }, 7.4);
    timeline.to(section.querySelector('[data-scroll-hint]'), { opacity: .25, duration: .3 }, 7.6);

    function updateProgress(value) {
        progress = THREE.MathUtils.clamp(value, 0, 1);
        const index = Math.min(7, Math.floor(progress * 8));
        section.querySelector('[data-stage-current]').textContent = String(index + 1).padStart(2, '0');
        section.querySelector('[data-stage-name]').textContent = stageInfo[index][0];
        section.querySelector('[data-stage-description]').textContent = stageInfo[index][1];
        section.querySelector('[data-progress-bar]').style.width = `${progress * 100}%`;
        section.querySelector('[role="progressbar"]').setAttribute('aria-valuenow', String(index + 1));
        section.classList.toggle('is-complete', progress >= .999);
        section.classList.toggle('is-final-title', progress >= .91);
        finalTitle.classList.toggle('is-visible', progress >= .91);
        finalTitle.setAttribute('aria-hidden', String(progress < .91));
        section.querySelector('[data-scroll-hint]').textContent = progress >= .999
            ? 'Система собрана · перетащите модель для обзора'
            : 'Прокрутите, чтобы собрать систему';
    }

    if (reducedMotion) {
        registered.forEach(object => {
            object.position.copy(object.userData.homePosition);
            object.rotation.copy(object.userData.homeRotation);
            object.scale.setScalar(1);
        });
        cameraPosition.set(...cameraKeys[8].position);
        cameraTarget.set(...cameraKeys[8].target);
        progress = 1;
        updateProgress(1);
    } else {
        updateProgress(0);
        ScrollTrigger.create({
            trigger: section,
            animation: timeline,
            start: 'top top',
            end: () => `+=${Math.round(window.innerHeight * (window.innerWidth < 700 ? 4.6 : 5.1))}`,
            pin: true,
            scrub: 1,
            anticipatePin: 1,
            invalidateOnRefresh: true,
            onUpdate: self => {
                if (self.progress < .999) rotateRoot.rotation.set(0, 0, 0);
                updateProgress(self.progress);
            },
        });
    }

    const resizeObserver = new ResizeObserver(() => {
        const width = canvas.clientWidth;
        const height = canvas.clientHeight;
        if (!width || !height) return;
        const viewportWidth = document.documentElement.clientWidth;
        section.style.setProperty('--aqua-viewport-width', `${viewportWidth}px`);
        section.style.setProperty('--aqua-viewport-half', `${viewportWidth / 2}px`);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.6));
        renderer.setSize(width, height, false);
        ScrollTrigger.refresh();
    });
    resizeObserver.observe(section);

    let frameId = 0;
    let lastFrameTime = 0;
    function renderFrame(time) {
        if (destroyed) return;
        frameId = window.requestAnimationFrame(renderFrame);
        if (time - lastFrameTime < 28) return;
        lastFrameTime = time;
        const aspect = canvas.clientWidth / Math.max(canvas.clientHeight, 1);
        const mobileFraming = aspect < .75 ? 1.6 : aspect < 1 ? 1.3 : 1;
        camera.position.copy(cameraPosition).sub(cameraTarget).multiplyScalar(mobileFraming).add(cameraTarget);
        camera.lookAt(cameraTarget);
        renderer.render(scene, camera);
    }
    frameId = window.requestAnimationFrame(renderFrame);

    const visibilityObserver = new IntersectionObserver(([entry]) => {
        if (entry.isIntersecting && !frameId) frameId = window.requestAnimationFrame(renderFrame);
        if (!entry.isIntersecting && frameId) {
            window.cancelAnimationFrame(frameId);
            frameId = 0;
        }
    }, { threshold: 0 });
    visibilityObserver.observe(section);

    section.dataset.sceneReady = 'true';
    canvas.style.cursor = 'default';

    return () => {
        destroyed = true;
        window.cancelAnimationFrame(frameId);
        visibilityObserver.disconnect();
        resizeObserver.disconnect();
        ScrollTrigger.getAll().filter(trigger => trigger.trigger === section).forEach(trigger => trigger.kill());
        timeline.kill();
        canvas.removeEventListener('pointerdown', onPointerDown);
        canvas.removeEventListener('pointermove', onPointerMove);
        canvas.removeEventListener('pointerup', onPointerUp);
        canvas.removeEventListener('pointercancel', onPointerUp);
        window.removeEventListener('aqua:sensor-select', externalSensorSelect);
        scene.traverse(object => {
            if (object.geometry) object.geometry.dispose();
            if (object.material) {
                (Array.isArray(object.material) ? object.material : [object.material]).forEach(material => material.dispose());
            }
        });
        renderer.dispose();
    };
}
