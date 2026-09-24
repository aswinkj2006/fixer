/**
 * Industrial Scene Factory
 *
 * Creates the shared rendering environment for all machine views:
 * - Scene with dark industrial background + fog
 * - PMREMGenerator synthetic environment map (warm studio reflections)
 * - Three-point lighting rig (key + fill + rim)
 * - Ground plane with grid overlay
 * - Renderer with ACES tone mapping, sRGB output
 * - EffectComposer with SSAO + UnrealBloom + OutputPass
 * - OrbitControls with autoRotate: false
 * - Dynamic fault PointLight
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { SSAOPass } from 'three/examples/jsm/postprocessing/SSAOPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { getCameraPreset } from './cameraPresets';
import { createStructuralBlack } from './materials';
import { createMesh } from './meshUtils';

export interface IndustrialSceneResult {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
  controls: OrbitControls;
  composer: EffectComposer;
  faultLight: THREE.PointLight;
  dispose: () => void;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Synthetic environment map generator                                      */
/* ═══════════════════════════════════════════════════════════════════════════ */

function createFactoryEnvironment(renderer: THREE.WebGLRenderer): THREE.Texture {
  const pmrem = new THREE.PMREMGenerator(renderer);
  pmrem.compileCubemapShader();

  // Build a small scene with clean industrial lighting to bake into the env map
  const envScene = new THREE.Scene();

  // Top: daylight / high-bay LED ceiling illumination
  const topLight = new THREE.HemisphereLight(0xffffff, 0x94a3b8, 1.4);
  envScene.add(topLight);

  // Key direction: bright neutral highlight
  const warmDir = new THREE.DirectionalLight(0xffffff, 1.2);
  warmDir.position.set(5, 10, 4);
  envScene.add(warmDir);

  // Cool fill from side (factory walls bounce)
  const coolDir = new THREE.DirectionalLight(0xe2e8f0, 0.8);
  coolDir.position.set(-5, 4, -4);
  envScene.add(coolDir);

  // Bright skybox sphere so metallic reflections see bright factory walls
  const hotspot = new THREE.Mesh(
    new THREE.SphereGeometry(50, 16, 16),
    new THREE.MeshBasicMaterial({ color: 0xdde3ea, side: THREE.BackSide }),
  );
  envScene.add(hotspot);

  const envMap = pmrem.fromScene(envScene, 0.04).texture;
  pmrem.dispose();
  return envMap;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Main scene factory                                                       */
/* ═══════════════════════════════════════════════════════════════════════════ */

export function createIndustrialScene(
  canvas: HTMLCanvasElement,
  container: HTMLElement,
  machineId: string,
  highQuality: boolean = true,
): IndustrialSceneResult {
  let w = container.clientWidth || 800;
  let h = container.clientHeight || 480;

  // ── Scene ──
  const scene = new THREE.Scene();
  // Well-lit clean modern industrial factory space
  scene.background = new THREE.Color(0xdce3ec);
  // Linear fog starting well behind the machine so the model is 100% crisp with zero haze
  scene.fog = new THREE.Fog(0xdce3ec, 16, 45);

  // ── Camera (from preset) ──
  const preset = getCameraPreset(machineId);
  const camera = new THREE.PerspectiveCamera(preset.fov, w / h, 0.1, 100);
  camera.position.copy(preset.position);

  // ── Renderer ──
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
    powerPreference: 'high-performance',
  });
  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  // ── Environment Map ──
  const envMap = createFactoryEnvironment(renderer);
  scene.environment = envMap;

  // ── OrbitControls — NO auto-rotate ──
  const controls = new OrbitControls(camera, canvas);
  controls.target.copy(preset.target);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.autoRotate = false;
  controls.minDistance = 2.5;
  controls.maxDistance = 14;
  controls.maxPolarAngle = Math.PI / 2.05;
  controls.update();

  // ── Bright Industrial Facility Lighting Rig ──
  // Ambient: balanced high-CRI white light
  scene.add(new THREE.AmbientLight(0xffffff, 0.65));

  // Key light: overhead high-bay industrial LED fixture (crisp shadow)
  const keyLight = new THREE.DirectionalLight(0xffffff, 1.6);
  keyLight.position.set(6, 12, 6);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(1024, 1024);
  keyLight.shadow.camera.near = 0.5;
  keyLight.shadow.camera.far = 32;
  keyLight.shadow.camera.left = -7;
  keyLight.shadow.camera.right = 7;
  keyLight.shadow.camera.top = 7;
  keyLight.shadow.camera.bottom = -7;
  keyLight.shadow.bias = -0.0004;
  scene.add(keyLight);

  // Overhead soft fill
  const overheadBank = new THREE.DirectionalLight(0xf1f5f9, 0.35);
  overheadBank.position.set(0, 14, 0);
  scene.add(overheadBank);

  // Fill light: soft neutral bounce from factory walls
  const fillLight = new THREE.DirectionalLight(0xe2e8f0, 0.65);
  fillLight.position.set(-6, 5, 5);
  scene.add(fillLight);

  // Rim / back light: subtle contour definition
  const rimLight = new THREE.DirectionalLight(0xdbeafe, 0.6);
  rimLight.position.set(-4, 7, -6);
  scene.add(rimLight);

  // Dynamic fault / repair point light
  const faultLight = new THREE.PointLight(0xef4444, 0, 8);
  scene.add(faultLight);

  // ── Polished Factory Concrete Floor ──
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x8f9aa9,
    roughness: 0.42,
    metalness: 0.15,
  });
  const floor = createMesh(
    new THREE.PlaneGeometry(30, 30),
    floorMat,
    undefined,
    [-Math.PI / 2, 0, 0],
    false,
    true,
  );
  scene.add(floor);

  // Floor grid marking (walkway / machine perimeter)
  const gridHelper = new THREE.GridHelper(20, 20, 0x546e7a, 0xa0aec0);
  gridHelper.position.y = 0.002;
  scene.add(gridHelper);

  // Factory safety boundary borders (yellow/black perimeter guide lines)
  const borderMat = createStructuralBlack();
  for (const z of [-4.5, 4.5]) {
    scene.add(createMesh(
      new THREE.BoxGeometry(18, 0.02, 0.08),
      borderMat,
      [0, 0.01, z],
    ));
  }
  for (const x of [-4.5, 4.5]) {
    scene.add(createMesh(
      new THREE.BoxGeometry(0.08, 0.02, 9),
      borderMat,
      [x, 0.01, 0],
    ));
  }

  // ── Post-Processing ──
  const composer = new EffectComposer(renderer);

  const renderPass = new RenderPass(scene, camera);
  composer.addPass(renderPass);

  if (highQuality) {
    // SSAO — crisp joint creases and contact shadows
    const ssaoPass = new SSAOPass(scene, camera, w, h);
    ssaoPass.kernelRadius = 0.45;
    ssaoPass.minDistance = 0.001;
    ssaoPass.maxDistance = 0.03;
    (ssaoPass as any).output = SSAOPass.OUTPUT.Default;
    composer.addPass(ssaoPass);

    // Bloom — high threshold (0.96) so only actual emissive items (LEDs, laser, screens) bloom
    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(w, h),
      0.15,   // strength
      0.35,   // radius
      0.96,   // threshold (prevents white surfaces from blooming)
    );
    composer.addPass(bloomPass);
  }

  // Output pass for correct sRGB
  const outputPass = new OutputPass();
  composer.addPass(outputPass);

  // ── Resize Handler ──
  const onResize = () => {
    if (!container) return;
    w = container.clientWidth;
    h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    composer.setSize(w, h);
  };
  window.addEventListener('resize', onResize);

  // ── Dispose ──
  const dispose = () => {
    window.removeEventListener('resize', onResize);
    controls.dispose();
    renderer.dispose();
    envMap.dispose();
  };

  return { scene, camera, renderer, controls, composer, faultLight, dispose };
}
