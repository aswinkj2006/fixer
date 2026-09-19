import type { FC } from 'react';
import { Link } from 'react-router-dom';

interface NavbarProps {
  wsConnected: boolean;
  onOpenTriggerModal: () => void;
  activeTriggerCount: number;
}

export const Navbar: FC<NavbarProps> = ({
  wsConnected,
  onOpenTriggerModal,
  activeTriggerCount,
}) => {
  return (
    <header style={{
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      background: 'rgba(7, 10, 19, 0.85)',
      backdropFilter: 'blur(16px)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '14px 28px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
    }}>
      {/* Brand */}
      <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #06b6d4 0%, #4f46e5 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 800,
          color: '#ffffff',
          fontSize: '1.2rem',
          boxShadow: '0 0 16px rgba(6, 182, 212, 0.4)',
        }}>
          F
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
              fixer<span style={{ color: '#06b6d4' }}>.ai</span>
            </span>
            <span style={{
              fontSize: '0.68rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              background: 'rgba(99, 102, 241, 0.16)',
              color: '#818cf8',
              padding: '2px 7px',
              borderRadius: '6px',
              border: '1px solid rgba(99, 102, 241, 0.3)',
            }}>
              Industrial Fleet AI
            </span>
          </div>
          <p style={{ fontSize: '0.72rem', color: '#94a3b8', margin: 0 }}>
            Offline Prognostics & Multimodal Machine Advisory
          </p>
        </div>
      </Link>

      {/* Center status: Offline local AI badge */}
      <div style={{
        display: 'none',
        alignItems: 'center',
        gap: '8px',
        background: 'rgba(15, 23, 42, 0.6)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        padding: '6px 14px',
        borderRadius: '20px',
        fontSize: '0.76rem',
        color: '#cbd5e1',
      }} className="desktop-indicator">
        <span style={{ color: '#10b981' }}>⚡</span>
        <span>Local Air-Gapped Stack: <strong>whisper.cpp • Gemma 3 4B • Phi-4 • nomic-embed</strong></span>
      </div>

      {/* Right controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* WebSocket status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 12px',
          borderRadius: '20px',
          background: wsConnected ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          border: `1px solid ${wsConnected ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)'}`,
          fontSize: '0.75rem',
          fontWeight: 600,
          color: wsConnected ? '#34d399' : '#f87171',
        }}>
          <span className="pulse-dot" style={{ background: wsConnected ? '#10b981' : '#ef4444' }} />
          <span>{wsConnected ? 'Live Telemetry Stream' : 'Connecting Stream...'}</span>
        </div>

        {/* Anomaly trigger button */}
        <button
          id="btn-open-triggers"
          onClick={onOpenTriggerModal}
          className={activeTriggerCount > 0 ? 'btn-danger' : 'btn-secondary'}
          style={{ padding: '8px 16px', fontSize: '0.82rem' }}
        >
          <span>⚡ Anomaly Simulator</span>
          {activeTriggerCount > 0 && (
            <span style={{
              background: '#ffffff',
              color: '#dc2626',
              borderRadius: '50%',
              padding: '1px 6px',
              fontSize: '0.72rem',
              fontWeight: 800,
            }}>
              {activeTriggerCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
};
