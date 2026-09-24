/**
 * Mesh Utility Functions — createMesh, greeble helpers
 *
 * Shared by all machine model builders for consistent
 * shadow, bevel, and detail behaviour.
 */
import * as THREE from 'three';
import {
  createStructuralBlack,
  createBrushedSteel,
  createRubberDark,
  createSafetyStripeMaterial,
  createScreenPanel,
  createRedController,
  createPerforatedMetal,
  createWarningYellow,
} from './materials';

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Core mesh creator                                                        */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Create a mesh with position/rotation/shadow in one call.
 * `castShadow` and `receiveShadow` both default to TRUE so
 * every mesh participates in the shadow pipeline unless opted out.
 */
export function createMesh<G extends THREE.BufferGeometry, M extends THREE.Material | THREE.Material[]>(
  geometry: G,
  material: M,
  pos?: [number, number, number],
  rot?: [number, number, number],
  castShadow = true,
  receiveShadow = true,
): THREE.Mesh<G, M> {
  const m = new THREE.Mesh(geometry, material);
  if (pos) m.position.set(pos[0], pos[1], pos[2]);
  if (rot) m.rotation.set(rot[0], rot[1], rot[2]);
  m.castShadow = castShadow;
  m.receiveShadow = receiveShadow;
  return m;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Bolt ring around a cylindrical joint                            */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Adds a ring of small hex bolt heads around a joint.
 * Great for reducers, bearings, and flange plates.
 */
export function addBoltRing(
  parent: THREE.Object3D,
  radius: number,
  y: number,
  count: number = 8,
  boltRadius: number = 0.025,
  boltHeight: number = 0.04,
): void {
  const boltMat = createBrushedSteel();
  const boltGeo = new THREE.CylinderGeometry(boltRadius, boltRadius * 1.15, boltHeight, 6); // hex head
  for (let i = 0; i < count; i++) {
    const angle = (i / count) * Math.PI * 2;
    const bolt = createMesh(
      boltGeo,
      boltMat,
      [Math.cos(angle) * radius, y, Math.sin(angle) * radius],
    );
    parent.add(bolt);
  }
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Cable conduit run                                               */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Adds a rubber cable conduit along a path defined by Vector3 points.
 */
export function addCableConduit(
  parent: THREE.Object3D,
  points: THREE.Vector3[],
  radius: number = 0.025,
  segments: number = 8,
): void {
  if (points.length < 2) return;
  const curve = new THREE.CatmullRomCurve3(points);
  const tubeGeo = new THREE.TubeGeometry(curve, segments * points.length, radius, 6, false);
  const cable = createMesh(tubeGeo, createRubberDark());
  parent.add(cable);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Safety stripe accent                                           */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Adds a yellow/black hazard stripe strip to a surface edge.
 */
export function addSafetyStripe(
  parent: THREE.Object3D,
  position: [number, number, number],
  size: [number, number, number],
): void {
  const stripeMat = createSafetyStripeMaterial();
  const stripeGeo = new THREE.BoxGeometry(size[0], size[1], size[2]);
  const stripe = createMesh(stripeGeo, stripeMat, position);
  parent.add(stripe);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Improved Andon warning-light stack                              */
/* ═══════════════════════════════════════════════════════════════════════════ */

export interface AndonBeaconRefs {
  group: THREE.Group;
  redMat: THREE.MeshBasicMaterial;
  yellowMat: THREE.MeshBasicMaterial;
  greenMat: THREE.MeshBasicMaterial;
}

/**
 * Builds an industrial Andon beacon tower with proper lens glow materials.
 * Returns material refs for the animation loop to control colours.
 */
export function createAndonBeacon(
  position: [number, number, number] = [-1.8, 0, -1.8],
): AndonBeaconRefs {
  const group = new THREE.Group();
  group.position.set(position[0], position[1], position[2]);

  // Pole
  const poleMat = createStructuralBlack();
  const pole = createMesh(new THREE.CylinderGeometry(0.04, 0.04, 1.8, 12), poleMat, [0, 0.9, 0]);
  group.add(pole);

  // Base plate
  const basePlate = createMesh(
    new THREE.CylinderGeometry(0.12, 0.14, 0.06, 16),
    poleMat,
    [0, 0.02, 0],
  );
  group.add(basePlate);

  // Lens housings
  const housingGeo = new THREE.CylinderGeometry(0.1, 0.1, 0.04, 16);
  group.add(createMesh(housingGeo, poleMat, [0, 2.0, 0]));
  group.add(createMesh(housingGeo, poleMat, [0, 1.83, 0]));
  group.add(createMesh(housingGeo, poleMat, [0, 1.66, 0]));

  // Lens materials (controlled by animation loop)
  const redMat = new THREE.MeshBasicMaterial({ color: 0x440000 });
  const yellowMat = new THREE.MeshBasicMaterial({ color: 0x443300 });
  const greenMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });

  // Lens cylinders (slightly smaller, inset into housings)
  const lensGeo = new THREE.CylinderGeometry(0.075, 0.075, 0.12, 16);
  group.add(createMesh(lensGeo, redMat, [0, 1.95, 0]));
  group.add(createMesh(lensGeo, yellowMat, [0, 1.78, 0]));
  group.add(createMesh(lensGeo, greenMat, [0, 1.61, 0]));

  // Top cap
  group.add(createMesh(
    new THREE.CylinderGeometry(0.06, 0.1, 0.08, 16),
    poleMat,
    [0, 2.08, 0],
  ));

  return { group, redMat, yellowMat, greenMat };
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Small vendor logo / label placeholder                           */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Adds a small rectangular label/decal surface to a part.
 */
export function addVendorLabel(
  parent: THREE.Object3D,
  position: [number, number, number],
  rotation?: [number, number, number],
  width: number = 0.2,
  height: number = 0.08,
): void {
  const labelGeo = new THREE.PlaneGeometry(width, height);
  const labelMat = new THREE.MeshStandardMaterial({
    color: 0x94a3b8,
    roughness: 0.6,
    metalness: 0.3,
    emissive: new THREE.Color(0x1e293b),
    emissiveIntensity: 0.1,
  });
  const label = createMesh(labelGeo, labelMat, position, rotation, false, false);
  parent.add(label);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Junction box                                                    */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Adds a small electrical junction box with cable entry.
 */
export function addJunctionBox(
  parent: THREE.Object3D,
  position: [number, number, number],
  size: [number, number, number] = [0.15, 0.12, 0.08],
): void {
  const boxMat = createStructuralBlack();
  const box = createMesh(new THREE.BoxGeometry(size[0], size[1], size[2]), boxMat, position);
  parent.add(box);

  // Small conduit stub
  const stubGeo = new THREE.CylinderGeometry(0.015, 0.015, 0.06, 8);
  const stub = createMesh(stubGeo, createRubberDark(), [position[0], position[1] + size[1] * 0.5 + 0.03, position[2]]);
  parent.add(stub);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Ventilation Louver / Grille                                      */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Adds a ventilation grille with realistic recessed slats.
 */
export function addVentGrille(
  parent: THREE.Object3D,
  position: [number, number, number],
  size: [number, number, number] = [0.25, 0.25, 0.02],
  slatCount: number = 5,
  rotation?: [number, number, number],
): THREE.Group {
  const group = new THREE.Group();
  group.position.set(position[0], position[1], position[2]);
  if (rotation) group.rotation.set(rotation[0], rotation[1], rotation[2]);

  const frameMat = createStructuralBlack();
  const backingMat = createPerforatedMetal();

  // Recessed backplate
  const back = createMesh(new THREE.BoxGeometry(size[0], size[1], 0.005), backingMat, [0, 0, -0.005]);
  group.add(back);

  // Slats
  const slatHeight = (size[1] / slatCount) * 0.45;
  const slatGeo = new THREE.BoxGeometry(size[0] * 0.9, slatHeight, 0.012);
  const slatStep = size[1] / (slatCount + 1);
  const startY = -size[1] / 2 + slatStep;

  for (let i = 0; i < slatCount; i++) {
    const slat = createMesh(slatGeo, frameMat, [0, startY + i * slatStep, 0.006]);
    slat.rotation.x = -0.35; // angled louver slat
    group.add(slat);
  }

  parent.add(group);
  return group;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Industrial Hydraulic / Pneumatic Cylinder                        */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Adds an articulated 2-piece hydraulic cylinder (barrel + chromed rod)
 * between a base position and target position.
 */
export function addHydraulicCylinder(
  parent: THREE.Object3D,
  basePos: [number, number, number],
  targetPos: [number, number, number],
  barrelRadius: number = 0.05,
  rodRadius: number = 0.028,
): { barrel: THREE.Mesh; rod: THREE.Mesh; group: THREE.Group } {
  const group = new THREE.Group();
  const p1 = new THREE.Vector3(...basePos);
  const p2 = new THREE.Vector3(...targetPos);
  const dir = new THREE.Vector3().subVectors(p2, p1);
  const totalLength = dir.length();
  dir.normalize();

  group.position.copy(p1);
  const up = new THREE.Vector3(0, 1, 0);
  const quat = new THREE.Quaternion().setFromUnitVectors(up, dir);
  group.quaternion.copy(quat);

  const barrelLength = totalLength * 0.58;
  const rodLength = totalLength * 0.55;

  // Cylinder body
  const barrelMat = createStructuralBlack();
  const barrelGeo = new THREE.CylinderGeometry(barrelRadius, barrelRadius, barrelLength, 16);
  const barrel = createMesh(barrelGeo, barrelMat, [0, barrelLength / 2, 0]);
  group.add(barrel);

  // Cylinder cap flange
  const capGeo = new THREE.CylinderGeometry(barrelRadius * 1.15, barrelRadius * 1.15, 0.03, 16);
  group.add(createMesh(capGeo, barrelMat, [0, barrelLength, 0]));

  // Chrome rod (telescoping out)
  const rodMat = createBrushedSteel();
  const rodGeo = new THREE.CylinderGeometry(rodRadius, rodRadius, rodLength, 16);
  const rod = createMesh(rodGeo, rodMat, [0, barrelLength + rodLength / 2 - 0.05, 0]);
  group.add(rod);

  // End mounting clevis
  const clevisGeo = new THREE.BoxGeometry(barrelRadius * 1.3, 0.05, barrelRadius * 1.3);
  group.add(createMesh(clevisGeo, barrelMat, [0, 0.02, 0]));
  group.add(createMesh(clevisGeo, barrelMat, [0, totalLength, 0]));

  parent.add(group);
  return { barrel, rod, group };
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Industrial HMI Control Panel / Pendant                          */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Creates an industrial control terminal with screen, emergency stop button,
 * and tactile buttons.
 */
export function addControlPanel(
  parent: THREE.Object3D,
  position: [number, number, number],
  size: [number, number, number] = [0.36, 0.46, 0.08],
  rotation?: [number, number, number],
): THREE.Group {
  const panel = new THREE.Group();
  panel.position.set(position[0], position[1], position[2]);
  if (rotation) panel.rotation.set(rotation[0], rotation[1], rotation[2]);

  const enclosureMat = createStructuralBlack();
  const screenMat = createScreenPanel();
  const eStopRed = createRedController();
  const warningYel = createWarningYellow();
  const steelMat = createBrushedSteel();

  // Enclosure box
  const box = createMesh(new THREE.BoxGeometry(size[0], size[1], size[2]), enclosureMat);
  panel.add(box);

  // Top screen bezel inset
  const screenW = size[0] * 0.78;
  const screenH = size[1] * 0.45;
  const screenMesh = createMesh(
    new THREE.PlaneGeometry(screenW, screenH),
    screenMat,
    [0, size[1] * 0.18, size[2] * 0.5 + 0.002],
  );
  panel.add(screenMesh);

  // Screen outer bezel frame
  const bezel = createMesh(
    new THREE.BoxGeometry(screenW + 0.03, screenH + 0.03, 0.01),
    steelMat,
    [0, size[1] * 0.18, size[2] * 0.5 + 0.001],
  );
  panel.add(bezel);

  // Emergency Stop Mushroom button (lower right)
  const eStopBase = createMesh(
    new THREE.CylinderGeometry(0.025, 0.025, 0.015, 16),
    warningYel,
    [size[0] * 0.28, -size[1] * 0.22, size[2] * 0.5 + 0.01],
    [Math.PI / 2, 0, 0],
  );
  panel.add(eStopBase);

  const eStopCap = createMesh(
    new THREE.CylinderGeometry(0.035, 0.028, 0.02, 16),
    eStopRed,
    [size[0] * 0.28, -size[1] * 0.22, size[2] * 0.5 + 0.025],
    [Math.PI / 2, 0, 0],
  );
  panel.add(eStopCap);

  // Push buttons (grid on lower left)
  const btnMatGreen = new THREE.MeshStandardMaterial({ color: 0x22c55e, roughness: 0.3 });
  const btnMatBlue = new THREE.MeshStandardMaterial({ color: 0x3b82f6, roughness: 0.3 });
  const btnMatWhite = new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 0.3 });
  const btnGeo = new THREE.CylinderGeometry(0.014, 0.014, 0.012, 12);

  const btnColors = [btnMatGreen, btnMatBlue, btnMatWhite, steelMat];
  for (let row = 0; row < 2; row++) {
    for (let col = 0; col < 2; col++) {
      const idx = row * 2 + col;
      const btn = createMesh(
        btnGeo,
        btnColors[idx],
        [-size[0] * 0.28 + col * 0.06, -size[1] * 0.16 - row * 0.06, size[2] * 0.5 + 0.008],
        [Math.PI / 2, 0, 0],
      );
      panel.add(btn);
    }
  }

  parent.add(panel);
  return panel;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Door Hinge                                                      */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Adds an industrial door hinge with mounting plate and pin.
 */
export function addDoorHinge(
  parent: THREE.Object3D,
  position: [number, number, number],
  length: number = 0.12,
  radius: number = 0.014,
): THREE.Group {
  const hinge = new THREE.Group();
  hinge.position.set(position[0], position[1], position[2]);

  const mat = createBrushedSteel();
  // Barrel
  const barrel = createMesh(new THREE.CylinderGeometry(radius, radius, length, 12), mat);
  hinge.add(barrel);

  // End caps
  const capGeo = new THREE.SphereGeometry(radius * 1.05, 8, 8);
  hinge.add(createMesh(capGeo, mat, [0, length / 2, 0]));
  hinge.add(createMesh(capGeo, mat, [0, -length / 2, 0]));

  // Flange plates
  const plateGeo = new THREE.BoxGeometry(0.04, length * 0.4, 0.006);
  hinge.add(createMesh(plateGeo, mat, [-0.02, length * 0.2, 0]));
  hinge.add(createMesh(plateGeo, mat, [0.02, -length * 0.2, 0]));

  parent.add(hinge);
  return hinge;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Cable P-Clip / Clamp                                            */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Adds a metal P-clip clamping conduit to a surface.
 */
export function addCableClip(
  parent: THREE.Object3D,
  position: [number, number, number],
  rotation?: [number, number, number],
): void {
  const clipGroup = new THREE.Group();
  clipGroup.position.set(position[0], position[1], position[2]);
  if (rotation) clipGroup.rotation.set(rotation[0], rotation[1], rotation[2]);

  const mat = createBrushedSteel();
  const loop = createMesh(new THREE.TorusGeometry(0.028, 0.006, 6, 12, Math.PI), mat);
  loop.rotation.z = Math.PI / 2;
  clipGroup.add(loop);

  const foot = createMesh(new THREE.BoxGeometry(0.03, 0.006, 0.015), mat, [0.015, -0.028, 0]);
  clipGroup.add(foot);

  parent.add(clipGroup);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Circular Connector Port                                          */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Adds a knurled circular industrial electrical connector port.
 */
export function addConnectorPort(
  parent: THREE.Object3D,
  position: [number, number, number],
  rotation?: [number, number, number],
  radius: number = 0.025,
): void {
  const portGroup = new THREE.Group();
  portGroup.position.set(position[0], position[1], position[2]);
  if (rotation) portGroup.rotation.set(rotation[0], rotation[1], rotation[2]);

  const metal = createBrushedSteel();
  const inner = createStructuralBlack();

  // Knurled outer collar
  const collar = createMesh(new THREE.CylinderGeometry(radius, radius, 0.03, 16), metal);
  portGroup.add(collar);

  // Flange ring
  const flange = createMesh(new THREE.CylinderGeometry(radius * 1.35, radius * 1.35, 0.008, 16), metal, [0, -0.012, 0]);
  portGroup.add(flange);

  // Pin receptacle face
  const face = createMesh(new THREE.CylinderGeometry(radius * 0.75, radius * 0.75, 0.032, 12), inner, [0, 0.002, 0]);
  portGroup.add(face);

  parent.add(portGroup);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Motor Cooling Fins                                               */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Adds radial cooling fins around a cylindrical motor body.
 */
export function addCoolingFins(
  parent: THREE.Object3D,
  yStart: number,
  yEnd: number,
  innerRadius: number,
  finCount: number = 8,
  finDepth: number = 0.035,
  finThickness: number = 0.008,
): void {
  const finMat = createStructuralBlack();
  const length = Math.abs(yEnd - yStart);
  const midY = (yStart + yEnd) / 2;

  const finGeo = new THREE.BoxGeometry(finThickness, length, finDepth);
  for (let i = 0; i < finCount; i++) {
    const angle = (i / finCount) * Math.PI * 2;
    const r = innerRadius + finDepth / 2;
    const fin = createMesh(
      finGeo,
      finMat,
      [Math.cos(angle) * r, midY, Math.sin(angle) * r],
    );
    fin.rotation.y = -angle;
    parent.add(fin);
  }
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Greeble: Compound Hose / Cable Bundle                                     */
/* ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Creates realistic parallel multi-hose lines (e.g. pneumatic green + power black)
 * with periodic zip-tie or clamp collars along the trajectory.
 */
export function addHoseBundle(
  parent: THREE.Object3D,
  points: THREE.Vector3[],
  hoseRadius: number = 0.018,
  includeClamps: boolean = true,
): THREE.Group {
  const group = new THREE.Group();
  if (points.length < 2) return group;

  const curve1 = new THREE.CatmullRomCurve3(points);

  // Generate slightly offset path for second hose
  const points2 = points.map((p, i) => {
    const offset = new THREE.Vector3(0.025, 0.01, 0.015);
    if (i % 2 === 1) offset.multiplyScalar(0.7);
    return p.clone().add(offset);
  });
  const curve2 = new THREE.CatmullRomCurve3(points2);

  // Hose 1: Black rubber power/signal conduit
  const tube1Geo = new THREE.TubeGeometry(curve1, points.length * 10, hoseRadius, 8, false);
  const tube1 = createMesh(tube1Geo, createRubberDark());
  group.add(tube1);

  // Hose 2: Industrial green pneumatic line
  const tube2Geo = new THREE.TubeGeometry(curve2, points.length * 10, hoseRadius * 0.85, 8, false);
  const tube2 = createMesh(tube2Geo, new THREE.MeshStandardMaterial({ color: 0x16a34a, roughness: 0.65 }));
  group.add(tube2);

  // Zip-tie / clamp collars along curve
  if (includeClamps) {
    const clampMat = createStructuralBlack();
    const clampGeo = new THREE.CylinderGeometry(hoseRadius * 2.2, hoseRadius * 2.2, 0.025, 12);
    const numClamps = Math.max(2, Math.floor(points.length * 1.5));
    for (let i = 1; i < numClamps; i++) {
      const u = i / numClamps;
      const pt = curve1.getPointAt(u);
      const tangent = curve1.getTangentAt(u);
      const clamp = createMesh(clampGeo, clampMat, [pt.x + 0.01, pt.y, pt.z + 0.005]);
      clamp.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tangent);
      group.add(clamp);
    }
  }

  parent.add(group);
  return group;
}

