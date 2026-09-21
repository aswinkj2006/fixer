import { useState, useEffect } from 'react';
import type { FC } from 'react';
import axios from 'axios';
import type { Machine, FleetLeaderboardItem, FleetReliability } from '../types';
import { MachineCard } from '../components/MachineCard';
import { TriggerModal } from '../components/TriggerModal';
import { FactoryFloor3DViewer } from '../components/FactoryFloor3DViewer';

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
  const [viewMode, setViewMode] = useState<'cards' | 'floor3d'>('cards');
  const [leaderboard, setLeaderboard] = useState<FleetLeaderboardItem[]>([]);
  const [loadingLeaderboard, setLoadingLeaderboard] = useState(false);
  const [reliability, setReliability] = useState<FleetReliability | null>(null);
  const [reliabilityWindow, setReliabilityWindow] = useState<number>(90);
  const [loadingReliability, setLoadingReliability] = useState(false);

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

  const fetchReliability = async (days = reliabilityWindow) => {
    setLoadingReliability(true);
    try {
      const res = await axios.get(`/api/fleet/reliability?window_days=${days}`);
      setReliability(res.data);
    } catch (e) {
      console.warn('Failed to load fleet reliability:', e);
    } finally {
      setLoadingReliability(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
    fetchReliability(reliabilityWindow);
  }, [reliabilityWindow]);

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
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
            Fleet Health Index
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
            <span style={{
              fontSize: '2.2rem',
              fontWeight: 800,
              color: avgHealth >= 85 ? 'var(--status-healthy)' : avgHealth >= 60 ? 'var(--status-warning)' : 'var(--status-critical)',
            }}>
              {avgHealth}%
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {avgHealth >= 85 ? 'Nominal Fleet Condition' : 'Anomalies Detected'}
            </span>
          </div>
          <div style={{
            marginTop: '10px',
            height: '4px',
            borderRadius: '2px',
            background: 'var(--border-card)',
            overflow: 'hidden',
          }}>
            <div style={{
              width: `${avgHealth}%`,
              height: '100%',
              background: avgHealth >= 85 ? 'var(--status-healthy)' : avgHealth >= 60 ? 'var(--status-warning)' : 'var(--status-critical)',
            }} />
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '22px 24px' }}>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
            Overall Equipment Effectiveness (OEE)
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
            <span style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--accent-blue)' }}>
              {avgOee}%
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Target: 85%+ (World Class)</span>
          </div>
          <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', margin: 0, marginTop: '8px' }}>
            Availability × Performance × Quality composite
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '22px 24px' }}>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
            Active Anomalies & Injections
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
            <span style={{
              fontSize: '2.2rem',
              fontWeight: 800,
              color: activeAlerts > 0 ? 'var(--status-critical)' : 'var(--status-healthy)',
            }}>
              {activeAlerts}
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {activeAlerts > 0 ? 'Urgent Review Required' : 'Zero Active Faults'}
            </span>
          </div>
          <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', margin: 0, marginTop: '8px' }}>
            Monitored by local Ornstein-Uhlenbeck sensors
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '22px 24px' }}>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
            Monitored Asset Fleet
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
            <span style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--accent-violet)' }}>
              4 / 4
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--status-healthy)', fontWeight: 600 }}>● 100% Online</span>
          </div>
          <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', margin: 0, marginTop: '8px' }}>
            FANUC Robot, Haas CNC, Conveyor, Metrology
          </p>
        </div>
      </section>

      {/* Fleet Machinery Header & View Switcher */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Fleet Machinery & Digital Twins
          </h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0 }}>
            Real-time multi-sensor prognostic scoring and 3D digital twin visualization per machine instance
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* View Mode Switcher */}
          <div
            style={{
              display: 'flex',
              background: 'var(--bg-card-subtle)',
              borderRadius: 'var(--btn-radius)',
              padding: '3px',
              border: '1px solid var(--border-card)',
            }}
          >
            <button
              onClick={() => setViewMode('cards')}
              style={{
                padding: '6px 14px',
                borderRadius: '4px',
                border: 'none',
                background: viewMode === 'cards' ? 'var(--accent-blue)' : 'transparent',
                color: viewMode === 'cards' ? '#ffffff' : 'var(--text-muted)',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              📊 Telemetry Grid
            </button>
            <button
              onClick={() => setViewMode('floor3d')}
              style={{
                padding: '6px 14px',
                borderRadius: '4px',
                border: 'none',
                background: viewMode === 'floor3d' ? 'var(--accent-blue)' : 'transparent',
                color: viewMode === 'floor3d' ? '#ffffff' : 'var(--text-muted)',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              🏭 3D Factory Floor
            </button>
          </div>

          <button className="btn-secondary" onClick={onRefresh} style={{ padding: '8px 16px', fontSize: '0.82rem' }}>
            ↻ Refresh Fleet
          </button>
        </div>
      </div>

      {/* Machinery Content: Either 3D Factory Floor or Card Grid */}
      {viewMode === 'floor3d' ? (
        <section style={{ marginBottom: '48px' }}>
          <FactoryFloor3DViewer machines={machines} height="520px" />
        </section>
      ) : (
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
      )}

      {/* ISO 14224 Fleet Reliability & Financial Impact */}
      <section className="glass-panel" style={{ padding: '28px', marginBottom: '40px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '1.25rem' }}>⏱️</span>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.01em', margin: 0 }}>
                ISO 14224 Fleet Reliability & Financial Impact
              </h2>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0, marginTop: '4px' }}>
              Automated MTBF, MTTR, Plant Availability %, and Downtime Cost Avoidance calculations
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>ROLLING WINDOW:</span>
            {[30, 90, 180].map((days) => (
              <button
                key={days}
                onClick={() => setReliabilityWindow(days)}
                style={{
                  padding: '4px 12px',
                  borderRadius: 'var(--btn-radius)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  border: reliabilityWindow === days ? '1px solid var(--accent-blue)' : '1px solid var(--border-card)',
                  background: reliabilityWindow === days ? 'rgba(37, 99, 235, 0.15)' : 'var(--bg-card-subtle)',
                  color: reliabilityWindow === days ? 'var(--accent-blue)' : 'var(--text-secondary)',
                  transition: 'all 0.15s ease',
                }}
              >
                {days}D
              </button>
            ))}
            <button
              className="btn-secondary"
              onClick={() => fetchReliability(reliabilityWindow)}
              disabled={loadingReliability}
              style={{ padding: '4px 12px', fontSize: '0.78rem', marginLeft: '6px' }}
            >
              {loadingReliability ? '...' : '↻'}
            </button>
          </div>
        </div>

        {/* 4 Reliability Metric Cards */}
        {reliability ? (
          <>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
              marginBottom: '24px',
            }}>
              <div style={{
                background: 'var(--bg-card-subtle)',
                padding: '18px 20px',
                borderRadius: 'var(--btn-radius)',
                border: '1px solid var(--border-card)',
              }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                  Plant Availability
                </span>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
                  <span style={{
                    fontSize: '2rem',
                    fontWeight: 800,
                    color: reliability.fleet_availability_pct >= 95 ? 'var(--status-healthy)' : reliability.fleet_availability_pct >= 90 ? 'var(--status-warning)' : 'var(--status-critical)',
                  }}>
                    {reliability.fleet_availability_pct}%
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    ({reliability.fleet_operating_hours} hrs runtime)
                  </span>
                </div>
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                  {reliability.fleet_downtime_hours} hrs recorded downtime
                </p>
              </div>

              <div style={{
                background: 'var(--bg-card-subtle)',
                padding: '18px 20px',
                borderRadius: 'var(--btn-radius)',
                border: '1px solid var(--border-card)',
              }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                  Fleet MTBF (Operating Hours)
                </span>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
                  <span style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-blue)' }}>
                    {reliability.fleet_mtbf_hours}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>hours</span>
                </div>
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                  {reliability.fleet_failures_count} failure events in {reliability.window_days}d
                </p>
              </div>

              <div style={{
                background: 'var(--bg-card-subtle)',
                padding: '18px 20px',
                borderRadius: 'var(--btn-radius)',
                border: '1px solid var(--border-card)',
              }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                  Fleet MTTR (Repair Turnaround)
                </span>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
                  <span style={{
                    fontSize: '2rem',
                    fontWeight: 800,
                    color: reliability.fleet_mttr_hours <= 2.0 ? 'var(--status-healthy)' : 'var(--status-warning)',
                  }}>
                    {reliability.fleet_mttr_hours}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>hours</span>
                </div>
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                  Turnaround per closed ticket
                </p>
              </div>

              <div style={{
                background: 'rgba(16, 185, 129, 0.08)',
                padding: '18px 20px',
                borderRadius: 'var(--btn-radius)',
                border: '1px solid rgba(16, 185, 129, 0.25)',
              }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--status-healthy)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                  Downtime Cost Avoided
                </span>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
                  <span style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-healthy)' }}>
                    ${reliability.total_cost_avoided_usd.toLocaleString()}
                  </span>
                </div>
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                  At $18.5k/hr downtime + AI fast triage
                </p>
              </div>
            </div>

            {/* Recent Downtime Log */}
            <div>
              <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '12px' }}>
                Recent Plant Downtime & Incident Log
              </h3>
              {reliability.recent_fleet_events.length === 0 ? (
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontStyle: 'italic', margin: 0 }}>
                  No downtime events logged in the selected {reliability.window_days}-day period.
                </p>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontSize: '0.8rem',
                    textAlign: 'left',
                  }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--table-border)', color: 'var(--text-muted)' }}>
                        <th style={{ padding: '8px 12px' }}>Asset</th>
                        <th style={{ padding: '8px 12px' }}>Fault Code</th>
                        <th style={{ padding: '8px 12px' }}>Symptom</th>
                        <th style={{ padding: '8px 12px' }}>Downtime</th>
                        <th style={{ padding: '8px 12px' }}>Severity</th>
                        <th style={{ padding: '8px 12px' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reliability.recent_fleet_events.slice(0, 6).map((evt) => (
                        <tr key={evt.ticket_id} style={{ borderBottom: '1px solid var(--table-border)' }}>
                          <td style={{ padding: '10px 12px' }}>
                            <span style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              color: 'var(--accent-blue)',
                              background: 'var(--bg-card-subtle)',
                              padding: '2px 6px',
                              borderRadius: 'var(--btn-radius)',
                              border: '1px solid var(--border-card)',
                            }}>
                              {evt.machine_id}
                            </span>
                          </td>
                          <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                            {evt.failure_code || 'N/A'}
                          </td>
                          <td style={{ padding: '10px 12px', color: 'var(--text-secondary)', maxWidth: '300px' }}>
                            {evt.symptom}
                          </td>
                          <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: 'var(--status-warning)', fontWeight: 600 }}>
                            {evt.duration_hours} hrs
                          </td>
                          <td style={{ padding: '10px 12px' }}>
                            <span style={{
                              fontSize: '0.72rem',
                              fontWeight: 700,
                              textTransform: 'uppercase',
                              padding: '2px 8px',
                              borderRadius: 'var(--btn-radius)',
                              background: evt.severity === 'critical' ? 'rgba(239, 68, 68, 0.15)' : evt.severity === 'high' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(37, 99, 235, 0.12)',
                              color: evt.severity === 'critical' ? 'var(--status-critical)' : evt.severity === 'high' ? 'var(--status-warning)' : 'var(--accent-blue)',
                              border: `1px solid ${evt.severity === 'critical' ? 'rgba(239, 68, 68, 0.3)' : evt.severity === 'high' ? 'rgba(245, 158, 11, 0.3)' : 'rgba(37, 99, 235, 0.25)'}`,
                            }}>
                              {evt.severity}
                            </span>
                          </td>
                          <td style={{ padding: '10px 12px' }}>
                            <span style={{
                              fontSize: '0.72rem',
                              fontWeight: 600,
                              color: evt.status === 'Resolved' ? 'var(--status-healthy)' : 'var(--accent-blue)',
                            }}>
                              ● {evt.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        ) : (
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontStyle: 'italic', margin: 0 }}>
            Loading fleet reliability analytics...
          </p>
        )}
      </section>

      {/* Fleet Recurring Faults Leaderboard */}
      <section className="glass-panel" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '1.2rem' }}>🧠</span>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.01em', margin: 0 }}>
                Fleet Recurring Faults Leaderboard (Tier 2 Semantic Memory)
              </h2>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0, marginTop: '4px' }}>
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
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic', padding: '16px 0' }}>
              No recurring fault clusters detected yet across Tier 2 collections.
            </p>
          ) : (
            leaderboard.map((item) => (
              <div
                key={`${item.machine_id}-${item.rank}`}
                style={{
                  padding: '16px 20px',
                  borderRadius: 'var(--btn-radius)',
                  background: 'var(--bg-card-subtle)',
                  border: '1px solid var(--border-card)',
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
                    borderRadius: 'var(--btn-radius)',
                    background: item.rank === 1 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(37, 99, 235, 0.12)',
                    color: item.rank === 1 ? 'var(--status-critical)' : 'var(--accent-blue)',
                    border: `1px solid ${item.rank === 1 ? 'rgba(239, 68, 68, 0.3)' : 'rgba(37, 99, 235, 0.25)'}`,
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
                        color: 'var(--accent-blue)',
                        background: 'var(--bg-card-subtle)',
                        padding: '2px 6px',
                        borderRadius: 'var(--btn-radius)',
                        border: '1px solid var(--border-card)',
                      }}>
                        {item.machine_id}
                      </span>
                      <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                        {item.pattern_name}
                      </h3>
                      {item.failure_code && (
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          [{item.failure_code}]
                        </span>
                      )}
                    </div>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: 0 }}>
                      💡 Longest-Lasting Fix: <strong style={{ color: 'var(--status-healthy)' }}>{item.longest_lasting_fix}</strong>
                    </p>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span style={{
                    fontSize: '0.76rem',
                    fontWeight: 700,
                    background: 'rgba(245, 158, 11, 0.12)',
                    color: 'var(--status-warning)',
                    padding: '4px 10px',
                    borderRadius: 'var(--btn-radius)',
                    border: '1px solid rgba(245, 158, 11, 0.25)',
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
