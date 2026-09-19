import type { FC } from 'react';
import { Link } from 'react-router-dom';
import type { Machine } from '../types';

interface MachineCardProps {
  machine: Machine;
}

export const MachineCard: FC<MachineCardProps> = ({ machine }) => {
  const isHealthy = machine.health_status === 'healthy';
  const isWarning = machine.health_status === 'warning';
  const isCritical = machine.health_status === 'critical';

  const statusColor = isHealthy ? '#10b981' : isWarning ? '#f59e0b' : '#ef4444';
  const badgeClass = isHealthy ? 'badge-healthy' : isWarning ? 'badge-warning' : 'badge-critical';

  // Format sensor key names and units for display
  const sensorConfigs: Record<string, { label: string; unit: string }> = {
    torque: { label: 'Axis Torque', unit: 'Nm' },
    vibration: { label: 'Vibration', unit: 'mm/s²' },
    cycle_count: { label: 'Cycle Status', unit: '' },
    temperature: { label: 'Spindle / Motor Temp', unit: '°C' },
    rpm: { label: 'Spindle Speed', unit: 'RPM' },
    current: { label: 'Current Draw', unit: 'A' },
    calibration_dev: { label: 'Calibration Offset', unit: 'Nm offset' },
  };

  return (
    <Link
      to={`/machine/${machine.machine_id}`}
      style={{ textDecoration: 'none', color: 'inherit' }}
      id={`card-${machine.machine_id.toLowerCase()}`}
    >
      <div
        className="glass-panel"
        style={{
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          height: '100%',
          cursor: 'pointer',
          position: 'relative',
          overflow: 'hidden',
          borderColor: isCritical ? 'rgba(239, 68, 68, 0.4)' : undefined,
        }}
      >
        {/* Top active trigger glow strip */}
        {machine.trigger_active && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '3px',
            background: 'linear-gradient(90deg, #ef4444 0%, #f59e0b 100%)',
            boxShadow: '0 0 12px #ef4444',
          }} />
        )}

        {/* Card Header */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem',
                fontWeight: 700,
                background: 'rgba(255, 255, 255, 0.08)',
                padding: '3px 10px',
                borderRadius: '8px',
                color: '#e2e8f0',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}>
                {machine.machine_id}
              </span>
              <span style={{ fontSize: '0.74rem', color: '#94a3b8' }}>
                {machine.location}
              </span>
            </div>

            {/* Status Pill */}
            <div className={badgeClass} style={{
              padding: '3px 10px',
              borderRadius: '20px',
              fontSize: '0.72rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}>
              <span className="pulse-dot" style={{ background: statusColor, width: '6px', height: '6px' }} />
              {machine.health_status}
            </div>
          </div>

          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', marginBottom: '4px', lineHeight: 1.3 }}>
            {machine.name}
          </h3>
          <p style={{ fontSize: '0.76rem', color: '#64748b', marginBottom: '18px' }}>
            Model: <span style={{ fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>{machine.model}</span>
          </p>

          {/* Health Score and OEE Bar Row */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.25)',
            borderRadius: '12px',
            padding: '14px 16px',
            marginBottom: '18px',
            border: '1px solid rgba(255, 255, 255, 0.04)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Health Score
              </span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                <span style={{ fontSize: '1.75rem', fontWeight: 800, color: statusColor, lineHeight: 1 }}>
                  {machine.health_score}
                </span>
                <span style={{ fontSize: '0.85rem', color: '#64748b' }}>/ 100</span>
              </div>
            </div>

            {/* Service window pill */}
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Predicted Service
              </span>
              <div style={{
                fontSize: '0.82rem',
                fontWeight: 600,
                color: isCritical ? '#f87171' : isWarning ? '#fbbf24' : '#e2e8f0',
                marginTop: '2px',
              }}>
                {machine.predicted_service_window}
              </div>
            </div>
          </div>

          {/* Live Sensor Pills */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '18px' }}>
            {Object.entries(machine.current_readings).map(([stype, val]) => {
              const cfg = sensorConfigs[stype] || { label: stype, unit: '' };
              const isFlag = stype === 'cycle_count';
              const displayVal = isFlag ? (val > 0.5 ? 'WELDING' : 'IDLE') : typeof val === 'number' ? val.toFixed(2) : val;

              return (
                <div
                  key={stype}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '0.78rem',
                    padding: '6px 10px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid rgba(255, 255, 255, 0.04)',
                  }}
                >
                  <span style={{ color: '#94a3b8' }}>{cfg.label}</span>
                  <span className="telemetry-val" style={{ color: isFlag && val > 0.5 ? '#38bdf8' : '#f1f5f9' }}>
                    {displayVal} <span style={{ fontSize: '0.7rem', color: '#64748b' }}>{cfg.unit}</span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Card Footer: OEE & Open Tickets */}
        <div style={{
          paddingTop: '12px',
          borderTop: '1px solid rgba(255, 255, 255, 0.06)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.75rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: '#64748b' }}>OEE:</span>
            <span style={{ fontWeight: 700, color: '#38bdf8' }}>{machine.oee_pct}%</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#a5b4fc', fontWeight: 600 }}>
            <span>Open Tickets: {machine.open_tickets}</span>
            <span>→</span>
          </div>
        </div>
      </div>
    </Link>
  );
};
