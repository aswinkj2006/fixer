import { useState, useEffect } from 'react';
import type { FC } from 'react';
import axios from 'axios';

interface SimMachine {
  machine_id: string;
  name: string;
  health_score: number;
  health_status: string;
  trigger_active: boolean;
  current_readings: Record<string, number>;
}

export const SimulationControl: FC = () => {
  const [machines, setMachines] = useState<SimMachine[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [messages, setMessages] = useState<Record<string, { text: string; type: 'success' | 'error' }>>({});

  const fetchMachines = async () => {
    try {
      const res = await axios.get('/api/machines');
      setMachines(res.data || []);
    } catch (e) {
      console.warn('Failed to load machines:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMachines();
    const timer = setInterval(fetchMachines, 3000);
    return () => clearInterval(timer);
  }, []);

  const handleInjectFault = async (machineId: string) => {
    setActionLoading((prev) => ({ ...prev, [machineId]: true }));
    setMessages((prev) => ({ ...prev, [machineId]: undefined as any }));
    try {
      await axios.post(`/api/machines/${machineId}/fault`);
      setMessages((prev) => ({ ...prev, [machineId]: { text: 'Fault injected successfully', type: 'success' } }));
      fetchMachines();
    } catch (e: any) {
      setMessages((prev) => ({
        ...prev,
        [machineId]: { text: e?.response?.data?.detail || 'Failed to inject fault', type: 'error' },
      }));
    } finally {
      setActionLoading((prev) => ({ ...prev, [machineId]: false }));
    }
  };

  const handleRepair = async (machineId: string) => {
    setActionLoading((prev) => ({ ...prev, [machineId]: true }));
    setMessages((prev) => ({ ...prev, [machineId]: undefined as any }));
    try {
      const res = await axios.post(`/api/machines/${machineId}/fix`, {
        technician_notes: 'Repair executed via simulation control panel',
        technician_id: 'Sim-Panel',
      });
      setMessages((prev) => ({
        ...prev,
        [machineId]: { text: res.data.remedy || 'Machine repaired & sensors normalized', type: 'success' },
      }));
      fetchMachines();
    } catch (e: any) {
      setMessages((prev) => ({
        ...prev,
        [machineId]: { text: e?.response?.data?.detail || 'Failed to repair', type: 'error' },
      }));
    } finally {
      setActionLoading((prev) => ({ ...prev, [machineId]: false }));
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '60px 20px', textAlign: 'center', color: '#94a3b8', fontFamily: 'monospace' }}>
        Loading simulation control...
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#0a0f1d',
        color: '#e2e8f0',
        fontFamily: "'Inter', 'SF Pro Display', system-ui, sans-serif",
        padding: '40px 24px',
      }}
    >
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '32px' }}>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
            Simulation Control Panel
          </h1>
          <p style={{ fontSize: '0.82rem', color: '#64748b', margin: '6px 0 0' }}>
            Inject faults and trigger repairs for demo scenarios. This page is not linked from the main app.
          </p>
        </div>

        {/* Machine Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {machines.map((m) => {
            const isFault = m.trigger_active;
            const isLoading = actionLoading[m.machine_id];
            const msg = messages[m.machine_id];

            return (
              <div
                key={m.machine_id}
                style={{
                  background: '#111827',
                  border: `1px solid ${isFault ? 'rgba(239, 68, 68, 0.4)' : '#1e293b'}`,
                  borderRadius: '10px',
                  padding: '20px 24px',
                }}
              >
                {/* Machine Info Row */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span
                      style={{
                        fontFamily: 'monospace',
                        fontSize: '0.8rem',
                        fontWeight: 700,
                        background: '#1e293b',
                        color: '#38bdf8',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        border: '1px solid #334155',
                      }}
                    >
                      {m.machine_id}
                    </span>
                    <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f1f5f9' }}>
                      {m.name}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {/* Health Score */}
                    <span
                      style={{
                        fontSize: '0.82rem',
                        fontWeight: 700,
                        color: m.health_score >= 85 ? '#10b981' : m.health_score >= 60 ? '#f59e0b' : '#ef4444',
                      }}
                    >
                      Health: {m.health_score}%
                    </span>

                    {/* Status Badge */}
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        padding: '3px 10px',
                        borderRadius: '6px',
                        background: isFault ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                        color: isFault ? '#ef4444' : '#10b981',
                        border: `1px solid ${isFault ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                      }}
                    >
                      {isFault ? '⚠ Fault Active' : '● Normal'}
                    </span>
                  </div>
                </div>

                {/* Sensor Readings */}
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '14px' }}>
                  {Object.entries(m.current_readings)
                    .filter(([k]) => k !== 'cycle_count')
                    .map(([key, val]) => (
                      <div
                        key={key}
                        style={{
                          background: '#0f172a',
                          padding: '6px 10px',
                          borderRadius: '6px',
                          border: '1px solid #1e293b',
                          fontSize: '0.72rem',
                        }}
                      >
                        <span style={{ color: '#64748b', textTransform: 'capitalize' }}>{key}: </span>
                        <span style={{ color: '#e2e8f0', fontWeight: 600, fontFamily: 'monospace' }}>
                          {typeof val === 'number' ? val.toFixed(2) : val}
                        </span>
                      </div>
                    ))}
                </div>

                {/* Action Buttons */}
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => handleInjectFault(m.machine_id)}
                    disabled={isLoading || isFault}
                    style={{
                      padding: '8px 18px',
                      borderRadius: '8px',
                      border: '1px solid #334155',
                      background: isFault ? '#1e293b' : '#1e293b',
                      color: isFault ? '#475569' : '#f59e0b',
                      fontSize: '0.82rem',
                      fontWeight: 600,
                      cursor: isLoading || isFault ? 'not-allowed' : 'pointer',
                      opacity: isFault ? 0.5 : 1,
                      transition: 'all 0.15s ease',
                    }}
                  >
                    ⚡ Inject Fault
                  </button>

                  <button
                    onClick={() => handleRepair(m.machine_id)}
                    disabled={isLoading || !isFault}
                    style={{
                      padding: '8px 18px',
                      borderRadius: '8px',
                      border: 'none',
                      background: isFault
                        ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                        : '#1e293b',
                      color: isFault ? '#ffffff' : '#475569',
                      fontSize: '0.82rem',
                      fontWeight: 700,
                      cursor: isLoading || !isFault ? 'not-allowed' : 'pointer',
                      opacity: !isFault ? 0.5 : 1,
                      boxShadow: isFault ? '0 2px 10px rgba(16, 185, 129, 0.25)' : 'none',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    🔧 Repair & Restore
                  </button>
                </div>

                {/* Message */}
                {msg && (
                  <div
                    style={{
                      marginTop: '10px',
                      padding: '8px 14px',
                      borderRadius: '6px',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      background: msg.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                      color: msg.type === 'success' ? '#10b981' : '#ef4444',
                      border: `1px solid ${msg.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                    }}
                  >
                    {msg.text}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
