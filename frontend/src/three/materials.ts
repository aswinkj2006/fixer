/**
 * Shared PBR Material Presets for Industrial Equipment
 *
 * All machine models pull from this palette so every asset
 * renders with a consistent, physically-based look.
 *
 * Factory functions return fresh instances so per-model
 * mutations (fault glow, emissive overrides) don't leak.
 */
import * as THREE from 'three';

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Painted metal / plastic shells                                           */
/* ═══════════════════════════════════════════════════════════════════════════ */

/** FANUC-style bright yellow painted shell (clearcoat automotive finish) */
export function createIndustrialYellow(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0xf59e0b,
    roughness: 0.35,
    metalness: 0.15,
    clearcoat: 0.6,
    clearcoatRoughness: 0.2,
  });
}

/** Haas / industrial blue painted enclosure */
export function createIndustrialBlue(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0x1d4ed8,
    roughness: 0.35,
    metalness: 0.15,
    clearcoat: 0.6,
    clearcoatRoughness: 0.2,
  });
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Structural / housing metal                                               */
/* ═══════════════════════════════════════════════════════════════════════════ */

/** Black structural frames, joint housings, machine bases */
export function createStructuralBlack(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0x1e293b,
    roughness: 0.4,
    metalness: 0.6,
  });
}

/** Brushed stainless steel / chrome — spindle shafts, precision surfaces */
export function createBrushedSteel(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0x94a3b8,
    roughness: 0.18,
    metalness: 0.92,
  });
}

/** Motor housing / cast iron — heavier, duller than structural black */
export function createMotorCastIron(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0x334155,
    roughness: 0.45,
    metalness: 0.72,
  });
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Rubber, cable, non-metal                                                 */
/* ═══════════════════════════════════════════════════════════════════════════ */

/** Rubber gaskets, cable sheaths, belt surfaces */
export function createRubberDark(): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color: 0x18181b,
    roughness: 0.9,
    metalness: 0.0,
  });
}

/** Granite / stone surface plate (metrology) */
export function createGranite(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0x0f172a,
    roughness: 0.15,
    metalness: 0.15,
  });
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Glass, indicators, emissive                                              */
/* ═══════════════════════════════════════════════════════════════════════════ */

/** Transparent glass panel (CNC window, gauge cover) */
export function createGlassIndicator(): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color: 0x334155,
    roughness: 0.1,
    metalness: 0.2,
    transparent: true,
    opacity: 0.35,
    depthWrite: false,
  });
}

/** Welding torch tip / hot metal accent */
export function createWeldTorch(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0xd97706,
    roughness: 0.3,
    metalness: 0.5,
    emissive: new THREE.Color(0x4a2400),
    emissiveIntensity: 0.15,
  });
}

/** Precision seal ring — high-vis yellow, metallic */
export function createSealRing(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0xf59e0b,
    roughness: 0.2,
    metalness: 0.9,
  });
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Failure-capable material (can be mutated for emissive fault glow)        */
/* ═══════════════════════════════════════════════════════════════════════════ */

/** Creates a material that starts neutral but can pulse red/cyan for faults */
export function createFailureMaterial(
  baseColor: number = 0x334155,
  metalness: number = 0.8,
  roughness: number = 0.3,
): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: baseColor,
    metalness,
    roughness,
    emissive: new THREE.Color(0x000000),
    emissiveIntensity: 0,
  });
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Small emissive indicators (screen panels, laser, status LEDs)            */
/* ═══════════════════════════════════════════════════════════════════════════ */

/** Glowing digital readout / screen */
export function createScreenPanel(): THREE.MeshBasicMaterial {
  return new THREE.MeshBasicMaterial({ color: 0x0284c7 });
}

/** Laser beam material */
export function createLaserBeam(color: number = 0x10b981): THREE.MeshBasicMaterial {
  return new THREE.MeshBasicMaterial({ color });
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Safety stripe texture (yellow/black diagonal hazard)                     */
/* ═══════════════════════════════════════════════════════════════════════════ */

/** Generates a canvas-based yellow/black hazard stripe texture */
export function createSafetyStripeMaterial(): THREE.MeshStandardMaterial {
  const size = 128;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d')!;

  // Black background
  ctx.fillStyle = '#1a1a1a';
  ctx.fillRect(0, 0, size, size);

  // Yellow diagonal stripes
  ctx.strokeStyle = '#f59e0b';
  ctx.lineWidth = 14;
  for (let i = -size; i < size * 2; i += 28) {
    ctx.beginPath();
    ctx.moveTo(i, 0);
    ctx.lineTo(i + size, size);
    ctx.stroke();
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(2, 1);

  return new THREE.MeshStandardMaterial({
    map: texture,
    roughness: 0.6,
    metalness: 0.1,
  });
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Additional Industrial Presets (Controller, Hoses, Machine Enclosures)     */
/* ═══════════════════════════════════════════════════════════════════════════ */

/** FANUC R-30iB controller cabinet red painted sheet metal */
export function createRedController(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0xdc2626,
    roughness: 0.35,
    metalness: 0.15,
    clearcoat: 0.5,
    clearcoatRoughness: 0.2,
  });
}

/** Industrial green pneumatic / coolant flexible hose */
export function createGreenHose(): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color: 0x16a34a,
    roughness: 0.65,
    metalness: 0.05,
  });
}

/** Haas-style machine enclosure powder coat */
export function createHaasGrey(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0xc0c8d4,
    roughness: 0.4,
    metalness: 0.25,
    clearcoat: 0.15,
    clearcoatRoughness: 0.3,
  });
}

/** Extruded aluminum / anodized silver cart tubing & handles */
export function createCartSilver(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0xc8d1dc,
    roughness: 0.25,
    metalness: 0.85,
    clearcoat: 0.2,
  });
}

/** Polished epoxy concrete floor tile */
export function createConcreteFloor(): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color: 0x9aa5b5,
    roughness: 0.38,
    metalness: 0.18,
  });
}

/** Perforated metal mesh / shelf / vent grille */
export function createPerforatedMetal(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0x334155,
    roughness: 0.45,
    metalness: 0.75,
  });
}

/** Warning / caution sign yellow */
export function createWarningYellow(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0xfacc15,
    roughness: 0.3,
    metalness: 0.1,
  });
}

