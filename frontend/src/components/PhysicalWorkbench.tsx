import { useState } from 'react';
import type { FC } from 'react';
import axios from 'axios';
import { Wrench, AlertTriangle, CheckCircle2, RefreshCw, Zap, ShieldCheck } from 'lucide-react';

interface PhysicalWorkbenchProps {
  machineId: string;
  isFaultActive: boolean;
  onFaultToggled: (active: boolean) => void;
  onRepairStart: () => void;
  onRepairComplete: () => void;
}

const FAULT_DETAILS: Record<
  string,
  {
    component: string;
    faultName: string;
    physicalSymptom: string;
    remedySteps: string[];
    oemStandard: string;
  }
> = {
  'M-01': {
    component: 'J2 Articulated Axis Reducer Gearbox',
    faultName: 'Reducer Grease Seal Blowout & Friction Surge',
    physicalSymptom: 'Viscous lubricant depletion at seal collar; rising internal mechanical friction.',
    remedySteps: [
      'Purge degraded grease cavity and wipe seal flange',
      'Inject 250ml Mobilux EP2 synthetic lubricant via Zerk fitting',
      'Re-torque seal flange collar bolts to OEM spec 85 Nm',
    ],
    oemStandard: 'FANUC B-83284EN/04 §7.2 Grease Replacement',
  },
  'M-02': {
    component: 'High-Precision Spindle Bearing Collar',
    faultName: 'Spindle Ceramic Bearing Race Spalling',
    physicalSymptom: 'Micro-chatter harmonic vibration (1.8+ mm/s²) and rapid spindle heat accumulation.',
    remedySteps: [
      'Stop spindle and flush contaminated micro-fog oil mist',
      'Install matched hybrid ceramic angular-contact bearing set',
      'Verify radial & axial spindle runout (< 1.2 µm)',
    ],
    oemStandard: 'Haas Service Manual §4.8 Spindle Assembly',
  },
  'M-03': {
    component: '3-Phase Induction Stator & Drive Shaft',
    faultName: 'Conveyor Stator Overload & Roller Binding',
    physicalSymptom: 'Mechanical track binding causing severe stator current spike (18A+) and overheating.',
    remedySteps: [
      'De-energize drive and clear conveyor track roller bind',
      'Re-align drive shaft flexible rubber coupler',
      'Verify 3-phase stator current balance and thermal cutoff reset',
    ],
    oemStandard: 'ISO 10816-3 General Industrial Electric Drives',
  },
  'M-04': {
    component: 'Reaction Torque Transducer & Reaction Sleeve',
    faultName: 'AS9100 Reaction Transducer Calibration Drift',
    physicalSymptom: 'Calibration offset drift (+0.28 Nm) exceeding allowable AS9100 quality tolerance.',
    remedySteps: [
      'Inspect granite bed level and vibration isolation mounts',
      'Perform optical laser zero recalibration routine',
      'Re-index reaction torque transducer against secondary transfer standard',
    ],
    oemStandard: 'AS9100 / IATF 16949 Section 7.1.5 Metrology Compliance',
  },
};

export const PhysicalWorkbench: FC<PhysicalWorkbenchProps> = ({
  machineId,
  isFaultActive,
  onFaultToggled,
  onRepairStart,
  onRepairComplete,
}) => {
  const [loadingAction, setLoadingAction] = useState<boolean>(false);
  const [repairStep, setRepairStep] = useState<string>('');
  const [repairSuccessMessage, setRepairSuccessMessage] = useState<string>('');

  const details = FAULT_DETAILS[machineId] || FAULT_DETAILS['M-01'];

  const handleSimulateTrouble = async () => {
    setLoadingAction(true);
    setRepairSuccessMessage('');
    try {
      await axios.post(`/api/machines/${machineId}/fault`);
      onFaultToggled(true);
    } catch (e) {
      console.error('Failed to trigger machine fault:', e);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleExecuteRepair = async () => {
    setLoadingAction(true);
    onRepairStart();
    setRepairSuccessMessage('');

    // Step 1 animation text
    setRepairStep(`[1/3] ${details.remedySteps[0]}...`);

    setTimeout(() => {
      setRepairStep(`[2/3] ${details.remedySteps[1]}...`);
    }, 900);

    setTimeout(() => {
      setRepairStep(`[3/3] ${details.remedySteps[2]}...`);
    }, 1800);

    // Call backend fix API
    try {
      const res = await axios.post(`/api/machines/${machineId}/fix`, {
        technician_notes: details.remedySteps.join('; '),
        technician_id: 'Lead-Tech-01',
      });

      setTimeout(() => {
        setLoadingAction(false);
        setRepairStep('');
        onFaultToggled(false);
        onRepairComplete();
        setRepairSuccessMessage(res.data.remedy || 'Equipment successfully repaired and telemetry normalized!');
      }, 2600);
    } catch (e) {
      console.error('Failed to execute machine repair:', e);
      setLoadingAction(false);
      setRepairStep('');
      onRepairComplete();
    }
  };

  return (
    <div
      className="glass-panel"
      style={{
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        border: isFaultActive ? '1px solid rgba(239, 68, 68, 0.4)' : undefined,
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.2rem' }}>🏭</span>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
              Physical Equipment & Maintenance Workbench
            </h2>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '4px 0 0' }}>
            Hardware physical status • Interactive trouble simulation • 1-Click animated repair & baseline restoration
          </p>
        </div>

        {/* State Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 14px',
            borderRadius: 'var(--btn-radius)',
            background: isFaultActive ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
            border: `1px solid ${isFaultActive ? 'rgba(239, 68, 68, 0.4)' : 'rgba(16, 185, 129, 0.4)'}`,
            fontSize: '0.78rem',
            fontWeight: 700,
            color: isFaultActive ? 'var(--status-critical)' : 'var(--status-healthy)',
          }}
        >
          {isFaultActive ? <AlertTriangle size={15} /> : <ShieldCheck size={15} />}
          <span>{isFaultActive ? 'ANOMALY / TROUBLE DETECTED' : 'NOMINAL PHYSICAL STATE'}</span>
        </div>
      </div>

      {/* Component & Fault Diagnostics Card */}
      <div
        style={{
          background: 'var(--bg-card-subtle)',
          borderRadius: 'var(--btn-radius)',
          border: '1px solid var(--border-card)',
          padding: '16px 18px',
        }}
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
          <div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Target Mechanical Assembly
            </span>
            <div style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
              {details.component}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--accent-blue)', marginTop: '4px' }}>
              Standard: {details.oemStandard}
            </div>
          </div>

          <div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Observed Failure Signature
            </span>
            <div
              style={{
                fontSize: '0.88rem',
                fontWeight: 700,
                color: isFaultActive ? 'var(--status-critical)' : 'var(--text-secondary)',
                marginTop: '2px',
              }}
            >
              {details.faultName}
            </div>
            <p style={{ fontSize: '0.73rem', color: 'var(--text-muted)', margin: '4px 0 0' }}>
              {details.physicalSymptom}
            </p>
          </div>
        </div>
      </div>

      {/* Active Repair Step Status Banner */}
      {repairStep && (
        <div
          style={{
            background: 'rgba(6, 182, 212, 0.12)',
            border: '1px solid var(--accent-cyan)',
            padding: '12px 16px',
            borderRadius: 'var(--btn-radius)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            color: 'var(--accent-cyan)',
            fontSize: '0.82rem',
            fontWeight: 600,
          }}
        >
          <RefreshCw size={16} className="spin-icon" />
          <span>{repairStep}</span>
        </div>
      )}

      {/* Success Banner */}
      {repairSuccessMessage && (
        <div
          style={{
            background: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid var(--status-healthy)',
            padding: '12px 16px',
            borderRadius: 'var(--btn-radius)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            color: 'var(--status-healthy)',
            fontSize: '0.82rem',
            fontWeight: 600,
          }}
        >
          <CheckCircle2 size={16} />
          <div>
            <strong>Physical Repair Complete:</strong> {repairSuccessMessage} (Sensor telemetry normalized to OEM baseline).
          </div>
        </div>
      )}

      {/* Action Buttons Row */}
      <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
        {/* Simulate Trouble Button */}
        <button
          onClick={handleSimulateTrouble}
          disabled={loadingAction || isFaultActive}
          className="btn-secondary"
          style={{
            flex: '1 1 200px',
            padding: '12px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            fontSize: '0.85rem',
            fontWeight: 700,
            cursor: loadingAction || isFaultActive ? 'not-allowed' : 'pointer',
            opacity: isFaultActive ? 0.5 : 1,
          }}
        >
          <Zap size={16} color="var(--status-warning)" />
          <span>Simulate Trouble (Inject Fault)</span>
        </button>

        {/* 1-Click Animated Repair Button */}
        <button
          onClick={handleExecuteRepair}
          disabled={loadingAction || !isFaultActive}
          style={{
            flex: '2 1 280px',
            padding: '12px 24px',
            borderRadius: 'var(--btn-radius)',
            border: 'none',
            background: isFaultActive
              ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
              : 'var(--bg-card-subtle)',
            color: isFaultActive ? '#ffffff' : 'var(--text-muted)',
            boxShadow: isFaultActive ? '0 4px 18px rgba(16, 185, 129, 0.35)' : 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
            fontSize: '0.9rem',
            fontWeight: 800,
            cursor: loadingAction || !isFaultActive ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          <Wrench size={18} />
          <span>{loadingAction ? 'Executing Repair Animation...' : 'Repair & Restore Equipment'}</span>
        </button>
      </div>
    </div>
  );
};
