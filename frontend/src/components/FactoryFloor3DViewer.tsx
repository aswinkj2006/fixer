import { useEffect, useRef } from 'react';
import type { FC } from 'react';
import { useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import type { Machine } from '../types';

interface FactoryFloor3DViewerProps {
  machines: Machine[];
  height?: string;
}

export const FactoryFloor3DViewer: FC<FactoryFloor3DViewerProps> = ({
  machines,
  height = '520px',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const navigate = useNavigate();

  const machinesRef = useRef(machines);
  useEffect(() => {
    machinesRef.current = machines;
  }, [machines]);

  useEffect(() => {
    if (!canvasRef.current || !containerRef.current) return;

    const canvas = canvasRef.current;
    const container = containerRef.current;
    let width = container.clientWidth || 900;
    let heightPx = container.clientHeight || 520;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x070b14);
    scene.fog = new THREE.FogExp2(0x070b14, 0.03);

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / heightPx, 0.1, 100);
    let spherical = { radius: 17.0, theta: 0.75, phi: 1.0 };

    const updateCamera = () => {
      spherical.phi = Math.max(0.3, Math.min(Math.PI / 2.15, spherical.phi));
      camera.position.x = spherical.radius * Math.sin(spherical.phi) * Math.sin(spherical.theta);
      camera.position.y = spherical.radius * Math.cos(spherical.phi);
      camera.position.z = spherical.radius * Math.sin(spherical.phi) * Math.cos(spherical.theta);
      camera.lookAt(0, 0.5, 0);
    };
    updateCamera();

    // Renderer
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setSize(width, heightPx);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.1);
    scene.add(ambientLight);

    const overheadGantryLight = new THREE.DirectionalLight(0xffffff, 1.6);
    overheadGantryLight.position.set(5, 16, 5);
    overheadGantryLight.castShadow = true;
    scene.add(overheadGantryLight);

    const blueAccentLight = new THREE.PointLight(0x0284c7, 3, 20);
    blueAccentLight.position.set(0, 6, 0);
    scene.add(blueAccentLight);

    // Concrete Factory Floor
    const floorGeo = new THREE.PlaneGeometry(32, 24);
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      roughness: 0.8,
      metalness: 0.2,
    });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    scene.add(floor);

    // Yellow Safety Boundary Lines on Floor
    const grid = new THREE.GridHelper(24, 24, 0xf59e0b, 0x1e293b);
    grid.position.y = 0.01;
    scene.add(grid);

    // Materials
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8, roughness: 0.3 });
    const silverMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.9, roughness: 0.2 });
    const yellowMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.4, roughness: 0.4 });
    const blueMat = new THREE.MeshStandardMaterial({ color: 0x2563eb, metalness: 0.5, roughness: 0.3 });

    // Interactive clickable hitboxes
    const interactiveMeshes: Array<{ mesh: THREE.Object3D; machineId: string }> = [];

    // 1. Cell 1: M-01 Robotic Welding Arm (Position: -5, 0, -3)
    const cell1 = new THREE.Group();
    cell1.position.set(-5.5, 0, -3.2);

    const rBase = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.8, 0.4, 16), darkMat);
    rBase.position.y = 0.2;
    const rArm1 = new THREE.Mesh(new THREE.BoxGeometry(0.35, 1.4, 0.35), yellowMat);
    rArm1.position.set(0, 0.9, 0);
    const rArm2 = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.2, 1.2, 16), yellowMat);
    rArm2.rotation.x = Math.PI / 4;
    rArm2.position.set(0, 1.8, 0.4);
    cell1.add(rBase, rArm1, rArm2);

    // Safety fencing for cell 1
    const fenceMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, wireframe: true });
    const fence = new THREE.Mesh(new THREE.BoxGeometry(3.6, 1.2, 3.6), fenceMat);
    fence.position.y = 0.6;
    cell1.add(fence);
    scene.add(cell1);
    interactiveMeshes.push({ mesh: cell1, machineId: 'M-01' });

    // 2. Cell 2: M-02 Haas CNC Precision Mill (Position: 5.5, 0, -3.2)
    const cell2 = new THREE.Group();
    cell2.position.set(5.5, 0, -3.2);

    const cncBody = new THREE.Mesh(new THREE.BoxGeometry(2.4, 1.2, 2.0), darkMat);
    cncBody.position.y = 0.6;
    const cncHead = new THREE.Mesh(new THREE.BoxGeometry(2.2, 1.4, 1.8), blueMat);
    cncHead.position.y = 1.8;
    const cncGlass = new THREE.Mesh(
      new THREE.BoxGeometry(1.4, 0.9, 0.1),
      new THREE.MeshStandardMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.4 })
    );
    cncGlass.position.set(0, 1.8, 0.92);
    cell2.add(cncBody, cncHead, cncGlass);
    scene.add(cell2);
    interactiveMeshes.push({ mesh: cell2, machineId: 'M-02' });

    // 3. Cell 3: M-03 Conveyor & Press Line (Position: -5.5, 0, 3.5)
    const cell3 = new THREE.Group();
    cell3.position.set(-5.5, 0, 3.5);

    const convBed = new THREE.Mesh(new THREE.BoxGeometry(4.2, 0.2, 1.2), darkMat);
    convBed.position.y = 0.7;
    const cMotor = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.32, 0.7, 16), darkMat);
    cMotor.rotation.z = Math.PI / 2;
    cMotor.position.set(-2.2, 0.7, 0.7);
    const press = new THREE.Mesh(new THREE.BoxGeometry(0.5, 1.6, 1.4), blueMat);
    press.position.set(0.6, 1.5, 0);
    cell3.add(convBed, cMotor, press);
    scene.add(cell3);
    interactiveMeshes.push({ mesh: cell3, machineId: 'M-03' });

    // 4. Cell 4: M-04 Torque Metrology Bench (Position: 5.5, 0, 3.5)
    const cell4 = new THREE.Group();
    cell4.position.set(5.5, 0, 3.5);

    const granite = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.35, 1.6), darkMat);
    granite.position.y = 0.2;
    const benchTop = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.2, 1.2), silverMat);
    benchTop.position.y = 0.45;
    const transducer = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.5, 16), silverMat);
    transducer.rotation.z = Math.PI / 2;
    transducer.position.set(-0.2, 0.8, 0);
    cell4.add(granite, benchTop, transducer);
    scene.add(cell4);
    interactiveMeshes.push({ mesh: cell4, machineId: 'M-04' });

    // Raycaster for click-to-navigate
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const onCanvasClick = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      for (const item of interactiveMeshes) {
        const intersects = raycaster.intersectObjects(item.mesh.children, true);
        if (intersects.length > 0) {
          navigate(`/machine/${item.machineId}`);
          return;
        }
      }
    };

    // Orbit Drag Controls
    let isDragging = false;
    let prevX = 0;
    let prevY = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevX = e.clientX;
      prevY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const dx = e.clientX - prevX;
      const dy = e.clientY - prevY;
      prevX = e.clientX;
      prevY = e.clientY;

      spherical.theta -= dx * 0.006;
      spherical.phi -= dy * 0.006;
      updateCamera();
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      spherical.radius = Math.max(8.0, Math.min(26.0, spherical.radius + e.deltaY * 0.01));
      updateCamera();
    };

    canvas.addEventListener('click', onCanvasClick);
    canvas.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    canvas.addEventListener('wheel', onWheel, { passive: false });

    // Resize
    const onResize = () => {
      if (!container) return;
      width = container.clientWidth;
      heightPx = container.clientHeight;
      camera.aspect = width / heightPx;
      camera.updateProjectionMatrix();
      renderer.setSize(width, heightPx);
    };
    window.addEventListener('resize', onResize);

    // Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // Subtle machine kinematics on the factory floor
      rArm1.rotation.y = Math.sin(elapsed * 0.8) * 0.3;
      cMotor.rotation.x += 0.05;

      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      canvas.removeEventListener('click', onCanvasClick);
      canvas.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      canvas.removeEventListener('wheel', onWheel);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
    };
  }, [navigate]);

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        width: '100%',
        height,
        borderRadius: 'var(--card-radius)',
        overflow: 'hidden',
        border: '1px solid var(--border-card)',
        boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
      }}
    >
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '100%', display: 'block', cursor: 'pointer' }}
      />

      {/* Top Banner */}
      <div
        style={{
          position: 'absolute',
          top: '16px',
          left: '16px',
          background: 'rgba(8, 12, 21, 0.88)',
          backdropFilter: 'blur(10px)',
          border: '1px solid var(--border-card)',
          padding: '8px 16px',
          borderRadius: 'var(--btn-radius)',
          fontSize: '0.8rem',
          fontWeight: 700,
          color: 'var(--text-primary)',
          pointerEvents: 'none',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}
      >
        <span className="pulse-dot" style={{ background: 'var(--status-healthy)' }} />
        <span>3D AUTOMOTIVE SHOP FLOOR DIGITAL TWIN • CLICK ANY MACHINE TO INSPECT</span>
      </div>

      {/* Bottom Machine Quick Cards Overlay */}
      <div
        style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          right: '16px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
          pointerEvents: 'auto',
        }}
      >
        {machines.map((m) => {
          const isCritical = m.health_status === 'critical' || m.trigger_active;
          const isWarning = m.health_status === 'warning';
          const statusColor = isCritical
            ? 'var(--status-critical)'
            : isWarning
            ? 'var(--status-warning)'
            : 'var(--status-healthy)';

          return (
            <div
              key={m.machine_id}
              onClick={() => navigate(`/machine/${m.machine_id}`)}
              style={{
                background: 'rgba(14, 20, 36, 0.88)',
                backdropFilter: 'blur(12px)',
                border: `1px solid ${isCritical ? 'rgba(239, 68, 68, 0.5)' : 'var(--border-card)'}`,
                padding: '10px 14px',
                borderRadius: 'var(--btn-radius)',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-blue)')}
              onMouseLeave={(e) =>
                (e.currentTarget.style.borderColor = isCritical ? 'rgba(239, 68, 68, 0.5)' : 'var(--border-card)')
              }
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', fontWeight: 800, color: 'var(--accent-blue)' }}>
                  {m.machine_id}
                </span>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: statusColor }}>
                  {m.health_score}%
                </span>
              </div>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {m.name}
              </div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Click to open 3D Workbench →
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
