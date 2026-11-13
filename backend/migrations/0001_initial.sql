-- sampleaqp 基线表结构（MySQL 8.0 / utf8mb4）
CREATE TABLE IF NOT EXISTS users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(160) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  display_name VARCHAR(80) NOT NULL,
  role VARCHAR(16) NOT NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  actor_email VARCHAR(160) NOT NULL,
  actor_role VARCHAR(16) NOT NULL,
  action VARCHAR(64) NOT NULL,
  entity VARCHAR(48) NOT NULL,
  entity_id VARCHAR(64) NULL,
  detail JSON NULL,
  layer VARCHAR(16) NOT NULL DEFAULT 'domain',
  ip VARCHAR(64) NULL,
  seed_key VARCHAR(120) NULL UNIQUE,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  KEY ix_audit_created (created_at),
  KEY ix_audit_actor (actor_email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS datasets (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(48) NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  scenario VARCHAR(400) NOT NULL,
  metric_label VARCHAR(80) NOT NULL,
  unit VARCHAR(16) NOT NULL DEFAULT '元',
  unit_scale INT NOT NULL DEFAULT 100,
  row_count BIGINT NOT NULL DEFAULT 0,
  source_rows BIGINT NOT NULL DEFAULT 0,
  strata_field VARCHAR(64) NOT NULL,
  value_field VARCHAR(64) NOT NULL,
  precision_target_pct DECIMAL(5,2) NOT NULL DEFAULT 2.00,
  confidence_level DECIMAL(4,3) NOT NULL DEFAULT 0.950,
  prior_period VARCHAR(24) NOT NULL,
  full_scan_baseline_ms INT NOT NULL DEFAULT 38600,
  truth_total_minor BIGINT NOT NULL DEFAULT 0,
  measured_full_scan_ms INT NULL,
  note VARCHAR(400) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dataset_strata (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  dataset_id BIGINT NOT NULL,
  code VARCHAR(32) NOT NULL,
  label VARCHAR(64) NOT NULL,
  population BIGINT NOT NULL,
  mean_minor BIGINT NOT NULL,
  prior_std_minor DECIMAL(14,2) NOT NULL,
  min_sample INT NOT NULL DEFAULT 30,
  sort_order INT NOT NULL DEFAULT 0,
  UNIQUE KEY uq_stratum (dataset_id, code),
  CONSTRAINT fk_stratum_dataset FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS waybills (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  dataset_id BIGINT NOT NULL,
  stratum_code VARCHAR(32) NOT NULL,
  value_minor BIGINT NOT NULL,
  sample_rank VARCHAR(20) NOT NULL,
  biz_date DATE NOT NULL,
  KEY ix_sample (dataset_id, stratum_code, sample_rank),
  CONSTRAINT fk_waybill_dataset FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sample_plans (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  dataset_id BIGINT NOT NULL,
  code VARCHAR(48) NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  confidence_level DECIMAL(4,3) NOT NULL,
  target_error_pct DECIMAL(5,2) NOT NULL,
  method VARCHAR(16) NOT NULL,
  status VARCHAR(16) NOT NULL,
  sample_size INT NOT NULL,
  allocation JSON NOT NULL,
  expected_ci_pct DECIMAL(6,3) NOT NULL,
  z_value DECIMAL(6,4) NOT NULL,
  note VARCHAR(400) NULL,
  created_by VARCHAR(160) NOT NULL,
  approved_by VARCHAR(160) NULL,
  approved_at DATETIME(3) NULL,
  seed_key VARCHAR(120) NULL UNIQUE,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_plan_dataset FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS approx_queries (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  plan_id BIGINT NOT NULL,
  dataset_id BIGINT NOT NULL,
  code VARCHAR(48) NOT NULL UNIQUE,
  filter_strata JSON NOT NULL,
  sample_size INT NOT NULL,
  value_estimate_minor BIGINT NOT NULL,
  ci_low_minor BIGINT NOT NULL,
  ci_high_minor BIGINT NOT NULL,
  rel_error_pct DECIMAL(7,4) NOT NULL,
  std_error_minor BIGINT NOT NULL,
  truth_total_minor BIGINT NOT NULL,
  truth_rel_error_pct DECIMAL(7,4) NOT NULL,
  strata_detail JSON NOT NULL,
  sample_ms DECIMAL(10,2) NOT NULL,
  truth_ms DECIMAL(10,2) NOT NULL,
  full_scan_baseline_ms INT NOT NULL,
  status VARCHAR(16) NOT NULL,
  run_by VARCHAR(160) NOT NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_query_plan FOREIGN KEY (plan_id) REFERENCES sample_plans(id) ON DELETE CASCADE,
  CONSTRAINT fk_query_dataset FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS qc_checks (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  query_id BIGINT NOT NULL,
  code VARCHAR(48) NOT NULL UNIQUE,
  target_pct DECIMAL(5,2) NOT NULL,
  rel_error_pct DECIMAL(7,4) NOT NULL,
  ci_pct DECIMAL(7,4) NOT NULL,
  min_stratum_sample INT NOT NULL,
  coverage_pct DECIMAL(8,4) NOT NULL,
  checks JSON NOT NULL,
  verdict VARCHAR(16) NOT NULL,
  review_state VARCHAR(16) NOT NULL,
  signoffs JSON NOT NULL,
  created_by VARCHAR(160) NOT NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_qc_query FOREIGN KEY (query_id) REFERENCES approx_queries(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
