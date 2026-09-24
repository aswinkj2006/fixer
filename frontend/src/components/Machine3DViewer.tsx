/**
 * Machine 3D Viewer — CCTV-Style Industrial Equipment Viewer
 *
 * Slim orchestrator (~190 lines) that composes:
 *   - sceneFactory  → shared renderer, lights, environment, post-processing
 *   - cameraPresets → fixed per-machine camera angles
 *   - materials     → PBR material palette
 *   - models/*      → per-machine model builders
 *   - meshUtils     → andon beacon, greebles
 */
import { useEffect, useRef, useState } from 'react';
import type { FC } from 'react';
import * as THREE from 'three';

import { createIndustrialScene } from '../three/sceneFactory';
import { getCameraLabel } from '../three/cameraPresets';
import { createAndonBeacon } from '../three/meshUtils';
import type { MachineModelBuilder } from '../three/models/types';
import { buildM01 } from '../three/models/buildM01';
import { buildM02 } from '../three/models/buildM02';
import { buildM03 } from '../three/models/buildM03';
import { buildM04 } from '../three/models/buildM04';

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Model builder registry                                                   */
/* ═══════════════════════════════════════════════════════════════════════════ */

const MODEL_BUILDERS: Record<string, MachineModelBuilder> = {
  'M-01': buildM01,
  'M-02': buildM02,
  'M-03': buildM03,
  'M-04': buildM04,
};

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Component                                                                */
/* ═══════════════════════════════════════════════════════════════════════════ */

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
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [timestamp, setTimestamp] = useState('');

  // Mutable state for animation loop
  const stateRef = useRef({ isFaultActive, isRepairing, readings });
  useEffect(() => {
    stateRef.current = { isFaultActive, isRepairing, readings };
  }, [isFaultActive, isRepairing, readings]);

  // Timestamp ticker
  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTimestamp(
        now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) +
        '  ' +
        now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      );
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  // ── Three.js scene lifecycle ──
  useEffect(() => {
    if (!canvasRef.current || !containerRef.current) return;

    // Create shared industrial scene
    const { scene, controls, composer, faultLight, dispose } = createIndustrialScene(
      canvasRef.current,
      containerRef.current,
      machineId,
    );

    // Build machine model
    const builder = MODEL_BUILDERS[machineId] ?? buildM01;
    const model = builder(scene);

    // Add andon beacon
    const beacon = createAndonBeacon([-1.8, 0, -1.8]);
    scene.add(beacon.group);

    // Animation loop
    let animId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      const fault = stateRef.current.isFaultActive;
      const repairing = stateRef.current.isRepairing;

      controls.update();

      // Beacon animation
      if (repairing) {
        beacon.redMat.color.setHex(0x440000);
        beacon.greenMat.color.setHex(0x004400);
        beacon.yellowMat.color.setHex(Math.sin(t * 12) > 0 ? 0xf59e0b : 0x443300);
      } else if (fault) {
        beacon.greenMat.color.setHex(0x004400);
        beacon.yellowMat.color.setHex(0x443300);
        beacon.redMat.color.setHex(Math.sin(t * 10) > 0 ? 0xef4444 : 0x440000);
      } else {
        beacon.redMat.color.setHex(0x440000);
        beacon.yellowMat.color.setHex(0x443300);
        beacon.greenMat.color.setHex(0x10b981);
      }

      // Machine-specific animation + fault effects
      model.animateTick(t, fault, repairing);

      // Dynamic fault light
      if (repairing) {
        faultLight.color.setHex(0x06b6d4);
        faultLight.intensity = (Math.sin(t * 4) + 1) * 1.5;
        faultLight.position.copy(model.faultLightPosition);
      } else if (fault) {
        faultLight.color.setHex(0xef4444);
        faultLight.intensity = 2.5;
        faultLight.position.copy(model.faultLightPosition);
      } else {
        faultLight.intensity = 0;
      }

      // Render via EffectComposer (SSAO + Bloom)
      composer.render();
    };

    animate();

    return () => {
      cancelAnimationFrame(animId);
      dispose();
    };
  }, [machineId]);

  const cameraLabel = getCameraLabel(machineId);

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        width: '100%',
        height,
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
        border: isFaultActive
          ? '2px solid rgba(239, 68, 68, 0.7)'
          : isRepairing
          ? '2px solid rgba(6, 182, 212, 0.8)'
          : '1px solid rgba(30, 41, 59, 0.6)',
        transition: 'border-color 0.3s ease',
        background: '#0a0e18',
      }}
    >
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block', cursor: 'grab' }} />

      {/* CCTV Scanlines */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)',
          mixBlendMode: 'multiply',
        }}
      />

      {/* REC indicator */}
      <div
        style={{
          position: 'absolute',
          top: '14px',
          left: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            background: '#ef4444',
            boxShadow: '0 0 8px rgba(239, 68, 68, 0.8)',
            animation: 'cctv-blink 1.2s infinite',
          }}
        />
        <span
          style={{
            fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
            fontSize: '0.72rem',
            fontWeight: 700,
            color: '#ef4444',
            letterSpacing: '0.12em',
            textShadow: '0 0 8px rgba(239, 68, 68, 0.5)',
          }}
        >
          ● REC
        </span>
      </div>

      {/* Camera Label */}
      <div
        style={{
          position: 'absolute',
          top: '14px',
          right: '14px',
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '0.68rem',
          fontWeight: 600,
          color: 'rgba(255,255,255,0.55)',
          letterSpacing: '0.05em',
          pointerEvents: 'none',
          textShadow: '0 1px 4px rgba(0,0,0,0.8)',
        }}
      >
        {cameraLabel}
      </div>

      {/* Timestamp */}
      <div
        style={{
          position: 'absolute',
          bottom: '14px',
          left: '14px',
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '0.72rem',
          fontWeight: 600,
          color: 'rgba(255,255,255,0.6)',
          letterSpacing: '0.08em',
          pointerEvents: 'none',
          textShadow: '0 1px 4px rgba(0,0,0,0.8)',
        }}
      >
        {timestamp}
      </div>

      {/* Status badge */}
      <div
        style={{
          position: 'absolute',
          bottom: '14px',
          right: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 10px',
          borderRadius: '6px',
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(4px)',
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            width: '7px',
            height: '7px',
            borderRadius: '50%',
            background: isFaultActive ? '#ef4444' : isRepairing ? '#06b6d4' : '#10b981',
            boxShadow: `0 0 6px ${isFaultActive ? '#ef4444' : isRepairing ? '#06b6d4' : '#10b981'}`,
          }}
        />
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '0.65rem',
            fontWeight: 700,
            color: isFaultActive ? '#ef4444' : isRepairing ? '#06b6d4' : '#10b981',
            letterSpacing: '0.06em',
          }}
        >
          {isRepairing ? 'REPAIRING' : isFaultActive ? 'FAULT DETECTED' : 'OPERATIONAL'}
        </span>
      </div>

      {/* Corner brackets */}
      {['tl', 'tr', 'bl', 'br'].map((c) => (
        <div
          key={c}
          style={{
            position: 'absolute',
            ...(c.includes('t') ? { top: '6px' } : { bottom: '6px' }),
            ...(c.includes('l') ? { left: '6px' } : { right: '6px' }),
            width: '20px',
            height: '20px',
            borderColor: 'rgba(255,255,255,0.15)',
            borderStyle: 'solid',
            borderWidth: 0,
            ...(c === 'tl' ? { borderTopWidth: '2px', borderLeftWidth: '2px' } : {}),
            ...(c === 'tr' ? { borderTopWidth: '2px', borderRightWidth: '2px' } : {}),
            ...(c === 'bl' ? { borderBottomWidth: '2px', borderLeftWidth: '2px' } : {}),
            ...(c === 'br' ? { borderBottomWidth: '2px', borderRightWidth: '2px' } : {}),
            pointerEvents: 'none',
          }}
        />
      ))}

      <style>{`@keyframes cctv-blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }`}</style>
    </div>
  );
};
