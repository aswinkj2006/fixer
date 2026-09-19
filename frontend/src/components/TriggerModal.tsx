import { useState, useEffect } from 'react';
import type { FC } from 'react';
import axios from 'axios';

interface TriggerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTriggerChanged: () => void;
}

export const TriggerModal: FC<TriggerModalProps> = ({
  isOpen,
  onClose,
  onTriggerChanged,
}) => {
  const [activeTriggers, setActiveTriggers] = useState<Record<string, any>>({});
  const [loadingMachine, setLoadingMachine] = useState<string | null>(null);

  const fetchTriggers = async () => {
    try {
      const res = await axios.get('/api/admin/triggers', {
        headers: { 'X-Admin-Key': 'fixer-demo-key-2026' }
      });
      setActiveTriggers(res.data.active_triggers || {});
    } catch (e) {
      console.warn('Could not fetch active triggers:', e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchTriggers();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const triggerPresets = [
    {
      machine_id: 'M-01',
      name: 'FANUC ARC Mate 100iD — Welding Robot',
      mode: 1,
      title: 'Mode 1: Reducer Grease Leak (Rising Torque)',
      desc: 'Mimics exponential friction increase from lubrication breakdown in J2/J3 reducer housing. Baseline torque climbs steadily.',
      badge: 'Robotics',
    },
    {
      machine_id: 'M-02',
      name: 'Haas VF-2 CNC Mill — Precision Machining',
      mode: 2,
      title: 'Mode 2: Spindle Bearing Wear (Vibration Growth)',
      desc: 'Mimics accelerated bearing track spallation. Increases vibration noise magnitude (sigma) + shifts vibration baseline upward.',
      badge: 'Precision CNC',
    },
    {
      machine_id: 'M-03',
      name: 'Conveyor Drive Motor — Station 7',
      mode: 3,
      title: 'Mode 3: Developing Motor Stator/Bearing Fault',
      desc: 'Mimics electrical overload and increased mechanical drag. Current draw baseline steps upward + frequent vibration spikes.',
      badge: 'Automotive Conveyance',
    },
  ];

  const handleActivate = async (machine_id: string, mode: number) => {
    setLoadingMachine(machine_id);
    try {
      await axios.post(
        `/api/admin/trigger?machine_id=${machine_id}&mode=${mode}`,
        {},
        { headers: { 'X-Admin-Key': 'fixer-demo-key-2026' } }
      );
      await fetchTriggers();
      onTriggerChanged();
    } catch (e) {
      console.error('Trigger activation failed:', e);
    } finally {
      setLoadingMachine(null);
    }
  };

  const handleDeactivate = async (machine_id: string) => {
    setLoadingMachine(machine_id);
    try {
      await axios.delete(
        `/api/admin/trigger?machine_id=${machine_id}`,
        { headers: { 'X-Admin-Key': 'fixer-demo-key-2026' } }
      );
      await fetchTriggers();
      onTriggerChanged();
    } catch (e) {
      console.error('Trigger deactivation failed:', e);
    } finally {
      setLoadingMachine(null);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(3, 7, 18, 0.75)',
      backdropFilter: 'blur(10px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '20px',
    }}>
      <div style={{
        background: 'var(--bg-card-solid)',
        border: '1px solid var(--border-card)',
        borderRadius: 'var(--card-radius)',
        width: '100%',
        maxWidth: '680px',
        boxShadow: '0 24px 64px rgba(0, 0, 0, 0.35)',
        overflow: 'hidden',
      }}>
        {/* Modal Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid var(--border-card)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'var(--bg-card-subtle)',
        }}>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
              <span>⚡</span> Hidden Anomaly Injection Panel
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0, marginTop: '2px' }}>
              Gradual physical fault escalation presets for live demo validation
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '1.4rem',
              cursor: 'pointer',
              lineHeight: 1,
              padding: '4px',
            }}
          >
            ×
          </button>
        </div>

        {/* Presets List */}
        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {triggerPresets.map((preset) => {
            const isActive = !!activeTriggers[preset.machine_id];
            const triggerInfo = activeTriggers[preset.machine_id];

            return (
              <div
                key={preset.machine_id}
                style={{
                  padding: '16px 20px',
                  borderRadius: 'var(--btn-radius)',
                  background: isActive ? 'rgba(239, 68, 68, 0.08)' : 'var(--bg-card-subtle)',
                  border: `1px solid ${isActive ? 'rgba(239, 68, 68, 0.35)' : 'var(--border-card)'}`,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '16px',
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{
                      fontWeight: 700,
                      fontSize: '0.78rem',
                      background: 'rgba(37, 99, 235, 0.12)',
                      color: 'var(--accent-blue)',
                      padding: '2px 8px',
                      borderRadius: 'var(--btn-radius)',
                      border: '1px solid rgba(37, 99, 235, 0.25)',
                    }}>
                      {preset.machine_id}
                    </span>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                      {preset.title}
                    </h3>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                    {preset.desc}
                  </p>
                  {isActive && (
                    <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.74rem', color: 'var(--status-critical)' }}>
                      <span className="pulse-dot" style={{ background: '#ef4444' }} />
                      <span>Fault Active & Escalating (Simulation Tick: {triggerInfo?.t_since_trigger ? Math.round(triggerInfo.t_since_trigger) : 0})</span>
                    </div>
                  )}
                </div>

                <div>
                  {isActive ? (
                    <button
                      className="btn-secondary"
                      onClick={() => handleDeactivate(preset.machine_id)}
                      disabled={loadingMachine === preset.machine_id}
                      style={{ padding: '8px 14px', fontSize: '0.8rem', color: 'var(--accent-blue)' }}
                    >
                      {loadingMachine === preset.machine_id ? 'Resetting...' : 'Reset to Normal'}
                    </button>
                  ) : (
                    <button
                      className="btn-primary"
                      onClick={() => handleActivate(preset.machine_id, preset.mode)}
                      disabled={loadingMachine === preset.machine_id}
                      style={{ padding: '8px 16px', fontSize: '0.8rem' }}
                    >
                      {loadingMachine === preset.machine_id ? 'Injecting...' : 'Trigger Fault'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Modal Footer */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid var(--border-card)',
          background: 'var(--bg-card-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            ℹ️ Failure curves develop gradually (OU drift compresses weeks into demo minutes).
          </span>
          <button className="btn-secondary" onClick={onClose} style={{ padding: '8px 18px', fontSize: '0.82rem' }}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
