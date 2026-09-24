/**
 * Per-Machine Camera Presets & CCTV Labels
 *
 * Fixed, deliberate three-quarter camera angles per machine.
 * No auto-rotation — these are product-shot compositions
 * that highlight the working part of each asset.
 */
import * as THREE from 'three';

export interface CameraPreset {
  position: THREE.Vector3;
  target: THREE.Vector3;
  fov: number;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Camera angles                                                            */
/* ═══════════════════════════════════════════════════════════════════════════ */

const PRESETS: Record<string, CameraPreset> = {
  'M-01': {
    position: new THREE.Vector3(4.5, 3.2, 4.8),
    target: new THREE.Vector3(0, 1.0, 0.3),
    fov: 40,
  },
  'M-02': {
    position: new THREE.Vector3(4.0, 3.5, 4.2),
    target: new THREE.Vector3(0, 1.5, 0),
    fov: 38,
  },
  'M-03': {
    position: new THREE.Vector3(5.5, 3.0, 4.0),
    target: new THREE.Vector3(-0.2, 1.0, 0),
    fov: 42,
  },
  'M-04': {
    position: new THREE.Vector3(3.8, 2.8, 3.5),
    target: new THREE.Vector3(0.2, 0.8, 0),
    fov: 38,
  },
};

/** Default fallback for unknown machine IDs */
const DEFAULT_PRESET: CameraPreset = {
  position: new THREE.Vector3(5.0, 3.5, 5.0),
  target: new THREE.Vector3(0, 1.0, 0),
  fov: 40,
};

export function getCameraPreset(machineId: string): CameraPreset {
  return PRESETS[machineId] ?? DEFAULT_PRESET;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  CCTV camera labels                                                       */
/* ═══════════════════════════════════════════════════════════════════════════ */

const CAMERA_LABELS: Record<string, string> = {
  'M-01': 'CAM-01  |  FANUC ARC Mate 100iD — Welding Cell',
  'M-02': 'CAM-02  |  Haas VF-2 CNC Precision Mill',
  'M-03': 'CAM-03  |  Conveyor & Stamping Station',
  'M-04': 'CAM-04  |  Torque Calibration Bench',
};

export function getCameraLabel(machineId: string): string {
  return CAMERA_LABELS[machineId] ?? `CAM  |  ${machineId}`;
}
