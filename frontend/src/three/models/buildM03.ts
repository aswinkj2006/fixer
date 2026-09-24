/**
 * Conveyor Transfer & Hydraulic Stamping Press Station
 *
 * Machine M-03. Compound geometry assembly:
 * - 6-leg structural tubular frame with diagonal cross-braces and leveling pads
 * - Belt deck with side guide rails, idler rollers, and photoelectric sensors
 * - Industrial drive motor & inline gearbox with cooling fins, terminal box, fan shroud (fail component)
 * - Hydraulic C-frame stamping press with chrome cylinder ram and yellow safety cage
 * - E-stop emergency push-button and conduit lines
 * - Moving machined billet workpieces on rubber belt
 */
import * as THREE from 'three';
import type { MachineModelParts } from './types';
import {
  createIndustrialBlue,
  createStructuralBlack,
  createBrushedSteel,
  createMotorCastIron,
  createRubberDark,
  createFailureMaterial,
  createWarningYellow,
  createPerforatedMetal,
} from '../materials';
import {
  createMesh,
  addBoltRing,
  addSafetyStripe,
  addJunctionBox,
  addVentGrille,
  addCoolingFins,
  addHoseBundle,
} from '../meshUtils';

export function buildM03(scene: THREE.Scene): MachineModelParts {
  const blue = createIndustrialBlue();
  const black = createStructuralBlack();
  const steel = createBrushedSteel();
  const motorIron = createMotorCastIron();
  const warningMat = createWarningYellow();
  const meshMat = createPerforatedMetal();
  const motorMat = createFailureMaterial(0x334155, 0.75, 0.35);

  // ═══════════════════════════════════════════════════════════════════════════
  //  1. STRUCTURAL CONVEYOR STAND & LEGS
  // ═══════════════════════════════════════════════════════════════════════════
  const standGroup = new THREE.Group();

  const legGeo = new THREE.BoxGeometry(0.1, 0.88, 0.1);
  const footPadGeo = new THREE.CylinderGeometry(0.08, 0.08, 0.03, 12);

  // 6 Upright legs with foot leveling pads
  const legPositions = [
    [-1.9, 0.44, -0.65], [-1.9, 0.44, 0.65],
    [0.0, 0.44, -0.65], [0.0, 0.44, 0.65],
    [1.9, 0.44, -0.65], [1.9, 0.44, 0.65],
  ];

  for (const [lx, ly, lz] of legPositions) {
    standGroup.add(createMesh(legGeo, black, [lx, ly, lz]));
    standGroup.add(createMesh(footPadGeo, steel, [lx, 0.015, lz]));
  }

  // Longitudinal lower tie beams
  standGroup.add(createMesh(new THREE.BoxGeometry(3.9, 0.06, 0.06), black, [0, 0.25, -0.65]));
  standGroup.add(createMesh(new THREE.BoxGeometry(3.9, 0.06, 0.06), black, [0, 0.25, 0.65]));

  // Transverse cross stretchers
  for (const x of [-1.9, 0, 1.9]) {
    standGroup.add(createMesh(new THREE.BoxGeometry(0.06, 0.06, 1.3), black, [x, 0.25, 0]));
  }

  scene.add(standGroup);

  // ═══════════════════════════════════════════════════════════════════════════
  //  2. CONVEYOR BED, ROLLERS & RUBBER BELT
  // ═══════════════════════════════════════════════════════════════════════════
  const bedGroup = new THREE.Group();
  bedGroup.position.set(0, 0.88, 0);

  // Main aluminum extrusion side channels
  bedGroup.add(createMesh(new THREE.BoxGeometry(4.4, 0.16, 0.08), black, [0, 0.08, -0.68]));
  bedGroup.add(createMesh(new THREE.BoxGeometry(4.4, 0.16, 0.08), black, [0, 0.08, 0.68]));

  // Yellow/black safety stripes along entire length of both side channels
  addSafetyStripe(bedGroup, [0, 0.08, -0.73], [4.4, 0.05, 0.01]);
  addSafetyStripe(bedGroup, [0, 0.08, 0.73], [4.4, 0.05, 0.01]);

  // Center slider bed plate
  bedGroup.add(createMesh(new THREE.BoxGeometry(4.1, 0.03, 1.26), steel, [0, 0.14, 0]));

  // Continuous black neoprene conveyor belt
  const beltMesh = createMesh(
    new THREE.BoxGeometry(4.2, 0.02, 1.2),
    createRubberDark(),
    [0, 0.16, 0],
  );
  bedGroup.add(beltMesh);

  // End head & tail pulleys (crowned steel drums)
  for (const x of [-2.1, 2.1]) {
    const pulley = createMesh(
      new THREE.CylinderGeometry(0.12, 0.12, 1.3, 20),
      steel,
      [x, 0.08, 0],
      [Math.PI / 2, 0, 0],
    );
    bedGroup.add(pulley);

    // Bearing pillow blocks
    for (const z of [-0.68, 0.68]) {
      bedGroup.add(createMesh(
        new THREE.BoxGeometry(0.14, 0.14, 0.06),
        black,
        [x, 0.08, z],
      ));
    }
  }

  // Intermediate return idler rollers underneath
  for (const x of [-1.2, 0, 1.2]) {
    bedGroup.add(createMesh(
      new THREE.CylinderGeometry(0.04, 0.04, 1.25, 16),
      steel,
      [x, -0.05, 0],
      [Math.PI / 2, 0, 0],
    ));
  }

  // Stainless steel product guide rails along belt
  bedGroup.add(createMesh(new THREE.BoxGeometry(4.2, 0.06, 0.03), steel, [0, 0.22, -0.58]));
  bedGroup.add(createMesh(new THREE.BoxGeometry(4.2, 0.06, 0.03), steel, [0, 0.22, 0.58]));

  // Optical beam sensor bracket at press entry
  const photoEye = createMesh(new THREE.BoxGeometry(0.04, 0.08, 0.04), warningMat, [-0.3, 0.26, 0.62]);
  bedGroup.add(photoEye);
  bedGroup.add(createMesh(new THREE.SphereGeometry(0.008, 8, 8), new THREE.MeshBasicMaterial({ color: 0xef4444 }), [-0.3, 0.26, 0.59]));

  scene.add(bedGroup);

  // ═══════════════════════════════════════════════════════════════════════════
  //  3. DRIVE MOTOR & GEAR REDUCER (FAULT COMPONENT)
  // ═══════════════════════════════════════════════════════════════════════════
  const motorAssembly = new THREE.Group();
  motorAssembly.position.set(-2.25, 0.96, 1.15);

  // Motor stator housing (cylindrical body with failMat)
  const motorStator = createMesh(
    new THREE.CylinderGeometry(0.32, 0.32, 0.75, 24),
    motorMat,
    [0, 0, 0],
    [0, 0, Math.PI / 2],
  );
  motorAssembly.add(motorStator);

  // Radial cooling fins around motor body
  addCoolingFins(motorAssembly, -0.28, 0.28, 0.32, 10, 0.035);

  // Motor rear fan shroud cover
  const fanShroud = createMesh(
    new THREE.CylinderGeometry(0.33, 0.33, 0.15, 20),
    black,
    [-0.42, 0, 0],
    [0, 0, Math.PI / 2],
  );
  motorAssembly.add(fanShroud);
  addVentGrille(motorAssembly, [-0.5, 0, 0], [0.22, 0.22, 0.02], 5, [0, -Math.PI / 2, 0]);

  // Front motor drive flange & gearbox
  const gearbox = createMesh(
    new THREE.BoxGeometry(0.38, 0.42, 0.42),
    motorIron,
    [0.42, -0.05, 0],
  );
  motorAssembly.add(gearbox);
  addBoltRing(motorAssembly, 0.28, 0.38, 6, 0.022, 0.04);

  // Drive chain / sprocket guard coupling to head pulley
  const chainGuard = createMesh(
    new THREE.BoxGeometry(0.48, 0.3, 0.12),
    warningMat,
    [0.35, 0, -0.32],
  );
  motorAssembly.add(chainGuard);

  // Motor terminal connection box on top
  const terminalBox = createMesh(
    new THREE.BoxGeometry(0.24, 0.18, 0.2),
    black,
    [0, 0.36, 0],
  );
  motorAssembly.add(terminalBox);

  scene.add(motorAssembly);

  // Power conduit running to electrical junction
  addHoseBundle(scene, [
    new THREE.Vector3(-2.25, 1.34, 1.15),
    new THREE.Vector3(-2.1, 1.55, 0.9),
    new THREE.Vector3(-1.7, 1.5, 0.72),
  ], 0.016);
  addJunctionBox(scene, [-1.6, 1.15, 0.72]);

  // ═══════════════════════════════════════════════════════════════════════════
  //  4. OVERHEAD HYDRAULIC STAMPING PRESS
  // ═══════════════════════════════════════════════════════════════════════════
  const pressStation = new THREE.Group();
  pressStation.position.set(0.4, 0.88, 0);

  // Twin massive chromed tie columns
  const columnGeo = new THREE.CylinderGeometry(0.09, 0.09, 2.1, 18);
  pressStation.add(createMesh(columnGeo, steel, [0, 1.05, -0.72]));
  pressStation.add(createMesh(columnGeo, steel, [0, 1.05, 0.72]));

  // Upper heavy crosshead crown (Industrial Blue)
  const crown = createMesh(
    new THREE.BoxGeometry(0.65, 0.45, 1.7),
    blue,
    [0, 2.05, 0],
  );
  pressStation.add(crown);

  // Top hydraulic manifold block & valve
  pressStation.add(createMesh(new THREE.BoxGeometry(0.3, 0.25, 0.35), black, [0, 2.38, 0]));
  pressStation.add(createMesh(new THREE.CylinderGeometry(0.03, 0.03, 0.15, 12), steel, [0, 2.55, 0]));

  // Main hydraulic cylinder barrel
  const cylinderBarrel = createMesh(
    new THREE.CylinderGeometry(0.18, 0.18, 0.75, 20),
    black,
    [0, 1.6, 0],
  );
  pressStation.add(cylinderBarrel);

  // Reciprocating chromed piston ram
  const pistonRam = createMesh(
    new THREE.CylinderGeometry(0.1, 0.1, 0.8, 20),
    steel,
    [0, 1.25, 0],
  );
  pressStation.add(pistonRam);

  // Stamping tooling die block
  const stampingDie = createMesh(
    new THREE.BoxGeometry(0.45, 0.2, 0.85),
    steel,
    [0, 0.82, 0],
  );
  pressStation.add(stampingDie);

  // Yellow wire safety cage screens (left & right guarding)
  const cageL = createMesh(new THREE.BoxGeometry(0.6, 1.2, 0.02), meshMat, [0, 1.15, -0.74]);
  const cageR = createMesh(new THREE.BoxGeometry(0.6, 1.2, 0.02), meshMat, [0, 1.15, 0.74]);
  pressStation.add(cageL, cageR);

  // Emergency stop button box on press column
  const eStopGroup = new THREE.Group();
  eStopGroup.position.set(0.12, 1.2, 0.75);
  eStopGroup.add(createMesh(new THREE.BoxGeometry(0.08, 0.12, 0.06), warningMat));
  eStopGroup.add(createMesh(
    new THREE.CylinderGeometry(0.028, 0.022, 0.02, 12),
    new THREE.MeshBasicMaterial({ color: 0xef4444 }),
    [0.04, 0, 0],
    [0, 0, Math.PI / 2],
  ));
  pressStation.add(eStopGroup);

  scene.add(pressStation);

  // ═══════════════════════════════════════════════════════════════════════════
  //  5. MOVING WORKPIECES (MACHINED STEEL BILLETS)
  // ═══════════════════════════════════════════════════════════════════════════
  const beltParts: THREE.Mesh[] = [];

  for (let i = 0; i < 4; i++) {
    // Stepped flange cylinder workpiece
    const part = new THREE.Group();
    const core = createMesh(new THREE.CylinderGeometry(0.18, 0.22, 0.22, 20), steel, [0, 0.11, 0]);
    const rim = createMesh(new THREE.CylinderGeometry(0.24, 0.24, 0.04, 20), steel, [0, 0.18, 0]);
    part.add(core, rim);
    part.position.set(-1.6 + i * 1.1, 1.04, 0);

    scene.add(part);
    beltParts.push(part as unknown as THREE.Mesh);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  //  6. ANIMATION TICK & FAULT DISPATCH
  // ═══════════════════════════════════════════════════════════════════════════
  const faultLightPosition = new THREE.Vector3(-2.25, 1.0, 1.15);

  const animateTick = (t: number, fault: boolean, repairing: boolean) => {
    // Conveyor belt motion
    const speed = fault ? 0.006 : 0.022;
    for (const p of beltParts) {
      p.position.x += speed;
      if (p.position.x > 2.0) {
        p.position.x = -2.0;
      }
    }

    // Hydraulic press ram reciprocating stroke
    const pressStroke = Math.abs(Math.sin(t * 1.8)) * 0.28;
    stampingDie.position.y = 0.82 - pressStroke;
    pistonRam.position.y = 1.25 - pressStroke;

    // Stator motor failure response
    if (repairing) {
      motorMat.emissive.setHex(0x06b6d4);
      motorMat.emissiveIntensity = (Math.sin(t * 4) + 1) * 0.45;
      motorStator.position.set(0, 0, 0);
    } else if (fault) {
      motorMat.emissive.setHex(0xb91c1c);
      motorMat.emissiveIntensity = 0.95 + Math.sin(t * 18) * 0.2;
      // Stator stator shudder / phase imbalance vibration
      motorStator.position.x = (Math.random() - 0.5) * 0.04;
      motorStator.position.y = (Math.random() - 0.5) * 0.04;
    } else {
      motorMat.emissiveIntensity = 0;
      motorStator.position.set(0, 0, 0);
    }
  };

  return { failMesh: motorStator, failMat: motorMat, faultLightPosition, animateTick };
}

