/**
 * FANUC ARC Mate 100iD — 6-Axis Welding Robot System
 *
 * Machine M-01. Compound geometry assembly:
 * - Multi-tier cast base with mounting lugs and anchor bolts
 * - J1 turret with motor housing, cooling fins, and connector ports
 * - J2 cycloidal speed reducer with bolt flanges (fail component)
 * - Ribbed upper arm casting with conduit guides
 * - J3 elbow with hollow wrist drive motors
 * - Articulated welding torch with gas shroud, nozzle, and contact tip
 * - Standalone red FANUC R-30iB controller cabinet with louvers and disconnect
 * - Dual-conduit flexible dress pack (green pneumatic + black power)
 * - Industrial slotted welding fixture table with clamp vise
 */
import * as THREE from 'three';
import type { MachineModelParts } from './types';
import {
  createIndustrialYellow,
  createStructuralBlack,
  createBrushedSteel,
  createWeldTorch,
  createFailureMaterial,
  createRedController,
  createWarningYellow,
} from '../materials';
import {
  createMesh,
  addBoltRing,
  addSafetyStripe,
  addVendorLabel,
  addVentGrille,
  addHoseBundle,
  addCoolingFins,
  addConnectorPort,
} from '../meshUtils';

export function buildM01(scene: THREE.Scene): MachineModelParts {
  const yellow = createIndustrialYellow();
  const black = createStructuralBlack();
  const steel = createBrushedSteel();
  const redCabinetMat = createRedController();
  const warningMat = createWarningYellow();
  const failMat = createFailureMaterial(0x334155, 0.8, 0.3);

  // ═══════════════════════════════════════════════════════════════════════════
  //  1. ROBOT BASE ASSEMBLY
  // ═══════════════════════════════════════════════════════════════════════════
  const baseGroup = new THREE.Group();

  // Bottom cast anchor plinth (octagonal/hex footprint)
  const anchorPlinth = createMesh(
    new THREE.CylinderGeometry(0.78, 0.84, 0.12, 16),
    black,
    [0, 0.06, 0],
  );
  baseGroup.add(anchorPlinth);

  // Mid pedestal column
  const midPedestal = createMesh(
    new THREE.CylinderGeometry(0.68, 0.76, 0.22, 24),
    black,
    [0, 0.23, 0],
  );
  baseGroup.add(midPedestal);

  // Ground anchor bolts (12 perimeter hex bolts)
  addBoltRing(baseGroup, 0.78, 0.12, 12, 0.026, 0.04);

  // Cable entry box on rear of base
  const cableEntry = createMesh(
    new THREE.BoxGeometry(0.28, 0.22, 0.18),
    black,
    [0, 0.22, -0.68],
  );
  baseGroup.add(cableEntry);
  addConnectorPort(baseGroup, [0.07, 0.22, -0.78], [Math.PI / 2, 0, 0], 0.022);
  addConnectorPort(baseGroup, [-0.07, 0.22, -0.78], [Math.PI / 2, 0, 0], 0.022);

  // FANUC logo plate on front
  addVendorLabel(baseGroup, [0, 0.25, 0.72], [0, 0, 0], 0.28, 0.1);

  scene.add(baseGroup);

  // ═══════════════════════════════════════════════════════════════════════════
  //  2. J1 AXIS (TURRET SWIVEL)
  // ═══════════════════════════════════════════════════════════════════════════
  const j1 = new THREE.Group();
  j1.position.y = 0.34;

  // Turret rotating base ring
  j1.add(createMesh(
    new THREE.CylinderGeometry(0.62, 0.66, 0.08, 24),
    black,
    [0, 0.04, 0],
  ));
  addBoltRing(j1, 0.63, 0.04, 16, 0.02, 0.03);

  // Turret main body shell (FANUC Yellow)
  j1.add(createMesh(
    new THREE.CylinderGeometry(0.52, 0.6, 0.44, 24),
    yellow,
    [0, 0.3, 0],
  ));

  // J1 Servo motor housing on side
  const j1Motor = createMesh(
    new THREE.CylinderGeometry(0.16, 0.16, 0.36, 16),
    black,
    [-0.42, 0.32, 0],
    [0, 0, Math.PI / 2],
  );
  j1.add(j1Motor);
  addCoolingFins(j1Motor, -0.14, 0.14, 0.16, 8, 0.025);

  // ═══════════════════════════════════════════════════════════════════════════
  //  3. J2 AXIS (SHOULDER & CYCLOIDAL REDUCER — FAULT COMPONENT)
  // ═══════════════════════════════════════════════════════════════════════════
  const j2 = new THREE.Group();
  j2.position.set(0, 0.52, 0);

  // Reducer core cylinder (fail component that glows/shakes)
  const reducer = createMesh(
    new THREE.CylinderGeometry(0.36, 0.36, 0.66, 28),
    failMat,
    [0, 0, 0],
    [0, 0, Math.PI / 2],
  );
  j2.add(reducer);

  // Reducer flange rings (left and right bearing retainers)
  const flangeGeo = new THREE.CylinderGeometry(0.39, 0.39, 0.06, 24);
  j2.add(createMesh(flangeGeo, black, [-0.28, 0, 0], [0, 0, Math.PI / 2]));
  j2.add(createMesh(flangeGeo, black, [0.28, 0, 0], [0, 0, Math.PI / 2]));

  // Reducer face bolt patterns
  addBoltRing(j2, 0.32, 0, 10, 0.022, 0.04);

  // J2 Counter-balance cylinder / spring canister behind shoulder
  const balanceCylinder = createMesh(
    new THREE.CylinderGeometry(0.12, 0.12, 0.7, 16),
    black,
    [0, 0.32, -0.32],
    [0.4, 0, 0],
  );
  j2.add(balanceCylinder);
  j2.add(createMesh(
    new THREE.CylinderGeometry(0.06, 0.06, 0.6, 16),
    steel,
    [0, 0.15, -0.22],
    [0.4, 0, 0],
  ));

  // Upper arm twin casting columns
  const armColumnGeo = new THREE.BoxGeometry(0.12, 1.35, 0.28);
  j2.add(createMesh(armColumnGeo, yellow, [-0.18, 0.75, 0]));
  j2.add(createMesh(armColumnGeo, yellow, [0.18, 0.75, 0]));

  // Upper arm center bracing block & hollow conduit channel
  j2.add(createMesh(
    new THREE.BoxGeometry(0.24, 1.25, 0.2),
    black,
    [0, 0.75, 0],
  ));

  // Arm warning label
  addVendorLabel(j2, [0.25, 0.85, 0], [0, Math.PI / 2, 0], 0.24, 0.08);

  // ═══════════════════════════════════════════════════════════════════════════
  //  4. J3 AXIS (ELBOW & FOREARM)
  // ═══════════════════════════════════════════════════════════════════════════
  const j3 = new THREE.Group();
  j3.position.set(0, 1.45, 0);

  // Elbow pivot hub
  j3.add(createMesh(
    new THREE.CylinderGeometry(0.26, 0.26, 0.52, 24),
    black,
    [0, 0, 0],
    [0, 0, Math.PI / 2],
  ));
  addBoltRing(j3, 0.22, 0, 8, 0.018, 0.03);

  // J3 Servo motor housing at elbow
  const j3Motor = createMesh(
    new THREE.CylinderGeometry(0.14, 0.14, 0.28, 16),
    black,
    [0.32, 0, 0],
    [0, 0, Math.PI / 2],
  );
  j3.add(j3Motor);

  // Forearm cast structure (slanted forward at rest)
  const forearmGroup = new THREE.Group();
  forearmGroup.position.set(0, 0.1, 0);

  const forearmMain = createMesh(
    new THREE.CylinderGeometry(0.16, 0.22, 1.25, 18),
    yellow,
    [0, 0.45, 0.45],
    [Math.PI / 4, 0, 0],
  );
  forearmGroup.add(forearmMain);

  // Forearm upper reinforcement spine
  const spine = createMesh(
    new THREE.BoxGeometry(0.08, 1.15, 0.1),
    black,
    [0, 0.48, 0.42],
    [Math.PI / 4, 0, 0],
  );
  forearmGroup.add(spine);

  // ═══════════════════════════════════════════════════════════════════════════
  //  5. WRIST ASSEMBLY & WELDING TORCH END EFFECTOR
  // ═══════════════════════════════════════════════════════════════════════════
  const wrist = new THREE.Group();
  wrist.position.set(0, 0.9, 0.9);

  // J4/J5 wrist housing
  wrist.add(createMesh(new THREE.SphereGeometry(0.2, 20, 20), steel));
  wrist.add(createMesh(
    new THREE.CylinderGeometry(0.15, 0.18, 0.22, 16),
    black,
    [0, 0.02, 0.08],
    [Math.PI / 4, 0, 0],
  ));

  // J6 tool flange plate
  const toolFlange = createMesh(
    new THREE.CylinderGeometry(0.11, 0.11, 0.04, 16),
    steel,
    [0, -0.1, 0.18],
    [Math.PI / 3, 0, 0],
  );
  wrist.add(toolFlange);

  // Welding torch swan neck barrel
  const torchNeck = createMesh(
    new THREE.CylinderGeometry(0.04, 0.05, 0.42, 16),
    steel,
    [0, -0.26, 0.32],
    [Math.PI / 2.6, 0, 0],
  );
  wrist.add(torchNeck);

  // Torch gas cup / ceramic nozzle
  const torchCup = createMesh(
    new THREE.CylinderGeometry(0.045, 0.032, 0.12, 16),
    black,
    [0, -0.42, 0.46],
    [Math.PI / 2.6, 0, 0],
  );
  wrist.add(torchCup);

  // Copper contact tip / electrode
  const torchTip = createMesh(
    new THREE.ConeGeometry(0.022, 0.1, 12),
    createWeldTorch(),
    [0, -0.48, 0.52],
    [Math.PI / 2.6, 0, 0],
  );
  wrist.add(torchTip);

  forearmGroup.add(wrist);
  j3.add(forearmGroup);
  j2.add(j3);
  j1.add(j2);
  scene.add(j1);

  // ═══════════════════════════════════════════════════════════════════════════
  //  6. FANUC R-30iB CONTROLLER CABINET (STANDALONE BESIDE ROBOT)
  // ═══════════════════════════════════════════════════════════════════════════
  const controllerGroup = new THREE.Group();
  controllerGroup.position.set(-1.6, 0, 0.6);
  controllerGroup.rotation.y = 0.35;

  // Plinth base
  controllerGroup.add(createMesh(
    new THREE.BoxGeometry(0.72, 0.1, 0.62),
    black,
    [0, 0.05, 0],
  ));

  // Main cabinet body (FANUC Red)
  const cabinetBody = createMesh(
    new THREE.BoxGeometry(0.68, 1.45, 0.58),
    redCabinetMat,
    [0, 0.82, 0],
  );
  controllerGroup.add(cabinetBody);

  // Cabinet door crease / bezel
  controllerGroup.add(createMesh(
    new THREE.BoxGeometry(0.64, 1.38, 0.02),
    black,
    [0, 0.82, 0.295],
  ));

  // Front cooling louvers
  addVentGrille(controllerGroup, [0, 1.25, 0.31], [0.45, 0.32, 0.02], 6);

  // Lower exhaust vent
  addVentGrille(controllerGroup, [0, 0.42, 0.31], [0.45, 0.22, 0.02], 4);

  // Main power disconnect rotary switch (Yellow plate + Red handle)
  controllerGroup.add(createMesh(
    new THREE.BoxGeometry(0.08, 0.08, 0.02),
    warningMat,
    [-0.2, 0.85, 0.31],
  ));
  controllerGroup.add(createMesh(
    new THREE.CylinderGeometry(0.025, 0.025, 0.04, 12),
    black,
    [-0.2, 0.85, 0.33],
    [Math.PI / 2, 0, 0],
  ));

  // Status indicator lights (Power green, fault red)
  controllerGroup.add(createMesh(
    new THREE.SphereGeometry(0.016, 8, 8),
    new THREE.MeshBasicMaterial({ color: 0x22c55e }),
    [-0.2, 0.98, 0.31],
  ));
  controllerGroup.add(createMesh(
    new THREE.SphereGeometry(0.016, 8, 8),
    new THREE.MeshBasicMaterial({ color: 0xef4444 }),
    [-0.14, 0.98, 0.31],
  ));

  // Yellow hazard warning decal on door
  addSafetyStripe(controllerGroup, [0.12, 0.85, 0.31], [0.18, 0.08, 0.01]);

  // Overhead lifting eye bolts
  const eyeBoltMat = steel;
  const eye1 = createMesh(new THREE.TorusGeometry(0.035, 0.01, 8, 16), eyeBoltMat, [-0.22, 1.58, 0]);
  eye1.rotation.y = Math.PI / 2;
  controllerGroup.add(eye1);
  const eye2 = createMesh(new THREE.TorusGeometry(0.035, 0.01, 8, 16), eyeBoltMat, [0.22, 1.58, 0]);
  eye2.rotation.y = Math.PI / 2;
  controllerGroup.add(eye2);

  scene.add(controllerGroup);

  // ═══════════════════════════════════════════════════════════════════════════
  //  7. FLEXIBLE HOSE / CABLE DRESS PACK RUNS
  // ═══════════════════════════════════════════════════════════════════════════
  // Bundle 1: Controller cabinet to robot base
  addHoseBundle(scene, [
    new THREE.Vector3(-1.3, 0.3, 0.5),
    new THREE.Vector3(-1.0, 0.08, 0.3),
    new THREE.Vector3(-0.6, 0.08, 0.0),
    new THREE.Vector3(-0.2, 0.15, -0.6),
  ], 0.022);

  // Bundle 2: Base to shoulder and upper arm
  addHoseBundle(scene, [
    new THREE.Vector3(0.48, 0.25, -0.2),
    new THREE.Vector3(0.52, 0.6, -0.1),
    new THREE.Vector3(0.42, 1.1, 0.0),
    new THREE.Vector3(0.28, 1.6, 0.2),
  ], 0.018);

  // ═══════════════════════════════════════════════════════════════════════════
  //  8. HEAVY DUTY WELDING FIXTURE TABLE & WORKPIECE
  // ═══════════════════════════════════════════════════════════════════════════
  const tableGroup = new THREE.Group();
  tableGroup.position.set(0, 0, 1.8);

  // 4 Heavy boxed legs
  const legMat = black;
  const legGeo = new THREE.BoxGeometry(0.12, 0.78, 0.12);
  tableGroup.add(createMesh(legGeo, legMat, [-0.75, 0.39, -0.5]));
  tableGroup.add(createMesh(legGeo, legMat, [0.75, 0.39, -0.5]));
  tableGroup.add(createMesh(legGeo, legMat, [-0.75, 0.39, 0.5]));
  tableGroup.add(createMesh(legGeo, legMat, [0.75, 0.39, 0.5]));

  // Lower foot leveling pads
  const footGeo = new THREE.CylinderGeometry(0.09, 0.09, 0.04, 12);
  tableGroup.add(createMesh(footGeo, steel, [-0.75, 0.02, -0.5]));
  tableGroup.add(createMesh(footGeo, steel, [0.75, 0.02, -0.5]));
  tableGroup.add(createMesh(footGeo, steel, [-0.75, 0.02, 0.5]));
  tableGroup.add(createMesh(footGeo, steel, [0.75, 0.02, 0.5]));

  // Cross-bracing frame
  tableGroup.add(createMesh(new THREE.BoxGeometry(1.45, 0.08, 0.08), legMat, [0, 0.2, -0.5]));
  tableGroup.add(createMesh(new THREE.BoxGeometry(1.45, 0.08, 0.08), legMat, [0, 0.2, 0.5]));
  tableGroup.add(createMesh(new THREE.BoxGeometry(0.08, 0.08, 0.95), legMat, [-0.75, 0.2, 0]));
  tableGroup.add(createMesh(new THREE.BoxGeometry(0.08, 0.08, 0.95), legMat, [0.75, 0.2, 0]));

  // Slotted precision steel top plate
  const tableTop = createMesh(
    new THREE.BoxGeometry(1.7, 0.08, 1.2),
    steel,
    [0, 0.82, 0],
  );
  tableGroup.add(tableTop);

  // Safety stripe along table front edge
  addSafetyStripe(tableGroup, [0, 0.82, -0.6], [1.7, 0.06, 0.02]);

  // Heavy steel toggle clamp fixture / vise
  const clampBase = createMesh(new THREE.BoxGeometry(0.3, 0.1, 0.25), black, [-0.4, 0.91, 0]);
  tableGroup.add(clampBase);
  const clampArm = createMesh(new THREE.BoxGeometry(0.06, 0.18, 0.06), steel, [-0.35, 1.02, 0]);
  tableGroup.add(clampArm);

  // Precision tubular pipe / gusset workpiece to weld
  const workpiece = createMesh(
    new THREE.CylinderGeometry(0.14, 0.14, 0.8, 20),
    steel,
    [0.1, 0.98, 0],
    [0, 0, Math.PI / 2],
  );
  tableGroup.add(workpiece);

  // Pipe flange rings on workpiece
  tableGroup.add(createMesh(
    new THREE.CylinderGeometry(0.2, 0.2, 0.04, 20),
    steel,
    [-0.2, 0.98, 0],
    [0, 0, Math.PI / 2],
  ));

  scene.add(tableGroup);

  // ═══════════════════════════════════════════════════════════════════════════
  //  9. ANIMATION TICK & FAULT DISPATCH
  // ═══════════════════════════════════════════════════════════════════════════
  const faultLightPosition = new THREE.Vector3(0, 1.25, 0);

  const animateTick = (t: number, fault: boolean, repairing: boolean) => {
    // 6-Axis coordinated motion
    j1.rotation.y = Math.sin(t * 0.8) * 0.45;
    j2.rotation.x = Math.sin(t * 1.2) * 0.25;
    j3.rotation.x = -Math.sin(t * 1.2) * 0.35;
    forearmGroup.rotation.y = Math.cos(t * 0.9) * 0.15;
    wrist.rotation.z = Math.sin(t * 2.0) * 0.5;

    // Fault / repair emissive response on J2 Cycloidal Reducer
    if (repairing) {
      failMat.emissive.setHex(0x06b6d4);
      failMat.emissiveIntensity = (Math.sin(t * 4) + 1) * 0.45;
      reducer.position.set(0, 0, 0);
    } else if (fault) {
      failMat.emissive.setHex(0xef4444);
      failMat.emissiveIntensity = 0.9 + Math.sin(t * 16) * 0.25;
      reducer.position.x = (Math.random() - 0.5) * 0.04;
      reducer.position.y = (Math.random() - 0.5) * 0.04;
    } else {
      failMat.emissiveIntensity = 0;
      reducer.position.set(0, 0, 0);
    }
  };

  return { failMesh: reducer, failMat, faultLightPosition, animateTick };
}

