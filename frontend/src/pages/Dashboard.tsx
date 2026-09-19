import { useState, useEffect } from 'react';
import type { FC } from 'react';
import axios from 'axios';
import type { Machine, FleetLeaderboardItem } from '../types';
import { MachineCard } from '../components/MachineCard';
import { TriggerModal } from '../components/TriggerModal';

interface DashboardProps {
  machines: Machine[];
  onRefresh: () => void;
  isModalOpen: boolean;
  onCloseModal: () => void;
}

export const Dashboard: FC<DashboardProps> = ({
  machines,
  onRefresh,
  isModalOpen,
  onCloseModal,
}) => {
  const [leaderboard, setLeaderboard] = useState<FleetLeaderboardItem[]>([]);
  const [loadingLeaderboard, setLoadingLeaderboard] = useState(false);

  const fetchLeaderboard = async () => {
    setLoadingLeaderboard(true);
    try {
      const res = await axios.get('/api/fleet/recurring-faults');
      setLeaderboard(res.data.leaderboard || []);
    } catch (e) {
      console.warn('Failed to load fleet leaderboard:', e);
    } finally {
      setLoadingLeaderboard(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  // Compute fleet KPIs
  const totalMachines = machines.length;
  const avgHealth = totalMachines > 0
    ? Math.round(machines.reduce((acc, m) => acc + m.health_score, 0) / totalMachines)
    : 100;
  const avgOee = totalMachines > 0
    ? (machines.reduce((acc, m) => acc + m.oee_pct, 0) / totalMachines).toFixed(1)
    : '94.0';
  const activeAlerts = machines.filter((m) => m.health_status === 'critical' || m.trigger_active).length;

  return (
    <main style={{ maxWidth: '1440px', margin: '0 auto', padding: '32px 28px' }}>
      {/* Executive Fleet KPI Banner */}
      <section style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '20px',
        marginBottom: '36px',
      }}>
        <div className="glass-panel" style={{ padding: '22px 24px' }}>
          <span style={{ fontSize: '0.74rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Fleet Health Index
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
            <span style={{
              fontSize: '2.2rem',
              fontWeight: 800,
              color: avgHealth >= 85 ? '#10b981' : avgHealth >= 60 ? '#f59e0b' : '#ef4444',
            }}>
              {avgHealth}%
            </span>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              {avgHealth >= 85 ? 'Nominal Fleet Condition' : 'Anomalies Detected'}
            </span>
          </div>
          <div style={{
            marginTop: '10px',
            height: '4px',
            borderRadius: '2px',
            background: 'rgba(255, 255, 255, 0.08)',
            overflow: 'hidden',
          }}>
            <div style={{
              width: `${avgHealth}%`,
              height: '100%',
              background: avgHealth >= 85 ? '#10b981' : avgHealth >= 60 ? '#f59e0b' : '#ef4444',
            }} />
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '22px 24px' }}>
          <span style={{ fontSize: '0.74rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Overall Equipment Effectiveness (OEE)
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
            <span style={{ fontSize: '2.2rem', fontWeight: 800, color: '#38bdf8' }}>
              {avgOee}%
            </span>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Target: 85%+ (World Class)</span>
          </div>
          <p style={{ fontSize: '0.74rem', color: '#64748b', margin: 0, marginTop: '8px' }}>
            Availability × Performance × Quality composite
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '22px 24px' }}>
          <span style={{ fontSize: '0.74rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Active Anomalies & Injections
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
            <span style={{
              fontSize: '2.2rem',
              fontWeight: 800,
              color: activeAlerts > 0 ? '#ef4444' : '#34d399',
            }}>
              {activeAlerts}
            </span>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              {activeAlerts > 0 ? 'Urgent Review Required' : 'Zero Active Faults'}
            </span>
          </div>
          <p style={{ fontSize: '0.74rem', color: '#64748b', margin: 0, marginTop: '8px' }}>
            Monitored by local Ornstein-Uhlenbeck sensors
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '22px 24px' }}>
          <span style={{ fontSize: '0.74rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Monitored Asset Fleet
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
            <span style={{ fontSize: '2.2rem', fontWeight: 800, color: '#a78bfa' }}>
              4 / 4
            </span>
            <span style={{ fontSize: '0.8rem', color: '#34d399' }}>● 100% Online</span>
          </div>
          <p style={{ fontSize: '0.74rem', color: '#64748b', margin: 0, marginTop: '8px' }}>
            FANUC Robot, Haas CNC, Conveyor, Metrology
          </p>
        </div>
      </section>

      {/* Fleet Machinery Grid Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            Fleet Condition & Telemetry Grid
          </h2>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', margin: 0 }}>
            Real-time multi-sensor prognostic scoring per machine instance
          </p>
        </div>

        <button className="btn-secondary" onClick={onRefresh} style={{ padding: '8px 16px', fontSize: '0.82rem' }}>
          ↻ Refresh Fleet
        </button>
      </div>

      {/* 4-Machine Grid */}
      <section style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(310px, 1fr))',
        gap: '24px',
        marginBottom: '48px',
      }}>
        {machines.map((machine) => (
          <MachineCard key={machine.machine_id} machine={machine} />
        ))}
      </section>

      {/* Fleet Recurring Faults Leaderboard */}
      <section className="glass-panel" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '1.2rem' }}>🧠</span>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.01em', margin: 0 }}>
                Fleet Recurring Faults Leaderboard (Tier 2 Semantic Memory)
              </h2>
            </div>
            <p style={{ fontSize: '0.82rem', color: '#94a3b8', margin: 0, marginTop: '4px' }}>
              Surfaces patterns across the plant and identifies the longest-lasting historical remedies
            </p>
          </div>

          <button
            className="btn-secondary"
            onClick={fetchLeaderboard}
            disabled={loadingLeaderboard}
            style={{ padding: '6px 14px', fontSize: '0.78rem' }}
          >
            {loadingLeaderboard ? 'Scanning...' : '↻ Re-cluster'}
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {leaderboard.length === 0 ? (
            <p style={{ fontSize: '0.85rem', color: '#64748b', fontStyle: 'italic', padding: '16px 0' }}>
              No recurring fault clusters detected yet across Tier 2 collections.
            </p>
          ) : (
            leaderboard.map((item) => (
              <div
                key={`${item.machine_id}-${item.rank}`}
                style={{
                  padding: '16px 20px',
                  borderRadius: '12px',
                  background: 'rgba(0, 0, 0, 0.25)',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '20px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1 }}>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    background: item.rank === 1 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(99, 102, 241, 0.15)',
                    color: item.rank === 1 ? '#f87171' : '#a5b4fc',
                    border: `1px solid ${item.rank === 1 ? 'rgba(239, 68, 68, 0.3)' : 'rgba(99, 102, 241, 0.25)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 800,
                    fontSize: '0.85rem',
                  }}>
                    #{item.rank}
                  </div>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                      <span style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        color: '#38bdf8',
                        background: 'rgba(6, 182, 212, 0.1)',
                        padding: '2px 6px',
                        borderRadius: '4px',
                      }}>
                        {item.machine_id}
                      </span>
                      <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                        {item.pattern_name}
                      </h3>
                      {item.failure_code && (
                        <span style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                          [{item.failure_code}]
                        </span>
                      )}
                    </div>
                    <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: 0 }}>
                      💡 Longest-Lasting Fix: <strong style={{ color: '#34d399' }}>{item.longest_lasting_fix}</strong>
                    </p>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span style={{
                    fontSize: '0.76rem',
                    fontWeight: 700,
                    background: 'rgba(245, 158, 11, 0.15)',
                    color: '#fbbf24',
                    padding: '4px 10px',
                    borderRadius: '12px',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                  }}>
                    {item.occurrence_count} Occurrences
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      {/* Trigger Modal */}
      <TriggerModal
        isOpen={isModalOpen}
        onClose={onCloseModal}
        onTriggerChanged={onRefresh}
      />
    </main>
  );
};
