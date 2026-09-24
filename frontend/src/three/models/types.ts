/**
 * Shared interface for machine model builders.
 *
 * Every buildM0X function returns this shape so the
 * viewer component can treat all machines uniformly.
 */
import * as THREE from 'three';

export interface MachineModelParts {
  /**
   * The fail-target mesh whose position gets jittered during fault.
   * May be undefined for machines without a visible fail component.
   */
  failMesh?: THREE.Mesh;

  /**
   * The material applied to the fail mesh — mutated for emissive glow.
   */
  failMat?: THREE.MeshPhysicalMaterial;

  /**
   * Ideal position for the dynamic fault PointLight.
   */
  faultLightPosition: THREE.Vector3;

  /**
   * Called every animation frame to drive machine-specific motion.
   * @param t - elapsed time in seconds (from THREE.Clock)
   * @param fault - whether a fault is currently active
   * @param repairing - whether a repair is in progress
   */
  animateTick: (t: number, fault: boolean, repairing: boolean) => void;
}

/** Signature for all machine model builder functions. */
export type MachineModelBuilder = (scene: THREE.Scene) => MachineModelParts;
