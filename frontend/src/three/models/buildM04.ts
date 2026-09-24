/**
 * Crane MTTS Mobile Torque Calibration Cart & Testing Station
 *
 * Machine M-04. Compound geometry assembly:
 * - Mobile cart chassis on 4 heavy-duty dual-wheel locking casters
 * - 3-tier modular cabinet with slide-out drawer stack and aluminum grab handles
 * - Lower perforated stainless steel equipment shelf
 * - Polished surface plate with precision T-slots
 * - High-precision rotary torque transducer cartridge (fail component)
 * - Articulated monitor swing-arm with digital touch terminal readout
 * - Torque reaction calibration arm with laser collimator emitter
 * - Curly coiled data cable & industrial junction port
 */
import * as THREE from 'three';
import type { MachineModelParts } from './types';
import {
  createStructuralBlack,
  createBrushedSteel,
  createGranite,
  createSealRing,
  createFailureMaterial,
  createScreenPanel,
  createLaserBeam,
  createCartSilver,
  createIndustrialBlue,
  createPerforatedMetal,
  createRubberDark,
} from '../materials';
import {
  createMesh,
  addBoltRing,
  addSafetyStripe,
  addVendorLabel,
  addConnectorPort,
  addHoseBundle,
} from '../meshUtils';

export function buildM04(scene: THREE.Scene): MachineModelParts {
  const black = createStructuralBlack();
  const steel = createBrushedSteel();
  const cartSilver = createCartSilver();
  const drawerBlue = createIndustrialBlue();
  const rubber = createRubberDark();
  const perfMat = createPerforatedMetal();
  const transMat = createFailureMaterial(0x334155, 0.9, 0.22);

  // ═══════════════════════════════════════════════════════════════════════════
  //  1. MOBILE CART CHASSIS & 4 LOCKING CASTER WHEELS
  // ═══════════════════════════════════════════════════════════════════════════
  const cartGroup = new THREE.Group();

  // 4 Dual-wheel heavy duty casters with swivel yokes
  const casterCoords: [number, number, number][] = [
    [-0.95, 0, -0.65],
    [-0.95, 0, 0.65],
    [0.95, 0, -0.65],
    [0.95, 0, 0.65],
  ];

  for (const [cx, cy, cz] of casterCoords) {
    const caster = new THREE.Group();
    caster.position.set(cx, cy + 0.12, cz);

    // Swivel bearing plate
    caster.add(createMesh(new THREE.CylinderGeometry(0.07, 0.07, 0.03, 16), steel, [0, 0.05, 0]));

    // Steel yoke bracket
    caster.add(createMesh(new THREE.BoxGeometry(0.1, 0.08, 0.1), cartSilver, [0, 0, 0]));

    // Dual rubber wheels
    const wheelGeo = new THREE.CylinderGeometry(0.09, 0.09, 0.04, 16);
    caster.add(createMesh(wheelGeo, rubber, [-0.035, -0.04, 0], [0, 0, Math.PI / 2]));
    caster.add(createMesh(wheelGeo, rubber, [0.035, -0.04, 0], [0, 0, Math.PI / 2]));

    // Foot brake lever (red)
    caster.add(createMesh(
      new THREE.BoxGeometry(0.04, 0.015, 0.06),
      new THREE.MeshBasicMaterial({ color: 0xef4444 }),
      [0, 0.01, 0.06],
      [0.3, 0, 0],
    ));

    cartGroup.add(caster);
  }

  // Tubular extruded aluminum lower cart frame
  const lowerFrame = createMesh(
    new THREE.BoxGeometry(2.1, 0.06, 1.5),
    cartSilver,
    [0, 0.22, 0],
  );
  cartGroup.add(lowerFrame);

  // Lower perforated wire tray shelf
  const lowerShelf = createMesh(
    new THREE.BoxGeometry(1.95, 0.015, 1.35),
    perfMat,
    [0, 0.25, 0],
  );
  cartGroup.add(lowerShelf);

  // 4 Main corner vertical tubular uprights
  const uprightGeo = new THREE.BoxGeometry(0.07, 0.65, 0.07);
  cartGroup.add(createMesh(uprightGeo, cartSilver, [-0.98, 0.55, -0.68]));
  cartGroup.add(createMesh(uprightGeo, cartSilver, [-0.98, 0.55, 0.68]));
  cartGroup.add(createMesh(uprightGeo, cartSilver, [0.98, 0.55, -0.68]));
  cartGroup.add(createMesh(uprightGeo, cartSilver, [0.98, 0.55, 0.68]));

  // Left & right push handles (ergonomic bent tubular steel)
  for (const sideX of [-1.08, 1.08]) {
    const handleBar = createMesh(
      new THREE.CylinderGeometry(0.022, 0.022, 1.2, 16),
      steel,
      [sideX, 0.9, 0],
      [Math.PI / 2, 0, 0],
    );
    cartGroup.add(handleBar);
    cartGroup.add(createMesh(new THREE.BoxGeometry(0.12, 0.03, 0.03), cartSilver, [sideX > 0 ? 1.02 : -1.02, 0.9, -0.5]));
    cartGroup.add(createMesh(new THREE.BoxGeometry(0.12, 0.03, 0.03), cartSilver, [sideX > 0 ? 1.02 : -1.02, 0.9, 0.5]));
  }

  // ═══════════════════════════════════════════════════════════════════════════
  //  2. MODULAR 3-DRAWER CABINET STACK (LEFT SIDE)
  // ═══════════════════════════════════════════════════════════════════════════
  const drawerCabinet = new THREE.Group();
  drawerCabinet.position.set(-0.48, 0.52, 0);

  // Cabinet outer housing shell
  drawerCabinet.add(createMesh(new THREE.BoxGeometry(0.9, 0.52, 1.3), black));

  // 3 Drawers with handles
  for (let i = 0; i < 3; i++) {
    const dy = -0.16 + i * 0.16;
    // Drawer front face (industrial blue)
    const drawerFront = createMesh(
      new THREE.BoxGeometry(0.85, 0.135, 0.02),
      drawerBlue,
      [0, dy, 0.66],
    );
    drawerCabinet.add(drawerFront);

    // Full-width brushed aluminum pull handle
    const handle = createMesh(
      new THREE.BoxGeometry(0.72, 0.022, 0.025),
      steel,
      [0, dy + 0.03, 0.68],
    );
    drawerCabinet.add(handle);
  }
  cartGroup.add(drawerCabinet);

  // Right-side open CPU / power supply bay
  const rightBay = createMesh(new THREE.BoxGeometry(0.9, 0.52, 1.3), black, [0.48, 0.52, 0]);
  cartGroup.add(rightBay);

  // ═══════════════════════════════════════════════════════════════════════════
  //  3. TOP WORK SURFACE PLATE & TOOL TRAY
  // ═══════════════════════════════════════════════════════════════════════════
  // Heavy grade precision black granite surface plate
  const surfacePlate = createMesh(
    new THREE.BoxGeometry(2.15, 0.12, 1.55),
    createGranite(),
    [0, 0.88, 0],
  );
  cartGroup.add(surfacePlate);

  // Vendor branding badge on granite face
  addVendorLabel(surfacePlate, [0, 0.88, 0.785], [0, 0, 0], 0.38, 0.08);

  // Perimeter raised edge guard lip
  addSafetyStripe(cartGroup, [0, 0.94, -0.77], [2.15, 0.03, 0.015]);
  addSafetyStripe(cartGroup, [0, 0.94, 0.77], [2.15, 0.03, 0.015]);

  scene.add(cartGroup);

  // ═══════════════════════════════════════════════════════════════════════════
  //  4. HIGH-PRECISION ROTARY TORQUE TRANSDUCER (FAULT COMPONENT)
  // ═══════════════════════════════════════════════════════════════════════════
  const transducerGroup = new THREE.Group();
  transducerGroup.position.set(-0.25, 0.94, 0);

  // Heavy steel base sub-plate with T-nut tie downs
  const subPlate = createMesh(
    new THREE.BoxGeometry(0.75, 0.08, 0.55),
    steel,
    [0, 0.04, 0],
  );
  transducerGroup.add(subPlate);
  addBoltRing(transducerGroup, 0.28, 0.08, 6, 0.02, 0.03);

  // Transducer cylindrical core housing (fail component)
  const transCore = createMesh(
    new THREE.CylinderGeometry(0.32, 0.32, 0.65, 28),
    transMat,
    [0, 0.4, 0],
    [0, 0, Math.PI / 2],
  );
  transducerGroup.add(transCore);

  // Transducer front/rear precision flange rings
  const ringGeo = new THREE.CylinderGeometry(0.34, 0.34, 0.05, 24);
  transducerGroup.add(createMesh(ringGeo, steel, [-0.28, 0.4, 0], [0, 0, Math.PI / 2]));
  transducerGroup.add(createMesh(ringGeo, steel, [0.28, 0.4, 0], [0, 0, Math.PI / 2]));

  // Flange bolt patterns
  addBoltRing(transducerGroup, 0.3, 0.4, 8, 0.02, 0.035);

  // Precision Gold-anodized seal ring (toroidal)
  const sealRing = createMesh(
    new THREE.TorusGeometry(0.33, 0.024, 16, 36),
    createSealRing(),
    [0, 0.4, 0],
    [0, Math.PI / 2, 0],
    false,
    false,
  );
  transducerGroup.add(sealRing);

  // Input torque drive shaft (center keyed shaft)
  const driveShaft = createMesh(
    new THREE.CylinderGeometry(0.09, 0.09, 0.3, 16),
    steel,
    [0.42, 0.4, 0],
    [0, 0, Math.PI / 2],
  );
  transducerGroup.add(driveShaft);

  // Transducer Mil-spec sensor cable connector port
  addConnectorPort(transducerGroup, [0, 0.68, 0.15], [0.4, 0, 0], 0.025);

  scene.add(transducerGroup);

  // Curly coiled sensor cable draped from transducer to instrument junction
  addHoseBundle(scene, [
    new THREE.Vector3(-0.25, 1.62, 0.15),
    new THREE.Vector3(-0.2, 1.5, 0.35),
    new THREE.Vector3(0.0, 1.35, 0.45),
    new THREE.Vector3(0.4, 1.25, 0.4),
    new THREE.Vector3(0.65, 1.15, 0.25),
  ], 0.012);

  // ═══════════════════════════════════════════════════════════════════════════
  //  5. CALIBRATION REACTION ARM & LASER COLLIMATOR
  // ═══════════════════════════════════════════════════════════════════════════
  const reactionArm = new THREE.Group();
  reactionArm.position.set(0.2, 1.34, 0);

  // Pivot drive socket hub
  reactionArm.add(createMesh(new THREE.CylinderGeometry(0.11, 0.11, 0.12, 16), steel, [0, 0, 0], [0, 0, Math.PI / 2]));

  // Heavy milled calibration beam arm
  const armBeam = createMesh(
    new THREE.BoxGeometry(0.08, 0.62, 0.08),
    cartSilver,
    [0, 0.32, 0],
  );
  reactionArm.add(armBeam);

  // Counterbalance weight at end of arm
  const counterWeight = createMesh(
    new THREE.CylinderGeometry(0.08, 0.08, 0.16, 16),
    steel,
    [0, 0.62, 0],
    [0, 0, Math.PI / 2],
  );
  reactionArm.add(counterWeight);

  scene.add(reactionArm);

  // Laser alignment collimator barrel
  const collimator = createMesh(
    new THREE.CylinderGeometry(0.035, 0.035, 0.16, 16),
    black,
    [-0.65, 1.34, 0],
    [0, 0, Math.PI / 2],
  );
  scene.add(collimator);

  // Green laser alignment beam
  const laserMat = createLaserBeam(0x10b981);
  const laserBeam = createMesh(
    new THREE.CylinderGeometry(0.012, 0.012, 1.6, 8),
    laserMat,
    [0.15, 1.34, 0],
    [0, 0, Math.PI / 2],
    false,
    false,
  );
  scene.add(laserBeam);

  // ═══════════════════════════════════════════════════════════════════════════
  //  6. ARTICULATED DISPLAY TERMINAL (TABLET / DIGITAL READOUT)
  // ═══════════════════════════════════════════════════════════════════════════
  const terminalArm = new THREE.Group();
  terminalArm.position.set(0.75, 0.94, -0.55);

  // Base socket mount
  terminalArm.add(createMesh(new THREE.CylinderGeometry(0.06, 0.06, 0.1, 16), black));

  // Upright riser column
  const riser = createMesh(new THREE.CylinderGeometry(0.03, 0.03, 0.65, 12), steel, [0, 0.35, 0]);
  terminalArm.add(riser);

  // Articulated elbow joint
  terminalArm.add(createMesh(new THREE.SphereGeometry(0.045, 12, 12), black, [0, 0.68, 0]));

  // Extension reach boom
  const reachBoom = createMesh(
    new THREE.CylinderGeometry(0.025, 0.025, 0.35, 12),
    steel,
    [-0.1, 0.8, 0.1],
    [0.4, 0, -0.4],
  );
  terminalArm.add(reachBoom);

  // Digital calibration touchscreen tablet
  const tablet = new THREE.Group();
  tablet.position.set(-0.2, 0.94, 0.2);
  tablet.rotation.set(-0.25, 0.6, 0.1);

  // Tablet black bezel casing
  tablet.add(createMesh(new THREE.BoxGeometry(0.55, 0.38, 0.03), black));

  // LCD glass display
  const screenMesh = createMesh(
    new THREE.PlaneGeometry(0.5, 0.33),
    createScreenPanel(),
    [0, 0, 0.018],
  );
  tablet.add(screenMesh);

  // Tablet bumper silicone corners
  for (const [bx, by] of [[-0.27, -0.18], [-0.27, 0.18], [0.27, -0.18], [0.27, 0.18]]) {
    tablet.add(createMesh(new THREE.BoxGeometry(0.04, 0.04, 0.036), rubber, [bx, by, 0]));
  }

  terminalArm.add(tablet);
  scene.add(terminalArm);

  // Accessories on granite table (calibration torque wrench socket fixture)
  const adapterRack = createMesh(new THREE.BoxGeometry(0.4, 0.04, 0.25), black, [0.65, 0.96, 0.35]);
  scene.add(adapterRack);
  for (let i = 0; i < 4; i++) {
    const socket = createMesh(new THREE.CylinderGeometry(0.025 + i * 0.005, 0.025 + i * 0.005, 0.07, 12), steel, [0.52 + i * 0.08, 1.01, 0.35]);
    scene.add(socket);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  //  7. ANIMATION TICK & FAULT DISPATCH
  // ═══════════════════════════════════════════════════════════════════════════
  const faultLightPosition = new THREE.Vector3(-0.25, 1.35, 0);

  const animateTick = (t: number, fault: boolean, repairing: boolean) => {
    // Calibration reaction arm gentle torque oscillation
    reactionArm.rotation.x = Math.sin(t * 1.4) * 0.22;

    // Laser alignment beam status
    if (fault) {
      laserMat.color.setHex(0xef4444);
      laserBeam.rotation.y = Math.sin(t * 4) * 0.08;
    } else {
      laserMat.color.setHex(0x10b981);
      laserBeam.rotation.y = 0;
    }

    // Transducer strain-gauge failure response
    if (repairing) {
      transMat.emissive.setHex(0x06b6d4);
      transMat.emissiveIntensity = (Math.sin(t * 4) + 1) * 0.45;
      transCore.position.set(0, 0.4, 0);
    } else if (fault) {
      transMat.emissive.setHex(0xf59e0b);
      transMat.emissiveIntensity = 0.9 + Math.sin(t * 16) * 0.2;
      transCore.position.y = 0.4 + (Math.random() - 0.5) * 0.035;
      transCore.position.z = (Math.random() - 0.5) * 0.035;
    } else {
      transMat.emissiveIntensity = 0;
      transCore.position.set(0, 0.4, 0);
    }
  };

  return { failMesh: transCore, failMat: transMat, faultLightPosition, animateTick };
}
