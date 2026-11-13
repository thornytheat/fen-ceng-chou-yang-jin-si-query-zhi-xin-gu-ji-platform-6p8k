export type Role = 'admin' | 'analyst' | 'viewer';

export interface UserInfo {
  id: number;
  email: string;
  display_name: string;
  role: Role | string;
  role_label: string;
}

export interface LoginResult {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserInfo;
}

export interface Stratum {
  code: string;
  label: string;
  population: number;
  population_share_pct: number;
  mean_value: number;
  prior_std: number;
  min_sample: number;
  sort_order: number;
}

export interface Dataset {
  id: number;
  code: string;
  name: string;
  scenario: string;
  metric_label: string;
  unit: string;
  unit_scale: number;
  row_count: number;
  source_rows: number;
  strata_field: string;
  value_field: string;
  precision_target_pct: number;
  confidence_level: number;
  prior_period: string;
  full_scan_baseline_ms: number;
  truth_total: number;
  measured_full_scan_ms: number | null;
  note: string | null;
  strata_count: number;
  plan_count: number;
  query_count: number;
  updated_at: string;
  strata?: Stratum[];
}

export interface AllocationRow {
  code: string;
  label: string;
  population: number;
  prior_std: number;
  neyman_weight: number;
  sample_size: number;
  stratum_share_pct: number;
  expected_ci_contribution_pct: number;
}

export interface Plan {
  id: number;
  code: string;
  dataset_id: number;
  dataset_code: string;
  dataset_name: string;
  metric_label: string;
  name: string;
  confidence_level: number;
  target_error_pct: number;
  method: string;
  method_label: string;
  status: string;
  status_label: string;
  sample_size: number;
  expected_ci_pct: number;
  z_value: number;
  allocation: AllocationRow[];
  note: string | null;
  created_by: string;
  approved_by: string | null;
  approved_at: string | null;
  query_count: number;
  created_at: string;
  capacity_warning: string | null;
}

export interface StratumContribution {
  code: string;
  label: string;
  population: number;
  sample_size: number;
  sample_mean: number;
  contribution: number;
  ci_half: number;
  contribution_share_pct: number;
  variance_share_pct: number;
  verified: boolean;
}

export interface CompositionRow {
  code: string;
  label: string;
  sample_size: number;
  point_share_pct: number;
  point_share_raw_pct: number;
  std_error_pct: number;
  marginal_half_pct: number;
  joint_half_pct: number;
  joint_low_pct: number;
  joint_high_pct: number;
  interval_clipped: boolean;
}

export interface Composition {
  publishable: boolean;
  confidence: number;
  family_size: number;
  z_marginal: number;
  z_joint: number;
  method: string;
  min_stratum_sample: number;
  point_total_pct: number;
  rows: CompositionRow[];
  reasons: string[];
}

export interface ApproxQuery {
  id: number;
  code: string;
  plan_id: number;
  plan_name: string;
  dataset_id: number;
  dataset_code: string;
  dataset_name: string;
  metric_label: string;
  unit: string;
  filter_strata: string[];
  sample_size: number;
  value_estimate: number;
  ci_low: number;
  ci_high: number;
  ci_half: number;
  rel_error_pct: number;
  true_value: number;
  truth_rel_error_pct: number;
  speed_ratio: number;
  sample_ms: number;
  truth_ms: number;
  full_scan_baseline_ms: number;
  status: string;
  run_by: string;
  created_at: string;
  strata_detail: StratumContribution[];
  composition: Composition | null;
  qc_id: number | null;
  qc_verdict: string | null;
}

export interface CostSummary {
  totalSeconds: number;
  fullSeconds: number;
  sampleSeconds: number;
  rows: number;
}

export interface CheckItem {
  code: string;
  label: string;
  actual: string;
  threshold: string;
  ok: boolean;
  note: string;
}

export interface Signoff {
  stage: string;
  stage_label: string;
  actor_email: string;
  actor_name: string;
  role: string;
  decision: string;
  note: string | null;
  at: string;
}

export interface QcCheck {
  id: number;
  code: string;
  query_id: number;
  query_code: string;
  dataset_name: string;
  metric_label: string;
  target_pct: number;
  rel_error_pct: number;
  ci_pct: number;
  min_stratum_sample: number;
  coverage_pct: number;
  verdict: string;
  verdict_label: string;
  review_state: string;
  review_state_label: string;
  checks: CheckItem[];
  signoffs: Signoff[];
  next_stage: string | null;
  created_by: string;
  created_at: string;
  sample_size: number;
  value_estimate: number;
  true_value: number;
  unit: string;
}

export interface HealthInfo {
  status: string;
  db: boolean;
  redis: boolean;
  worker_heartbeat: number | null;
  brand: string;
}

export interface ListEnvelope<T> {
  items: T[];
  total: number;
}
