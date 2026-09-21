import { useEffect, useRef, useState } from 'react';
import type { FC } from 'react';
import * as THREE from 'three';

interface Machine3DViewerProps {
  machineId: string;
  readings?: Record<string, number>;
  isFaultActive?: boolean;
  isRepairing?: boolean;
  height?: string;
  showHUD?: boolean;
}

export const Machine3DViewer: FC<Machine3DViewerProps> = ({
  machineId,
  readings = {},
  isFaultActive = false,
  isRepairing = false,
  height = '480px',
  showHUD = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // HUD Pin screen coordinates { id, label, value, unit, x, y, isAnomaly }
  const [hudPins, setHudPins] = useState<
    Array<{
      id: string;
      label: string;
      value: string;
      unit: string;
      x: number;
      y: number;
      isAnomaly: boolean;
    }>
  >([]);

  // Internal mutable refs for 3D animation loop
  const stateRef = useRef({
    isFaultActive,
    isRepairing,
    readings,
  });

  useEffect(() => {
    stateRef.current.isFaultActive = isFaultActive;
    stateRef.current.isRepairing = isRepairing;
    stateRef.current.readings = readings;
  }, [isFaultActive, isRepairing, readings]);

  useEffect(() => {
    if (!canvasRef.current || !containerRef.current) return;

    const canvas = canvasRef.current;
    const container = containerRef.current;
    let width = container.clientWidth || 800;
    let heightPx = container.clientHeight || 480;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0f1d);
    scene.fog = new THREE.FogExp2(0x0a0f1d, 0.04);

    const camera = new THREE.PerspectiveCamera(45, width / heightPx, 0.1, 100);
    camera.position.set(4.8, 3.8, 5.2);

    // 2. Renderer
    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    });
    renderer.setSize(width, heightPx);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // 3. Studio Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.8);
    keyLight.position.set(6, 10, 6);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    scene.add(keyLight);

    const blueRimLight = new THREE.DirectionalLight(0x38bdf8, 1.2);
    blueRimLight.position.set(-6, 4, -5);
    scene.add(blueRimLight);

    // Fault dynamic point light (turns red when fault is active, cyan when repairing)
    const faultPointLight = new THREE.PointLight(0xef4444, 0, 8);
    scene.add(faultPointLight);

    // 4. Floor Grid with Tech Pedestal
    const gridHelper = new THREE.GridHelper(16, 32, 0x2563eb, 0x1e293b);
    gridHelper.position.y = -0.01;
    scene.add(gridHelper);

    const floorGeo = new THREE.PlaneGeometry(24, 24);
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0x070b14,
      roughness: 0.85,
      metalness: 0.2,
    });
    const floorMesh = new THREE.Mesh(floorGeo, floorMat);
    floorMesh.rotation.x = -Math.PI / 2;
    floorMesh.receiveShadow = true;
    scene.add(floorMesh);

    // 5. Machine Model Builder
    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    // References to animated parts
    const animParts: {
      type: string;
      base?: THREE.Object3D;
      j1?: THREE.Object3D;
      j2?: THREE.Object3D;
      j3?: THREE.Object3D;
      wrist?: THREE.Object3D;
      failingPart?: THREE.Mesh;
      failingMaterial?: THREE.MeshStandardMaterial;
      spindle?: THREE.Object3D;
      table?: THREE.Object3D;
      beltParts?: THREE.Mesh[];
      pressHead?: THREE.Object3D;
      calibArm?: THREE.Object3D;
      laserMesh?: THREE.Mesh;
      beaconGreen?: THREE.MeshBasicMaterial;
      beaconRed?: THREE.MeshBasicMaterial;
      beaconYellow?: THREE.MeshBasicMaterial;
      scannerTool?: THREE.Group;
      particles?: THREE.Points;
      particlePositions?: Float32Array;
      particleVelocities?: Float32Array;
      pinTargetPositions: Record<string, THREE.Vector3>;
    } = {
      type: machineId,
      pinTargetPositions: {},
    };

    // Shared materials
    const darkMetalMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.85, roughness: 0.35 });
    const silverSteelMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.9, roughness: 0.25 });
    const fanucYellowMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.3, roughness: 0.4 });
    const haasBlueMat = new THREE.MeshStandardMaterial({ color: 0x2563eb, metalness: 0.4, roughness: 0.3 });
    const motorCastIronMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.7, roughness: 0.5 });
    const graniteMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.2, metalness: 0.1 });

    // Status Andon Beacon Tower
    const beaconGroup = new THREE.Group();
    beaconGroup.position.set(-1.8, 0, -1.8);
    const poleGeo = new THREE.CylinderGeometry(0.04, 0.04, 1.8, 12);
    const pole = new THREE.Mesh(poleGeo, darkMetalMat);
    pole.position.y = 0.9;
    beaconGroup.add(pole);

    const bRedMat = new THREE.MeshBasicMaterial({ color: 0x440000 });
    const bYellowMat = new THREE.MeshBasicMaterial({ color: 0x443300 });
    const bGreenMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });

    const bRed = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.15, 16), bRedMat);
    bRed.position.y = 1.95;
    const bYellow = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.15, 16), bYellowMat);
    bYellow.position.y = 1.78;
    const bGreen = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.15, 16), bGreenMat);
    bGreen.position.y = 1.61;
    beaconGroup.add(bRed, bYellow, bGreen);
    scene.add(beaconGroup);

    animParts.beaconGreen = bGreenMat;
    animParts.beaconYellow = bYellowMat;
    animParts.beaconRed = bRedMat;

    // ──────────────────────────────────────────────────────────────────────────
    // Machine 1: M-01 FANUC ARC Mate 100iD (6-Axis Robotic Welding Arm)
    // ──────────────────────────────────────────────────────────────────────────
    if (machineId === 'M-01') {
      const robotGroup = new THREE.Group();

      // Base Pedestal
      const basePedestal = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.8, 0.35, 24), darkMetalMat);
      basePedestal.position.y = 0.175;
      basePedestal.castShadow = true;
      robotGroup.add(basePedestal);

      // J1 Turntable
      const j1 = new THREE.Group();
      j1.position.y = 0.35;
      const j1Body = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.6, 0.45, 24), fanucYellowMat);
      j1Body.position.y = 0.225;
      j1Body.castShadow = true;
      j1.add(j1Body);

      // J2 Shoulder with failing Reducer Gearbox
      const j2 = new THREE.Group();
      j2.position.set(0, 0.45, 0);

      // Failing Reducer Gearbox housing
      const reducerMat = new THREE.MeshStandardMaterial({
        color: 0x334155,
        metalness: 0.8,
        roughness: 0.3,
        emissive: new THREE.Color(0x000000),
        emissiveIntensity: 0,
      });
      const reducerHousing = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 0.6, 24), reducerMat);
      reducerHousing.rotation.z = Math.PI / 2;
      reducerHousing.castShadow = true;
      j2.add(reducerHousing);

      animParts.failingPart = reducerHousing;
      animParts.failingMaterial = reducerMat;
      animParts.pinTargetPositions['torque'] = new THREE.Vector3(0, 1.2, 0.3);

      // J2 Lower Arm
      const lowerArm = new THREE.Mesh(new THREE.BoxGeometry(0.32, 1.4, 0.32), fanucYellowMat);
      lowerArm.position.set(0, 0.7, 0);
      lowerArm.castShadow = true;
      j2.add(lowerArm);

      // J3 Elbow
      const j3 = new THREE.Group();
      j3.position.set(0, 1.4, 0);
      const j3Pivot = new THREE.Mesh(new THREE.SphereGeometry(0.28, 20, 20), silverSteelMat);
      j3.add(j3Pivot);

      const upperArm = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.22, 1.3, 16), fanucYellowMat);
      upperArm.rotation.x = Math.PI / 4;
      upperArm.position.set(0, 0.45, 0.45);
      upperArm.castShadow = true;
      j3.add(upperArm);

      // J4/J5/J6 Wrist and Welding Torch
      const wrist = new THREE.Group();
      wrist.position.set(0, 0.9, 0.9);

      const wristJoint = new THREE.Mesh(new THREE.SphereGeometry(0.18, 16, 16), silverSteelMat);
      wrist.add(wristJoint);

      const torchHead = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.09, 0.5, 12), silverSteelMat);
      torchHead.rotation.x = Math.PI / 2.5;
      torchHead.position.set(0, -0.2, 0.25);
      wrist.add(torchHead);

      const nozzleTip = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.15, 12), new THREE.MeshStandardMaterial({ color: 0xd97706 }));
      nozzleTip.position.set(0, -0.4, 0.45);
      wrist.add(nozzleTip);

      j3.add(wrist);
      j2.add(j3);
      j1.add(j2);
      robotGroup.add(j1);

      // Welding table and workpiece
      const weldTable = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.8, 1.2), darkMetalMat);
      weldTable.position.set(0, 0.4, 1.8);
      weldTable.castShadow = true;
      robotGroup.add(weldTable);

      const workPiece = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.2, 0.6), silverSteelMat);
      workPiece.position.set(0, 0.9, 1.8);
      robotGroup.add(workPiece);

      rootGroup.add(robotGroup);

      animParts.j1 = j1;
      animParts.j2 = j2;
      animParts.j3 = j3;
      animParts.wrist = wrist;
      animParts.pinTargetPositions['vibration'] = new THREE.Vector3(0, 1.6, 0.1);
      animParts.pinTargetPositions['cycle_count'] = new THREE.Vector3(0, 1.0, 1.8);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Machine 2: M-02 Haas VF-2 CNC Precision Mill
    // ──────────────────────────────────────────────────────────────────────────
    else if (machineId === 'M-02') {
      const cncGroup = new THREE.Group();

      // Main CNC Enclosure base
      const cncBase = new THREE.Mesh(new THREE.BoxGeometry(2.8, 1.1, 2.4), darkMetalMat);
      cncBase.position.y = 0.55;
      cncBase.castShadow = true;
      cncGroup.add(cncBase);

      // Upper Enclosure Frame
      const cncUpper = new THREE.Mesh(new THREE.BoxGeometry(2.6, 1.8, 2.2), haasBlueMat);
      cncUpper.position.y = 2.0;
      cncUpper.castShadow = true;
      cncGroup.add(cncUpper);

      // Viewing Window Cavity
      const windowCavity = new THREE.Mesh(
        new THREE.BoxGeometry(1.8, 1.2, 0.1),
        new THREE.MeshStandardMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.35, roughness: 0.1 })
      );
      windowCavity.position.set(0, 1.9, 1.12);
      cncGroup.add(windowCavity);

      // Internal Work Table (X/Y Bed)
      const table = new THREE.Group();
      table.position.set(0, 1.15, 0);
      const bed = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.15, 1.0), silverSteelMat);
      table.add(bed);

      // Billet workpiece in vise
      const billet = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.3, 0.4), silverSteelMat);
      billet.position.y = 0.22;
      table.add(billet);
      cncGroup.add(table);

      // Spindle Z-Head Column
      const spindle = new THREE.Group();
      spindle.position.set(0, 2.1, 0);

      // Spindle Bearing Housing (Failing Part)
      const bearingMat = new THREE.MeshStandardMaterial({
        color: 0x475569,
        metalness: 0.85,
        roughness: 0.2,
        emissive: new THREE.Color(0x000000),
        emissiveIntensity: 0,
      });
      const bearingHousing = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.32, 0.5, 24), bearingMat);
      spindle.add(bearingHousing);

      // Spinning Tool Chuck and Endmill Bit
      const toolChuck = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.2, 0.4, 16), silverSteelMat);
      toolChuck.position.y = -0.35;
      spindle.add(toolChuck);

      const endmill = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.35, 12), new THREE.MeshStandardMaterial({ color: 0xd4d4d8, metalness: 0.95 }));
      endmill.position.y = -0.62;
      spindle.add(endmill);

      cncGroup.add(spindle);
      rootGroup.add(cncGroup);

      animParts.table = table;
      animParts.spindle = spindle;
      animParts.failingPart = bearingHousing;
      animParts.failingMaterial = bearingMat;

      animParts.pinTargetPositions['vibration'] = new THREE.Vector3(0, 2.2, 0.4);
      animParts.pinTargetPositions['temperature'] = new THREE.Vector3(0, 2.0, -0.2);
      animParts.pinTargetPositions['rpm'] = new THREE.Vector3(0, 2.6, 0);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Machine 3: M-03 Industrial Conveyor / Stamping Station
    // ──────────────────────────────────────────────────────────────────────────
    else if (machineId === 'M-03') {
      const convGroup = new THREE.Group();

      // Conveyor Structure Legs
      for (let x of [-1.8, 0, 1.8]) {
        for (let z of [-0.6, 0.6]) {
          const leg = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.9, 0.12), darkMetalMat);
          leg.position.set(x, 0.45, z);
          convGroup.add(leg);
        }
      }

      // Conveyor Bed
      const bed = new THREE.Mesh(new THREE.BoxGeometry(4.2, 0.18, 1.3), darkMetalMat);
      bed.position.set(0, 0.9, 0);
      convGroup.add(bed);

      // Textured Rubber Belt
      const belt = new THREE.Mesh(
        new THREE.BoxGeometry(4.0, 0.04, 1.15),
        new THREE.MeshStandardMaterial({ color: 0x18181b, roughness: 0.9 })
      );
      belt.position.set(0, 1.0, 0);
      convGroup.add(belt);

      // Rollers at ends
      for (let x of [-2.0, 2.0]) {
        const roller = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 1.25, 20), silverSteelMat);
        roller.rotation.x = Math.PI / 2;
        roller.position.set(x, 0.9, 0);
        convGroup.add(roller);
      }

      // 3-Phase Electric Drive Motor with Cooling Fins (Failing Part)
      const motorMat = new THREE.MeshStandardMaterial({
        color: 0x334155,
        metalness: 0.7,
        roughness: 0.4,
        emissive: new THREE.Color(0x000000),
        emissiveIntensity: 0,
      });

      const motorGroup = new THREE.Group();
      motorGroup.position.set(-2.2, 0.9, 1.1);

      const motorStator = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 0.8, 24), motorMat);
      motorStator.rotation.z = Math.PI / 2;
      motorGroup.add(motorStator);

      // Cooling fins
      for (let i = -0.3; i <= 0.3; i += 0.12) {
        const fin = new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.38, 0.03, 24), darkMetalMat);
        fin.rotation.z = Math.PI / 2;
        fin.position.x = i;
        motorGroup.add(fin);
      }

      // Terminal connection box
      const termBox = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.25, 0.2), motorCastIronMat);
      termBox.position.set(0, 0.35, 0);
      motorGroup.add(termBox);
      convGroup.add(motorGroup);

      // Overhead Hydraulic Stamping Press
      const pressFrame = new THREE.Group();
      pressFrame.position.set(0.4, 1.0, 0);

      const pillarL = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 1.8, 16), silverSteelMat);
      pillarL.position.set(0, 0.9, -0.65);
      const pillarR = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 1.8, 16), silverSteelMat);
      pillarR.position.set(0, 0.9, 0.65);
      const topBeam = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.3, 1.5), haasBlueMat);
      topBeam.position.set(0, 1.8, 0);

      const pressHead = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.3, 0.8), silverSteelMat);
      pressHead.position.set(0, 1.3, 0);

      pressFrame.add(pillarL, pillarR, topBeam, pressHead);
      convGroup.add(pressFrame);

      // Automotive Transmission Parts on belt
      const beltParts: THREE.Mesh[] = [];
      for (let i = 0; i < 4; i++) {
        const part = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.24, 0.25, 16), silverSteelMat);
        part.position.set(-1.4 + i * 1.0, 1.15, 0);
        convGroup.add(part);
        beltParts.push(part);
      }

      rootGroup.add(convGroup);

      animParts.failingPart = motorStator;
      animParts.failingMaterial = motorMat;
      animParts.pressHead = pressHead;
      animParts.beltParts = beltParts;

      animParts.pinTargetPositions['current'] = new THREE.Vector3(-2.2, 1.4, 1.1);
      animParts.pinTargetPositions['temperature'] = new THREE.Vector3(-2.0, 1.0, 1.3);
      animParts.pinTargetPositions['vibration'] = new THREE.Vector3(-1.6, 1.1, 0.6);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Machine 4: M-04 Torque Calibration & Metrology Station
    // ──────────────────────────────────────────────────────────────────────────
    else {
      const calibGroup = new THREE.Group();

      // Precision Granite Base Slab
      const graniteBase = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.4, 1.8), graniteMat);
      graniteBase.position.y = 0.2;
      graniteBase.castShadow = true;
      calibGroup.add(graniteBase);

      // Steel Mounting Bench
      const bench = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.25, 1.4), darkMetalMat);
      bench.position.y = 0.525;
      calibGroup.add(bench);

      // Reaction Torque Transducer Cradle (Failing/Drifting Part)
      const transducerMat = new THREE.MeshStandardMaterial({
        color: 0x475569,
        metalness: 0.9,
        roughness: 0.25,
        emissive: new THREE.Color(0x000000),
        emissiveIntensity: 0,
      });

      const transducer = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 0.6, 24), transducerMat);
      transducer.rotation.z = Math.PI / 2;
      transducer.position.set(-0.2, 0.95, 0);
      calibGroup.add(transducer);

      // Gold AS9100 seal ring
      const sealRing = new THREE.Mesh(
        new THREE.TorusGeometry(0.36, 0.03, 16, 32),
        new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.9, roughness: 0.2 })
      );
      sealRing.rotation.y = Math.PI / 2;
      sealRing.position.set(-0.2, 0.95, 0);
      calibGroup.add(sealRing);

      // Servo Calibrator Arm
      const calibArm = new THREE.Group();
      calibArm.position.set(0.3, 0.95, 0);
      const armBar = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.6, 0.12), silverSteelMat);
      armBar.position.y = 0.25;
      calibArm.add(armBar);
      calibGroup.add(calibArm);

      // Laser Alignment Guide Beam (green normally, red on fault)
      const laserGeo = new THREE.CylinderGeometry(0.015, 0.015, 1.8, 8);
      const laserMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
      const laserMesh = new THREE.Mesh(laserGeo, laserMat);
      laserMesh.rotation.z = Math.PI / 2;
      laserMesh.position.set(0.1, 1.35, 0);
      calibGroup.add(laserMesh);

      // Digital Metrology Console Pillar
      const consolePillar = new THREE.Mesh(new THREE.BoxGeometry(0.35, 1.2, 0.35), darkMetalMat);
      consolePillar.position.set(0.8, 1.1, -0.6);
      calibGroup.add(consolePillar);

      const digitalDisplay = new THREE.Mesh(
        new THREE.BoxGeometry(0.4, 0.3, 0.05),
        new THREE.MeshBasicMaterial({ color: 0x0284c7 })
      );
      digitalDisplay.position.set(0.8, 1.5, -0.42);
      calibGroup.add(digitalDisplay);

      rootGroup.add(calibGroup);

      animParts.calibArm = calibArm;
      animParts.laserMesh = laserMesh;
      animParts.failingPart = transducer;
      animParts.failingMaterial = transducerMat;

      animParts.pinTargetPositions['calibration_dev'] = new THREE.Vector3(-0.2, 1.4, 0.2);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Automated 3D Maintenance Scanner Tool (for 1-click animated repair)
    // ──────────────────────────────────────────────────────────────────────────
    const scannerGroup = new THREE.Group();
    scannerGroup.visible = false;
    const ringGeo = new THREE.TorusGeometry(0.9, 0.04, 16, 48);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });
    const scannerRing = new THREE.Mesh(ringGeo, ringMat);
    scannerRing.rotation.x = Math.PI / 2;
    scannerGroup.add(scannerRing);

    const beamGeo = new THREE.ConeGeometry(0.9, 1.6, 32, 1, true);
    const beamMat = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      transparent: true,
      opacity: 0.25,
      side: THREE.DoubleSide,
    });
    const scannerBeam = new THREE.Mesh(beamGeo, beamMat);
    scannerBeam.position.y = 0.8;
    scannerGroup.add(scannerBeam);
    scene.add(scannerGroup);
    animParts.scannerTool = scannerGroup;

    // ──────────────────────────────────────────────────────────────────────────
    // Interactive Orbit / Drag Camera Controls
    // ──────────────────────────────────────────────────────────────────────────
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let spherical = { radius: 7.2, theta: 0.78, phi: 1.05 };

    const updateCameraFromSpherical = () => {
      spherical.phi = Math.max(0.2, Math.min(Math.PI / 2.1, spherical.phi));
      camera.position.x = spherical.radius * Math.sin(spherical.phi) * Math.sin(spherical.theta);
      camera.position.y = spherical.radius * Math.cos(spherical.phi);
      camera.position.z = spherical.radius * Math.sin(spherical.phi) * Math.cos(spherical.theta);
      camera.lookAt(0, 1.1, 0);
    };
    updateCameraFromSpherical();

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const dx = e.clientX - prevMouseX;
      const dy = e.clientY - prevMouseY;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;

      spherical.theta -= dx * 0.008;
      spherical.phi -= dy * 0.008;
      updateCameraFromSpherical();
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      spherical.radius = Math.max(3.0, Math.min(14.0, spherical.radius + e.deltaY * 0.006));
      updateCameraFromSpherical();
    };

    canvas.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    canvas.addEventListener('wheel', onWheel, { passive: false });

    // Handle Resize
    const onResize = () => {
      if (!container) return;
      width = container.clientWidth;
      heightPx = container.clientHeight;
      camera.aspect = width / heightPx;
      camera.updateProjectionMatrix();
      renderer.setSize(width, heightPx);
    };
    window.addEventListener('resize', onResize);

    // ──────────────────────────────────────────────────────────────────────────
    // Main Animation Loop
    // ──────────────────────────────────────────────────────────────────────────
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      const fault = stateRef.current.isFaultActive;
      const repairing = stateRef.current.isRepairing;
      const curReadings = stateRef.current.readings;

      // 1. Andon Tower Beacon status
      if (repairing) {
        animParts.beaconRed?.color.setHex(0x440000);
        animParts.beaconGreen?.color.setHex(0x004400);
        animParts.beaconYellow?.color.setHex(Math.sin(elapsed * 12) > 0 ? 0xf59e0b : 0x443300);
      } else if (fault) {
        animParts.beaconGreen?.color.setHex(0x004400);
        animParts.beaconYellow?.color.setHex(0x443300);
        animParts.beaconRed?.color.setHex(Math.sin(elapsed * 10) > 0 ? 0xef4444 : 0x440000);
      } else {
        animParts.beaconRed?.color.setHex(0x440000);
        animParts.beaconYellow?.color.setHex(0x443300);
        animParts.beaconGreen?.color.setHex(0x10b981);
      }

      // 2. Machine specific kinematics
      if (machineId === 'M-01') {
        const isWelding = curReadings.cycle_count === 1;
        const armSpeed = isWelding ? 1.4 : 0.8;
        if (animParts.j1) animParts.j1.rotation.y = Math.sin(elapsed * armSpeed) * 0.45;
        if (animParts.j2) animParts.j2.rotation.x = Math.sin(elapsed * (armSpeed * 1.5)) * 0.25;
        if (animParts.j3) animParts.j3.rotation.x = -Math.sin(elapsed * (armSpeed * 1.5)) * 0.35;
        if (animParts.wrist) animParts.wrist.rotation.z = Math.sin(elapsed * 2.0) * 0.5;

        // Reducer fault effect (vibration jitter + heat glow)
        if (animParts.failingPart && animParts.failingMaterial) {
          if (repairing) {
            const progress = (Math.sin(elapsed * 4) + 1) * 0.5;
            animParts.failingMaterial.emissive.setHex(0x06b6d4);
            animParts.failingMaterial.emissiveIntensity = progress * 0.7;
            faultPointLight.color.setHex(0x06b6d4);
            faultPointLight.intensity = progress * 3;
            faultPointLight.position.set(0, 1.2, 0);
          } else if (fault) {
            // Intense orange-red thermal heat & mechanical jitter
            animParts.failingMaterial.emissive.setHex(0xef4444);
            animParts.failingMaterial.emissiveIntensity = 0.85 + Math.sin(elapsed * 15) * 0.2;
            animParts.failingPart.position.x = (Math.random() - 0.5) * 0.04;
            animParts.failingPart.position.y = (Math.random() - 0.5) * 0.04;
            faultPointLight.color.setHex(0xef4444);
            faultPointLight.intensity = 2.5;
            faultPointLight.position.set(0, 1.2, 0);
          } else {
            animParts.failingMaterial.emissiveIntensity = 0;
            animParts.failingPart.position.set(0, 0, 0);
            faultPointLight.intensity = 0;
          }
        }
      } else if (machineId === 'M-02') {
        const rpm = curReadings.rpm || 8000;
        if (animParts.spindle) {
          animParts.spindle.rotation.y += (rpm / 60) * 0.05;
        }
        if (animParts.table) {
          animParts.table.position.x = Math.sin(elapsed * 1.5) * 0.35;
          animParts.table.position.z = Math.cos(elapsed * 1.2) * 0.25;
        }

        if (animParts.failingPart && animParts.failingMaterial) {
          if (repairing) {
            animParts.failingMaterial.emissive.setHex(0x06b6d4);
            animParts.failingMaterial.emissiveIntensity = 0.6;
            faultPointLight.color.setHex(0x06b6d4);
            faultPointLight.intensity = 3.0;
            faultPointLight.position.set(0, 2.1, 0);
          } else if (fault) {
            // Bearing chatter & high temp glow
            animParts.failingMaterial.emissive.setHex(0xdc2626);
            animParts.failingMaterial.emissiveIntensity = 0.9 + Math.sin(elapsed * 20) * 0.25;
            if (animParts.spindle) {
              animParts.spindle.position.x = (Math.random() - 0.5) * 0.05;
              animParts.spindle.position.z = (Math.random() - 0.5) * 0.05;
            }
            faultPointLight.color.setHex(0xdc2626);
            faultPointLight.intensity = 3.0;
            faultPointLight.position.set(0, 2.1, 0);
          } else {
            animParts.failingMaterial.emissiveIntensity = 0;
            if (animParts.spindle) animParts.spindle.position.set(0, 2.1, 0);
            faultPointLight.intensity = 0;
          }
        }
      } else if (machineId === 'M-03') {
        // Conveyor belt items translation
        if (animParts.beltParts) {
          const speed = fault ? 0.008 : 0.025;
          for (let p of animParts.beltParts) {
            p.position.x += speed;
            if (p.position.x > 1.8) p.position.x = -1.8;
          }
        }
        // Stamping head cycle
        if (animParts.pressHead) {
          animParts.pressHead.position.y = 1.3 - Math.abs(Math.sin(elapsed * 2.0)) * 0.35;
        }

        // Motor stator overload heat & vibration
        if (animParts.failingPart && animParts.failingMaterial) {
          if (repairing) {
            animParts.failingMaterial.emissive.setHex(0x06b6d4);
            animParts.failingMaterial.emissiveIntensity = 0.6;
            faultPointLight.color.setHex(0x06b6d4);
            faultPointLight.intensity = 2.5;
            faultPointLight.position.set(-2.2, 0.9, 1.1);
          } else if (fault) {
            animParts.failingMaterial.emissive.setHex(0xb91c1c);
            animParts.failingMaterial.emissiveIntensity = 0.95;
            animParts.failingPart.position.x = -2.2 + (Math.random() - 0.5) * 0.04;
            faultPointLight.color.setHex(0xb91c1c);
            faultPointLight.intensity = 2.5;
            faultPointLight.position.set(-2.2, 0.9, 1.1);
          } else {
            animParts.failingMaterial.emissiveIntensity = 0;
            animParts.failingPart.position.x = 0;
            faultPointLight.intensity = 0;
          }
        }
      } else if (machineId === 'M-04') {
        // Calibrator arm rotation
        if (animParts.calibArm) {
          animParts.calibArm.rotation.x = Math.sin(elapsed * 1.5) * 0.25;
        }

        // Laser alignment beam
        if (animParts.laserMesh) {
          if (fault) {
            (animParts.laserMesh.material as THREE.MeshBasicMaterial).color.setHex(0xef4444);
            animParts.laserMesh.rotation.y = Math.sin(elapsed * 3) * 0.1;
          } else {
            (animParts.laserMesh.material as THREE.MeshBasicMaterial).color.setHex(0x10b981);
            animParts.laserMesh.rotation.y = 0;
          }
        }

        if (animParts.failingPart && animParts.failingMaterial) {
          if (repairing) {
            animParts.failingMaterial.emissive.setHex(0x06b6d4);
            animParts.failingMaterial.emissiveIntensity = 0.5;
            faultPointLight.intensity = 2.0;
            faultPointLight.position.set(-0.2, 1.0, 0);
          } else if (fault) {
            animParts.failingMaterial.emissive.setHex(0xf59e0b);
            animParts.failingMaterial.emissiveIntensity = 0.8;
            faultPointLight.color.setHex(0xf59e0b);
            faultPointLight.intensity = 2.0;
            faultPointLight.position.set(-0.2, 1.0, 0);
          } else {
            animParts.failingMaterial.emissiveIntensity = 0;
            faultPointLight.intensity = 0;
          }
        }
      }

      // 3. Automated 3D Maintenance Scanner Tool Animation
      if (animParts.scannerTool) {
        if (repairing) {
          animParts.scannerTool.visible = true;
          // Sweep over failing part position
          const sweepY = 1.0 + Math.sin(elapsed * 5) * 0.6;
          animParts.scannerTool.position.set(0, sweepY, 0);
          animParts.scannerTool.rotation.y += 0.05;
        } else {
          animParts.scannerTool.visible = false;
        }
      }

      // 4. Update HUD screen projection pins
      if (showHUD) {
        const nextPins: Array<{
          id: string;
          label: string;
          value: string;
          unit: string;
          x: number;
          y: number;
          isAnomaly: boolean;
        }> = [];

        for (const [sKey, targetPos] of Object.entries(animParts.pinTargetPositions)) {
          const val = curReadings[sKey];
          if (val === undefined) continue;

          // Project 3D vector to screen coords
          const screenVec = targetPos.clone().project(camera);
          const x = ((screenVec.x + 1) * width) / 2;
          const y = ((-screenVec.y + 1) * heightPx) / 2;

          // Only show pins in front of the camera
          if (screenVec.z < 1.0) {
            const isAnomaly = fault && (sKey === 'torque' || sKey === 'vibration' || sKey === 'current' || sKey === 'calibration_dev');
            const unit =
              sKey === 'torque'
                ? 'Nm'
                : sKey === 'vibration'
                ? 'mm/s²'
                : sKey === 'temperature'
                ? '°C'
                : sKey === 'rpm'
                ? 'RPM'
                : sKey === 'current'
                ? 'A'
                : sKey === 'calibration_dev'
                ? 'Nm off'
                : '';

            nextPins.push({
              id: sKey,
              label: sKey.replace('_', ' ').toUpperCase(),
              value: typeof val === 'number' ? val.toFixed(1) : String(val),
              unit,
              x,
              y,
              isAnomaly: !!isAnomaly,
            });
          }
        }
        setHudPins(nextPins);
      }

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      canvas.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      canvas.removeEventListener('wheel', onWheel);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
    };
  }, [machineId]);

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        width: '100%',
        height,
        borderRadius: 'var(--card-radius)',
        overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
        border: isFaultActive
          ? '2px solid rgba(239, 68, 68, 0.7)'
          : isRepairing
          ? '2px solid rgba(6, 182, 212, 0.8)'
          : '1px solid var(--border-card)',
        transition: 'border-color 0.3s ease',
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          width: '100%',
          height: '100%',
          display: 'block',
          cursor: 'grab',
        }}
      />

      {/* Top Left Twin Status Pill */}
      <div
        style={{
          position: 'absolute',
          top: '16px',
          left: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(8, 12, 21, 0.85)',
          backdropFilter: 'blur(10px)',
          border: '1px solid var(--border-card)',
          padding: '6px 14px',
          borderRadius: 'var(--btn-radius)',
          fontSize: '0.76rem',
          fontWeight: 700,
          color: 'var(--text-primary)',
          pointerEvents: 'none',
        }}
      >
        <span
          className="pulse-dot"
          style={{
            background: isFaultActive
              ? 'var(--status-critical)'
              : isRepairing
              ? 'var(--accent-cyan)'
              : 'var(--status-healthy)',
            width: '8px',
            height: '8px',
          }}
        />
        <span>
          {isRepairing
            ? 'AUTOMATED REPAIR SCAN IN PROGRESS'
            : isFaultActive
            ? 'PHYSICAL FAULT CONDITION DETECTED'
            : 'DIGITAL TWIN: SYNCHRONIZED (NOMINAL)'}
        </span>
      </div>

      {/* Top Right 3D Orbit Help Hint */}
      <div
        style={{
          position: 'absolute',
          top: '16px',
          right: '16px',
          background: 'rgba(8, 12, 21, 0.75)',
          backdropFilter: 'blur(8px)',
          border: '1px solid var(--border-subtle)',
          padding: '4px 10px',
          borderRadius: 'var(--btn-radius)',
          fontSize: '0.68rem',
          color: 'var(--text-muted)',
          pointerEvents: 'none',
        }}
      >
        🖱️ Left Drag: Orbit • Scroll: Zoom
      </div>

      {/* Live 3D Floating Sensor Probe HUD Badges */}
      {showHUD &&
        hudPins.map((pin) => (
          <div
            key={pin.id}
            style={{
              position: 'absolute',
              left: `${pin.x}px`,
              top: `${pin.y}px`,
              transform: 'translate(-50%, -120%)',
              pointerEvents: 'none',
              transition: 'transform 0.05s ease',
            }}
          >
            <div
              style={{
                background: pin.isAnomaly ? 'rgba(239, 68, 68, 0.92)' : 'rgba(15, 23, 42, 0.88)',
                backdropFilter: 'blur(6px)',
                border: `1px solid ${pin.isAnomaly ? '#ef4444' : 'rgba(56, 189, 248, 0.4)'}`,
                padding: '4px 8px',
                borderRadius: '4px',
                boxShadow: pin.isAnomaly ? '0 0 12px rgba(239, 68, 68, 0.6)' : '0 2px 8px rgba(0,0,0,0.4)',
                textAlign: 'center',
                whiteSpace: 'nowrap',
              }}
            >
              <div style={{ fontSize: '0.6rem', color: pin.isAnomaly ? '#fee2e2' : '#94a3b8', fontWeight: 600 }}>
                {pin.label}
              </div>
              <div
                style={{
                  fontSize: '0.84rem',
                  fontWeight: 800,
                  fontFamily: 'var(--font-mono)',
                  color: pin.isAnomaly ? '#ffffff' : '#38bdf8',
                }}
              >
                {pin.value} <span style={{ fontSize: '0.65rem' }}>{pin.unit}</span>
              </div>
            </div>
            {/* Pointer notch */}
            <div
              style={{
                width: '6px',
                height: '6px',
                background: pin.isAnomaly ? '#ef4444' : '#38bdf8',
                borderRadius: '50%',
                margin: '3px auto 0',
                boxShadow: '0 0 6px #38bdf8',
              }}
            />
          </div>
        ))}

      {/* Repairing Overlay Banner with Progress */}
      {isRepairing && (
        <div
          style={{
            position: 'absolute',
            bottom: '24px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(8, 12, 21, 0.92)',
            backdropFilter: 'blur(12px)',
            border: '1px solid var(--accent-cyan)',
            padding: '12px 28px',
            borderRadius: 'var(--btn-radius)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 8px 30px rgba(6, 182, 212, 0.35)',
            pointerEvents: 'none',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.1rem' }}>🔧</span>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
              Executing Maintenance & Baseline Normalization Routine...
            </span>
          </div>
          <div
            style={{
              width: '280px',
              height: '4px',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '2px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: '100%',
                height: '100%',
                background: 'linear-gradient(90deg, #06b6d4, #3b82f6)',
                animation: 'pulse 1.2s infinite ease-in-out',
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
