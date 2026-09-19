export type HealthStatus = 'healthy' | 'warning' | 'critical';

export interface SensorDetail {
  sensor_type: string;
  current_value: number;
  baseline_mean: number;
  unit: string;
  z_score: number;
  sensor_health_score: number;
  status: HealthStatus;
  message: string;
}

export interface HealthReport {
  machine_id: string;
  health_score: number;
  status: HealthStatus;
  primary_driver: string | null;
  sensor_details: Record<string, SensorDetail>;
  timestamp?: string;
}

export interface RULReport {
  machine_id: string;
  rul_hours: number | null;
  rul_days: number | null;
  service_window: string;
  critical_sensor: string | null;
  current_value: number | null;
  threshold_value: number | null;
  unit: string;
  trend_rate_per_hour: number;
  r_squared: number;
  is_degrading: boolean;
  predicted_failure_iso: string | null;
  heuristic_disclosure: string;
  is_heuristic: boolean;
}

export interface Machine {
  machine_id: string;
  name: string;
  model: string;
  machine_type: string;
  location: string;
  install_date: string;
  current_readings: Record<string, number>;
  health_score: number;
  health_status: HealthStatus;
  primary_driver: string | null;
  rul_hours: number | null;
  predicted_service_window: string;
  oee_pct: number;
  open_tickets: number;
  trigger_active: boolean;
}

export interface MachineDetailData extends Machine {
  baseline_ranges: Record<string, any>;
  health: HealthReport;
  rul: RULReport;
  recent_tickets: TicketSummary[];
}

export interface TicketSummary {
  ticket_id: string;
  opened_at: string;
  closed_at: string | null;
  status: 'open' | 'escalated' | 'resolved';
  severity: 'low' | 'medium' | 'high' | 'critical';
  symptom_text: string;
  failure_code: string | null;
  confidence: number;
}

export interface TicketMessageItem {
  id?: number;
  sender: 'bot' | 'technician' | 'system';
  sender_name?: string;
  text: string;
  timestamp: string;
  slack_ts?: string;
}

export interface RecurringFaultCluster {
  cluster_id: string;
  machine_id: string;
  pattern_name: string;
  failure_code: string | null;
  occurrence_count: number;
  severity: string;
  longest_lasting_fix: string;
  recommended_remedy?: string;
  summary_insight: string;
  ticket_ids: string[];
}

export interface FleetLeaderboardItem {
  rank: number;
  machine_id: string;
  pattern_name: string;
  failure_code: string | null;
  occurrence_count: number;
  severity: string;
  longest_lasting_fix: string;
  summary_insight: string;
  ticket_ids: string[];
}

export interface SensorDataPoint {
  time: string;
  timestamp: number;
  [sensorKey: string]: number | string;
}
