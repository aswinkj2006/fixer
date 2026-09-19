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

  const statusColor = isHealthy ? 'var(--status-healthy)' : isWarning ? 'var(--status-warning)' : 'var(--status-critical)';
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
          padding: '22px',
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
            boxShadow: '0 0 10px #ef4444',
          }} />
        )}

        {/* Card Header */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.82rem',
                fontWeight: 700,
                background: 'var(--bg-card-subtle)',
                padding: '3px 9px',
                borderRadius: 'var(--btn-radius)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-card)',
              }}>
                {machine.machine_id}
              </span>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                {machine.location}
              </span>
            </div>

            {/* Status Slightly Rounded Rectangle Badge */}
            <div className={badgeClass} style={{
              padding: '3px 9px',
              borderRadius: 'var(--btn-radius)',
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

          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px', lineHeight: 1.3 }}>
            {machine.name}
          </h3>
          <p style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Model: <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{machine.model}</span>
          </p>

          {/* Health Score and RUL Row */}
          <div style={{
            background: 'var(--bg-card-subtle)',
            borderRadius: 'var(--btn-radius)',
            padding: '14px 16px',
            marginBottom: '16px',
            border: '1px solid var(--border-card)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Health Score
              </span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                <span style={{ fontSize: '1.75rem', fontWeight: 800, color: statusColor, lineHeight: 1 }}>
                  {machine.health_score}
                </span>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>/ 100</span>
              </div>
            </div>

            {/* Service window pill */}
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Predicted Service
              </span>
              <div style={{
                fontSize: '0.82rem',
                fontWeight: 600,
                color: isCritical ? '#ef4444' : isWarning ? '#f59e0b' : 'var(--text-primary)',
                marginTop: '2px',
              }}>
                {machine.predicted_service_window}
              </div>
            </div>
          </div>

          {/* Live Sensor Pills */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '16px' }}>
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
                    borderRadius: 'var(--btn-radius)',
                    background: 'var(--bg-card-subtle)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <span style={{ color: 'var(--text-secondary)' }}>{cfg.label}</span>
                  <span className="telemetry-val" style={{ color: isFlag && val > 0.5 ? 'var(--accent-cyan)' : 'var(--text-primary)' }}>
                    {displayVal} <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{cfg.unit}</span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Card Footer: OEE & Open Tickets */}
        <div style={{
          paddingTop: '12px',
          borderTop: '1px solid var(--border-card)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.75rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: 'var(--text-muted)' }}>OEE:</span>
            <span style={{ fontWeight: 700, color: 'var(--accent-blue)' }}>{machine.oee_pct}%</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-blue)', fontWeight: 600 }}>
            <span>{machine.open_tickets > 0 ? `⚠️ ${machine.open_tickets} Open Ticket` : '✓ All Systems Go'}</span>
          </div>
        </div>
      </div>
    </Link>
  );
};
