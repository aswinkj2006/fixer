import type { FC } from 'react';
import { Link } from 'react-router-dom';

interface NavbarProps {
  wsConnected: boolean;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}

export const Navbar: FC<NavbarProps> = ({
  wsConnected,
  theme,
  onToggleTheme,
}) => {
  return (
    <header style={{
      borderBottom: '1px solid var(--border-card)',
      background: 'var(--navbar-bg)',
      backdropFilter: 'blur(16px)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '12px 28px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      transition: 'background-color 0.2s ease, border-color 0.2s ease',
    }}>
      {/* Brand */}
      <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: 'var(--btn-radius)',
          background: 'linear-gradient(135deg, #0284c7 0%, #2563eb 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 800,
          color: '#ffffff',
          fontSize: '1.2rem',
          boxShadow: '0 2px 10px rgba(37, 99, 235, 0.35)',
        }}>
          F
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
              fixer<span style={{ color: 'var(--accent-cyan)' }}>.ai</span>
            </span>
            <span style={{
              fontSize: '0.68rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              background: 'rgba(37, 99, 235, 0.12)',
              color: 'var(--accent-blue)',
              padding: '2px 7px',
              borderRadius: 'var(--btn-radius)',
              border: '1px solid rgba(37, 99, 235, 0.25)',
            }}>
              Industrial Fleet AI
            </span>
          </div>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', margin: 0 }}>
            Predictive Maintenance & Machine Advisory
          </p>
        </div>
      </Link>

      {/* Right controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* WebSocket status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 12px',
          borderRadius: 'var(--btn-radius)',
          background: wsConnected ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          border: `1px solid ${wsConnected ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)'}`,
          fontSize: '0.75rem',
          fontWeight: 600,
          color: wsConnected ? 'var(--status-healthy)' : 'var(--status-critical)',
        }}>
          <span className="pulse-dot" style={{ background: wsConnected ? '#10b981' : '#ef4444' }} />
          <span>{wsConnected ? 'Live Telemetry' : 'Connecting...'}</span>
        </div>

        {/* Light / Dark Mode Toggle */}
        <button
          id="btn-theme-toggle"
          type="button"
          onClick={onToggleTheme}
          className="btn-secondary"
          style={{ padding: '8px 14px', fontSize: '0.82rem' }}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
        >
          <span>{theme === 'dark' ? '☀️' : '🌙'}</span>
          <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
        </button>
      </div>
    </header>
  );
};
