/**
 * Haas VF-2 Vertical Machining Center (CNC Precision Mill)
 *
 * Machine M-02. Compound geometry assembly:
 * - Rigid cast iron base frame with leveling feet and chip/coolant trough
 * - Light grey powder-coated enclosure with Haas blue side panels
 * - Dual sliding safety doors with steel handles and glass viewing windows
 * - Cantilever pendant swing-arm with Haas CNC control console (screen + keyboard + jog dial)
 * - Internal work volume: X-Y axis saddle, slotted table with vise, loc-line coolant nozzles
 * - High-speed spindle cartridge & bearing housing (fail component)
 * - Automatic Tool Changer (ATC) carousel drum on side
 * - Electrical service cabinet on rear with cooling louvers
 */
import * as THREE from 'three';
import type { MachineModelParts } from './types';
import {
  createIndustrialBlue,
  createHaasGrey,
  createStructuralBlack,
  createBrushedSteel,
  createGlassIndicator,
  createFailureMaterial,
} from '../materials';
import {
  createMesh,
  addBoltRing,
  addSafetyStripe,
  addVendorLabel,
  addVentGrille,
  addControlPanel,
} from '../meshUtils';

export function buildM02(scene: THREE.Scene): MachineModelParts {
  const haasGrey = createHaasGrey();
  const haasBlue = createIndustrialBlue();
  const black = createStructuralBlack();
  const steel = createBrushedSteel();
  const bearingMat = createFailureMaterial(0x334155, 0.85, 0.25);

  // ═══════════════════════════════════════════════════════════════════════════
  //  1. BASE CASTING & CHIP PAN
  // ═══════════════════════════════════════════════════════════════════════════
  const baseGroup = new THREE.Group();

  // Heavy cast base block
  const mainBase = createMesh(
    new THREE.BoxGeometry(3.0, 0.75, 2.6),
    black,
    [0, 0.375, 0],
  );
  baseGroup.add(mainBase);

  // 6 Machine leveling foot pads
  const footGeo = new THREE.CylinderGeometry(0.12, 0.14, 0.05, 16);
  const footCoords = [
    [-1.35, 0.025, -1.15], [0, 0.025, -1.15], [1.35, 0.025, -1.15],
    [-1.35, 0.025, 1.15], [0, 0.025, 1.15], [1.35, 0.025, 1.15],
  ];
  for (const [fx, fy, fz] of footCoords) {
    baseGroup.add(createMesh(footGeo, steel, [fx, fy, fz]));
  }

  // Front chip tray & coolant trough
  const chipTray = createMesh(
    new THREE.BoxGeometry(2.6, 0.22, 0.35),
    black,
    [0, 0.64, 1.35],
  );
  baseGroup.add(chipTray);

  // Safety stripe along chip tray lip
  addSafetyStripe(baseGroup, [0, 0.76, 1.51], [2.6, 0.04, 0.02]);

  scene.add(baseGroup);

  // ═══════════════════════════════════════════════════════════════════════════
  //  2. MAIN MACHINE ENCLOSURE
  // ═══════════════════════════════════════════════════════════════════════════
  const enclosureGroup = new THREE.Group();
  enclosureGroup.position.set(0, 0.75, 0);

  // Main enclosure lower skirt & sidewalls (Haas Off-White / Grey)
  const leftWall = createMesh(new THREE.BoxGeometry(0.2, 1.85, 2.4), haasGrey, [-1.4, 0.925, 0]);
  const rightWall = createMesh(new THREE.BoxGeometry(0.2, 1.85, 2.4), haasGrey, [1.4, 0.925, 0]);
  const backWall = createMesh(new THREE.BoxGeometry(2.8, 1.85, 0.2), haasGrey, [0, 0.925, -1.1]);
  enclosureGroup.add(leftWall, rightWall, backWall);

  // Blue decorative accent panels on sides
  enclosureGroup.add(createMesh(new THREE.BoxGeometry(0.04, 1.4, 1.8), haasBlue, [-1.51, 1.0, 0]));
  enclosureGroup.add(createMesh(new THREE.BoxGeometry(0.04, 1.4, 1.8), haasBlue, [1.51, 1.0, 0]));

  // Enclosure upper roof cap
  const roof = createMesh(new THREE.BoxGeometry(3.0, 0.15, 2.5), haasGrey, [0, 1.92, 0]);
  enclosureGroup.add(roof);

  // Front upper header panel above doors
  const header = createMesh(new THREE.BoxGeometry(2.8, 0.45, 0.15), haasGrey, [0, 1.625, 1.15]);
  enclosureGroup.add(header);

  // Haas VF-2 logo / vendor emblem on header
  addVendorLabel(enclosureGroup, [0, 1.625, 1.24], [0, 0, 0], 0.65, 0.18);

  // ═══════════════════════════════════════════════════════════════════════════
  //  3. DUAL SLIDING SAFETY DOORS WITH WINDOWS
  // ═══════════════════════════════════════════════════════════════════════════
  // Left sliding door
  const leftDoor = new THREE.Group();
  leftDoor.position.set(-0.68, 0.72, 1.16);

  const doorFrameL = createMesh(new THREE.BoxGeometry(1.32, 1.35, 0.05), haasGrey);
  leftDoor.add(doorFrameL);

  // Glass pane inset
  const glassL = createMesh(
    new THREE.BoxGeometry(1.0, 0.95, 0.03),
    createGlassIndicator(),
    [0, 0.05, 0.01],
    undefined,
    false,
    false,
  );
  leftDoor.add(glassL);

  // Black grab handle
  const handleL = createMesh(new THREE.BoxGeometry(0.04, 0.35, 0.06), black, [0.55, 0, 0.05]);
  leftDoor.add(handleL);

  enclosureGroup.add(leftDoor);

  // Right sliding door
  const rightDoor = new THREE.Group();
  rightDoor.position.set(0.68, 0.72, 1.16);

  const doorFrameR = createMesh(new THREE.BoxGeometry(1.32, 1.35, 0.05), haasGrey);
  rightDoor.add(doorFrameR);

  const glassR = createMesh(
    new THREE.BoxGeometry(1.0, 0.95, 0.03),
    createGlassIndicator(),
    [0, 0.05, 0.01],
    undefined,
    false,
    false,
  );
  rightDoor.add(glassR);

  const handleR = createMesh(new THREE.BoxGeometry(0.04, 0.35, 0.06), black, [-0.55, 0, 0.05]);
  rightDoor.add(handleR);

  enclosureGroup.add(rightDoor);

  scene.add(enclosureGroup);

  // ═══════════════════════════════════════════════════════════════════════════
  //  4. PENDANT CONTROL ARM & HAAS OPERATOR CONSOLE
  // ═══════════════════════════════════════════════════════════════════════════
  const pendantArmGroup = new THREE.Group();
  pendantArmGroup.position.set(1.45, 2.1, 0.6);

  // Arm pivot mount bracket on right wall
  pendantArmGroup.add(createMesh(new THREE.CylinderGeometry(0.08, 0.08, 0.22, 16), black));

  // Cantilever horizontal boom arm
  const boom = createMesh(
    new THREE.BoxGeometry(0.7, 0.08, 0.08),
    haasGrey,
    [0.35, 0.06, 0.15],
    [0, -0.4, 0],
  );
  pendantArmGroup.add(boom);

  // Drop pendant arm
  const dropArm = createMesh(
    new THREE.CylinderGeometry(0.04, 0.04, 0.5, 12),
    steel,
    [0.65, -0.22, 0.3],
  );
  pendantArmGroup.add(dropArm);

  // Operator HMI Terminal
  addControlPanel(
    pendantArmGroup,
    [0.65, -0.5, 0.3],
    [0.48, 0.58, 0.12],
    [0, -0.55, 0],
  );

  // Rotary MPG Handwheel / Jog dial on pendant
  const jogDial = createMesh(
    new THREE.CylinderGeometry(0.035, 0.035, 0.025, 16),
    steel,
    [0.72, -0.66, 0.42],
    [Math.PI / 2, 0, -0.55],
  );
  pendantArmGroup.add(jogDial);

  scene.add(pendantArmGroup);

  // ═══════════════════════════════════════════════════════════════════════════
  //  5. INTERNAL MACHINING ENCLOSURE & WORKTABLE (X-Y MOTION)
  // ═══════════════════════════════════════════════════════════════════════════
  // Telescoping stainless steel way covers
  const wayCovers = createMesh(
    new THREE.BoxGeometry(2.0, 0.12, 1.6),
    steel,
    [0, 0.82, 0],
  );
  scene.add(wayCovers);

  // Moving Worktable assembly
  const table = new THREE.Group();
  table.position.set(0, 0.92, 0);

  // Ground steel table platen with T-slots
  const tablePlaten = createMesh(
    new THREE.BoxGeometry(1.6, 0.14, 0.9),
    steel,
    [0, 0, 0],
  );
  table.add(tablePlaten);

  // 3 Recessed T-slots
  for (const z of [-0.25, 0, 0.25]) {
    table.add(createMesh(
      new THREE.BoxGeometry(1.5, 0.02, 0.035),
      black,
      [0, 0.075, z],
    ));
  }

  // Heavy Kurt-style precision milling vise
  const viseBody = createMesh(new THREE.BoxGeometry(0.55, 0.18, 0.32), black, [0, 0.16, 0]);
  table.add(viseBody);
  const viseJaws = createMesh(new THREE.BoxGeometry(0.48, 0.12, 0.08), steel, [0, 0.22, 0.1]);
  table.add(viseJaws);

  // Precision aluminum workpiece clamped in vise
  const rawPart = createMesh(
    new THREE.BoxGeometry(0.38, 0.16, 0.22),
    steel,
    [0, 0.34, 0],
  );
  table.add(rawPart);

  scene.add(table);

  // Loc-line flexible coolant hoses pointed at table
  const coolantNozzle1 = createMesh(
    new THREE.CylinderGeometry(0.015, 0.015, 0.35, 10),
    haasBlue,
    [-0.32, 1.8, 0.15],
    [0.5, 0, -0.4],
  );
  scene.add(coolantNozzle1);

  // ═══════════════════════════════════════════════════════════════════════════
  //  6. SPINDLE HEAD & BEARING CARTRIDGE (FAULT COMPONENT)
  // ═══════════════════════════════════════════════════════════════════════════
  const spindleHeadGroup = new THREE.Group();
  spindleHeadGroup.position.set(0, 2.15, 0);

  // Spindle casting slide housing (moves with Z axis)
  const zCasting = createMesh(
    new THREE.BoxGeometry(0.68, 0.8, 0.65),
    black,
    [0, 0.3, -0.15],
  );
  spindleHeadGroup.add(zCasting);

  // Drive motor on top of spindle
  const spindleMotor = createMesh(
    new THREE.CylinderGeometry(0.24, 0.24, 0.45, 20),
    black,
    [0, 0.85, -0.15],
  );
  spindleHeadGroup.add(spindleMotor);

  // Spindle bearing cartridge (fail component)
  const bearingHousing = createMesh(
    new THREE.CylinderGeometry(0.32, 0.34, 0.55, 24),
    bearingMat,
    [0, -0.15, 0],
  );
  spindleHeadGroup.add(bearingHousing);

  // Bearing flange mounting bolts
  addBoltRing(spindleHeadGroup, 0.33, 0.08, 8, 0.024, 0.035);

  // High-speed rotating spindle core + CAT-40 toolholder
  const rotatingSpindle = new THREE.Group();
  rotatingSpindle.position.set(0, -0.15, 0);

  // Precision spindle nose ring
  const nose = createMesh(
    new THREE.CylinderGeometry(0.2, 0.22, 0.18, 20),
    steel,
    [0, -0.32, 0],
  );
  rotatingSpindle.add(nose);

  // CAT-40 toolholder collet
  const collet = createMesh(
    new THREE.CylinderGeometry(0.1, 0.14, 0.22, 16),
    steel,
    [0, -0.48, 0],
  );
  rotatingSpindle.add(collet);

  // 4-Flute Carbide End Mill Tool
  const endMill = createMesh(
    new THREE.CylinderGeometry(0.035, 0.035, 0.32, 12),
    steel,
    [0, -0.7, 0],
  );
  rotatingSpindle.add(endMill);

  spindleHeadGroup.add(rotatingSpindle);
  scene.add(spindleHeadGroup);

  // ═══════════════════════════════════════════════════════════════════════════
  //  7. AUTOMATIC TOOL CHANGER (ATC) CAROUSEL DRUM
  // ═══════════════════════════════════════════════════════════════════════════
  const atcGroup = new THREE.Group();
  atcGroup.position.set(-1.05, 2.25, 0);

  // ATC support bracket from column
  atcGroup.add(createMesh(new THREE.BoxGeometry(0.4, 0.12, 0.25), black, [0.15, 0, 0]));

  // Carousel drum disc
  const drumDisc = createMesh(
    new THREE.CylinderGeometry(0.48, 0.48, 0.12, 20),
    haasGrey,
    [0, 0, 0],
  );
  atcGroup.add(drumDisc);

  // Tool pockets (ring of 10 tool pods)
  const pocketGeo = new THREE.CylinderGeometry(0.045, 0.045, 0.18, 12);
  for (let i = 0; i < 10; i++) {
    const angle = (i / 10) * Math.PI * 2;
    const px = Math.cos(angle) * 0.4;
    const pz = Math.sin(angle) * 0.4;
    atcGroup.add(createMesh(pocketGeo, steel, [px, -0.1, pz]));
  }

  scene.add(atcGroup);

  // ═══════════════════════════════════════════════════════════════════════════
  //  8. REAR ELECTRICAL CABINET & SERVICE PANELS
  // ═══════════════════════════════════════════════════════════════════════════
  const rearCabinetGroup = new THREE.Group();
  rearCabinetGroup.position.set(0, 1.4, -1.35);

  // Cabinet body
  rearCabinetGroup.add(createMesh(
    new THREE.BoxGeometry(2.4, 1.6, 0.35),
    haasGrey,
  ));

  // Dual ventilation grilles on rear
  addVentGrille(rearCabinetGroup, [-0.65, 0.35, -0.18], [0.55, 0.45, 0.02], 6, [0, Math.PI, 0]);
  addVentGrille(rearCabinetGroup, [0.65, 0.35, -0.18], [0.55, 0.45, 0.02], 6, [0, Math.PI, 0]);

  // Electrical warning sign
  addSafetyStripe(rearCabinetGroup, [0, 0.5, -0.18], [0.25, 0.12, 0.01]);

  scene.add(rearCabinetGroup);

  // ═══════════════════════════════════════════════════════════════════════════
  //  9. ANIMATION TICK & FAULT DISPATCH
  // ═══════════════════════════════════════════════════════════════════════════
  const faultLightPosition = new THREE.Vector3(0, 2.0, 0);

  const animateTick = (t: number, fault: boolean, repairing: boolean) => {
    // Spindle continuous rotation
    rotatingSpindle.rotation.y += 0.22;

    // Table multi-axis machining toolpath motion
    table.position.x = Math.sin(t * 1.6) * 0.32;
    table.position.z = Math.cos(t * 1.1) * 0.22;

    // Slight tool changer idle index
    atcGroup.rotation.y = Math.sin(t * 0.15) * 0.1;

    // Spindle bearing failure response
    if (repairing) {
      bearingMat.emissive.setHex(0x06b6d4);
      bearingMat.emissiveIntensity = (Math.sin(t * 4) + 1) * 0.45;
      spindleHeadGroup.position.set(0, 2.15, 0);
    } else if (fault) {
      bearingMat.emissive.setHex(0xdc2626);
      bearingMat.emissiveIntensity = 0.95 + Math.sin(t * 22) * 0.25;
      // High-vibration chatter on spindle head
      spindleHeadGroup.position.x = (Math.random() - 0.5) * 0.055;
      spindleHeadGroup.position.z = (Math.random() - 0.5) * 0.055;
    } else {
      bearingMat.emissiveIntensity = 0;
      spindleHeadGroup.position.set(0, 2.15, 0);
    }
  };

  return { failMesh: bearingHousing, failMat: bearingMat, faultLightPosition, animateTick };
}

