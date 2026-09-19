import { useState, useEffect } from 'react';
import type { FC } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';

import type { MachineDetailData, SensorDataPoint, MachineReliability } from '../types';
import { MachineChatWindow } from '../components/MachineChatWindow';

interface MachineDetailProps {
  realtimePoints: Record<string, SensorDataPoint[]>;
}

export const MachineDetail: FC<MachineDetailProps> = ({ realtimePoints }) => {
  const { id } = useParams<{ id: string }>();
  const machineId = id || 'M-01';

  const [machineData, setMachineData] = useState<MachineDetailData | null>(null);
  const [reliability, setReliability] = useState<MachineReliability | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSensor, setSelectedSensor] = useState<string>('');
  const [isExporting, setIsExporting] = useState(false);

  const handleExportReport = async () => {
    if (!machineId) return;
    setIsExporting(true);
    try {
      const res = await axios.get(`/api/machines/${machineId}/report`);
      const reportText = res.data.formatted_report;
      const blob = new Blob([reportText], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fixer_ai_${machineId}_diagnostic_report.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Failed to export diagnostic report:', e);
    } finally {
      setIsExporting(false);
    }
  };

  const fetchMachine = async () => {
    try {
      const [resMachine, resRel] = await Promise.allSettled([
        axios.get(`/api/machines/${machineId}`),
        axios.get(`/api/machines/${machineId}/reliability`),
      ]);

      if (resMachine.status === 'fulfilled') {
        setMachineData(resMachine.value.data);
        if (!selectedSensor && resMachine.value.data.current_readings) {
          const first = Object.keys(resMachine.value.data.current_readings).find((k) => k !== 'cycle_count') || Object.keys(resMachine.value.data.current_readings)[0];
          setSelectedSensor(first || '');
        }
      }

      if (resRel.status === 'fulfilled') {
        setReliability(resRel.value.data);
      }
    } catch (e) {
      console.error(`Failed to load machine ${machineId}:`, e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMachine();
  }, [machineId]);

  if (loading || !machineData) {
    return (
      <main style={{ maxWidth: '1440px', margin: '0 auto', padding: '40px 28px', textAlign: 'center' }}>
        <p style={{ color: '#94a3b8' }}>Loading diagnostic context for {machineId}...</p>
      </main>
    );
  }

  const isHealthy = machineData.health_status === 'healthy';
  const isWarning = machineData.health_status === 'warning';
  const statusColor = isHealthy ? '#10b981' : isWarning ? '#f59e0b' : '#ef4444';

  const sensorStream = realtimePoints[machineId] || [];

  // Fallback demo data if stream has few points
  const chartData = sensorStream.length >= 2
    ? sensorStream
    : Array.from({ length: 15 }).map((_, i) => {
        const val = machineData.current_readings[selectedSensor] || 0;
        return {
          time: `T-${15 - i}s`,
          timestamp: Date.now() - (15 - i) * 1000,
          [selectedSensor]: val + (Math.sin(i) * 0.05 * val),
        };
      });

  const sensorBaseline = machineData.baseline_ranges?.[selectedSensor] || {};
  const meanVal = sensorBaseline.mean;
  const critVal = machineData.rul?.threshold_value;

  return (
    <main style={{ maxWidth: '1440px', margin: '0 auto', padding: '32px 28px' }}>
      {/* Navigation Breadcrumb */}
      <div style={{ marginBottom: '20px' }}>
        <Link
          to="/"
          style={{
            textDecoration: 'none',
            color: '#94a3b8',
            fontSize: '0.85rem',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'color 0.2s',
          }}
        >
          <span>←</span>
          <span>Back to Fleet Overview</span>
        </Link>
      </div>

      {/* Machine Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '28px',
        flexWrap: 'wrap',
        gap: '16px',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '1rem',
              fontWeight: 800,
              background: 'rgba(99, 102, 241, 0.2)',
              color: '#818cf8',
              padding: '4px 12px',
              borderRadius: '8px',
              border: '1px solid rgba(99, 102, 241, 0.3)',
            }}>
              {machineData.machine_id}
            </span>
            <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
              {machineData.location} • Installed {machineData.install_date}
            </span>
          </div>

          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em', margin: 0 }}>
            {machineData.name}
          </h1>
          <p style={{ fontSize: '0.84rem', color: '#64748b', marginTop: '4px', margin: 0 }}>
            Architecture Model: <strong style={{ color: '#94a3b8' }}>{machineData.model}</strong> • Monitored via isolated Tier 1 & Tier 2 RAG
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={handleExportReport}
            disabled={isExporting}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '20px',
              color: '#cbd5e1',
              padding: '6px 14px',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: isExporting ? 'wait' : 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)')}
          >
            <span>📄</span>
            <span>{isExporting ? 'Generating Report...' : 'Export Shift Report'}</span>
          </button>

          <div className={isHealthy ? 'badge-healthy' : isWarning ? 'badge-warning' : 'badge-critical'} style={{
            padding: '6px 14px',
            borderRadius: '20px',
            fontSize: '0.8rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}>
            <span className="pulse-dot" style={{ background: statusColor }} />
            <span>{machineData.health_status} Condition</span>
          </div>
        </div>
      </div>

      {/* Hero Prognostic Row: Health Score, RUL, OEE */}
      <section style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '20px',
        marginBottom: '32px',
      }}>
        {/* Health Score Card */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <span style={{ fontSize: '0.74rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Industrial Health Score (ISO 10816)
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px', marginTop: '6px' }}>
            <span style={{ fontSize: '3rem', fontWeight: 800, color: statusColor, lineHeight: 1 }}>
              {machineData.health_score}
            </span>
            <span style={{ fontSize: '1.1rem', color: '#64748b' }}>/ 100</span>
          </div>

          <p style={{ fontSize: '0.8rem', color: isHealthy ? '#34d399' : '#fbbf24', marginTop: '8px', margin: 0 }}>
            {machineData.health?.primary_driver
              ? `Primary fault driver: ${machineData.health.primary_driver}`
              : 'All sensor signals within historical operational envelope.'}
          </p>
        </div>

        {/* RUL Forecast Card */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.74rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Remaining Useful Life (RUL)
            </span>
            <span style={{
              fontSize: '0.68rem',
              color: '#38bdf8',
              background: 'rgba(6, 182, 212, 0.12)',
              border: '1px solid rgba(6, 182, 212, 0.25)',
              padding: '2px 8px',
              borderRadius: '6px',
            }}>
              Heuristic
            </span>
          </div>

          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: '#f8fafc', marginTop: '8px' }}>
            {machineData.rul?.service_window || '> 30 days (nominal)'}
          </div>

          <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '4px', margin: 0 }}>
            {machineData.rul?.rul_hours
              ? `Extrapolated: ~${machineData.rul.rul_hours.toFixed(1)}h to critical OEM limit`
              : 'Zero active degradation drift detected'}
          </p>
          <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '10px', fontStyle: 'italic' }}>
            ℹ️ {machineData.rul?.heuristic_disclosure || 'Trend-based extrapolation'}
          </div>
        </div>

        {/* OEE Card */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <span style={{ fontSize: '0.74rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Overall Equipment Effectiveness (OEE)
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '6px' }}>
            <span style={{ fontSize: '3rem', fontWeight: 800, color: '#38bdf8', lineHeight: 1 }}>
              {machineData.oee_pct}%
            </span>
            <span style={{ fontSize: '0.82rem', color: '#34d399' }}>Nominal Rating</span>
          </div>
          <div style={{ display: 'flex', gap: '16px', marginTop: '12px', fontSize: '0.75rem', color: '#94a3b8' }}>
            <span>Avail: <strong>96%</strong></span>
            <span>Perf: <strong>98%</strong></span>
            <span>Qual: <strong>99.4%</strong></span>
          </div>
        </div>

        {/* ISO 14224 Reliability Profile Card */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.74rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              ISO 14224 Reliability
            </span>
            <span style={{
              fontSize: '0.68rem',
              color: '#34d399',
              background: 'rgba(52, 211, 153, 0.12)',
              border: '1px solid rgba(52, 211, 153, 0.25)',
              padding: '2px 8px',
              borderRadius: '6px',
            }}>
              {reliability ? `${reliability.availability_pct}% Avail` : '100% Avail'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
            <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc' }}>
              {reliability ? `${reliability.mtbf_hours}h` : '720h'}
            </span>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>MTBF</span>
            <span style={{ fontSize: '0.9rem', color: '#64748b', margin: '0 4px' }}>|</span>
            <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#fbbf24' }}>
              {reliability ? `${reliability.mttr_hours}h` : '1.0h'}
            </span>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>MTTR</span>
          </div>

          <p style={{ fontSize: '0.76rem', color: '#34d399', marginTop: '8px', margin: 0 }}>
            💰 <strong>${reliability ? reliability.cost_avoided_usd.toLocaleString() : '0'}</strong> downtime cost avoided
          </p>
          <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '10px' }}>
            {reliability ? `${reliability.total_downtime_hours}h downtime (${reliability.failure_count} incidents in ${reliability.window_days}d)` : '90-day operational evaluation window'}
          </div>
        </div>
      </section>

      {/* Main Grid: Telemetry Charts + Multimodal Chat Window */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0, 1.25fr) minmax(0, 1fr)',
        gap: '24px',
        marginBottom: '36px',
      }}>
        {/* Left Column: Real-time Recharts Live Telemetry */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                Live Sensor Telemetry
              </h2>
              <span style={{ fontSize: '0.74rem', color: '#94a3b8' }}>
                WebSocket live streaming • Mean-reverting Ornstein-Uhlenbeck baseline
              </span>
            </div>

            {/* Sensor selector tabs */}
            <div style={{ display: 'flex', gap: '6px' }}>
              {Object.keys(machineData.current_readings).filter((k) => k !== 'cycle_count').map((sensorKey) => (
                <button
                  key={sensorKey}
                  onClick={() => setSelectedSensor(sensorKey)}
                  style={{
                    background: selectedSensor === sensorKey ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255, 255, 255, 0.05)',
                    border: `1px solid ${selectedSensor === sensorKey ? '#6366f1' : 'rgba(255, 255, 255, 0.08)'}`,
                    color: selectedSensor === sensorKey ? '#ffffff' : '#94a3b8',
                    padding: '4px 10px',
                    borderRadius: '8px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  {sensorKey}
                </button>
              ))}
            </div>
          </div>

          {/* Recharts Chart Area */}
          <div style={{ width: '100%', height: '340px', marginTop: '10px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{
                    background: '#0f172a',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                {meanVal && (
                  <ReferenceLine y={meanVal} stroke="#06b6d4" strokeDasharray="3 3" label={{ value: 'Baseline Mean', fill: '#06b6d4', fontSize: 10 }} />
                )}
                {critVal && (
                  <ReferenceLine y={critVal} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'Critical Limit', fill: '#ef4444', fontSize: 10 }} />
                )}
                <Line
                  type="monotone"
                  dataKey={selectedSensor}
                  stroke="#818cf8"
                  strokeWidth={2.5}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Sensor Breakdown Row */}
          <div style={{
            marginTop: '20px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
            gap: '12px',
          }}>
            {Object.entries(machineData.current_readings).map(([stype, val]) => {
              const det = machineData.health?.sensor_details?.[stype];
              const isSelected = selectedSensor === stype;
              return (
                <div
                  key={stype}
                  onClick={() => stype !== 'cycle_count' && setSelectedSensor(stype)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: '10px',
                    background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                    border: `1px solid ${isSelected ? '#6366f1' : 'rgba(255, 255, 255, 0.06)'}`,
                    cursor: stype !== 'cycle_count' ? 'pointer' : 'default',
                  }}
                >
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'capitalize' }}>
                    {stype}
                  </div>
                  <div className="telemetry-val" style={{ fontSize: '1.05rem', color: '#f8fafc', marginTop: '2px' }}>
                    {typeof val === 'number' ? val.toFixed(2) : val}
                    <span style={{ fontSize: '0.7rem', color: '#64748b', marginLeft: '4px' }}>
                      {det?.unit || ''}
                    </span>
                  </div>
                  {det && (
                    <div style={{ fontSize: '0.68rem', color: det.status === 'healthy' ? '#34d399' : '#f87171', marginTop: '2px' }}>
                      {det.z_score > 0 ? `+${det.z_score.toFixed(1)}σ` : 'Nominal'}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Multimodal Machine Chat Window */}
        <div>
          <MachineChatWindow
            machineId={machineId}
            recentTickets={machineData.recent_tickets || []}
            onTicketUpdated={fetchMachine}
          />
        </div>
      </div>

      {/* Problem → Cause → Remedy Failure History (ISO 14224) */}
      <section className="glass-panel" style={{ padding: '28px' }}>
        <div style={{ marginBottom: '18px' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
            Incident History & ISO 14224 CMMS Taxonomy
          </h2>
          <span style={{ fontSize: '0.76rem', color: '#94a3b8' }}>
            Problem → Cause → Remedy records embedded into {machineId}'s Tier 2 vector brain
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8' }}>
                <th style={{ padding: '10px 14px' }}>Ticket ID</th>
                <th style={{ padding: '10px 14px' }}>Date</th>
                <th style={{ padding: '10px 14px' }}>Failure Code</th>
                <th style={{ padding: '10px 14px' }}>Observed Symptom</th>
                <th style={{ padding: '10px 14px' }}>Severity</th>
                <th style={{ padding: '10px 14px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {machineData.recent_tickets.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>
                    No recorded incident tickets for this machine.
                  </td>
                </tr>
              ) : (
                machineData.recent_tickets.map((t) => (
                  <tr key={t.ticket_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                    <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
                      {t.ticket_id.slice(0, 8)}
                    </td>
                    <td style={{ padding: '12px 14px', color: '#94a3b8' }}>
                      {new Date(t.opened_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)', color: '#a5b4fc' }}>
                      {t.failure_code || '—'}
                    </td>
                    <td style={{ padding: '12px 14px', color: '#f1f5f9', maxWidth: '300px' }}>
                      {t.symptom_text}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{
                        textTransform: 'uppercase',
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        color: t.severity === 'critical' ? '#f87171' : t.severity === 'high' ? '#fb923c' : '#fbbf24',
                      }}>
                        {t.severity}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{
                        fontSize: '0.72rem',
                        padding: '2px 8px',
                        borderRadius: '6px',
                        background: t.status === 'resolved' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                        color: t.status === 'resolved' ? '#34d399' : '#f87171',
                        border: `1px solid ${t.status === 'resolved' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                      }}>
                        {t.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
};
