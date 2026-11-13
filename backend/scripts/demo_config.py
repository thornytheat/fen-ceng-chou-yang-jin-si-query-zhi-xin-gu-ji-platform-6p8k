"""seed 演示数据的口径常量（与 batch-plan.md §5.7 的主流程验收数值对应）。

生成算法是确定性的：numpy PCG64 固定种子 + splitmix64 式 64bit 混合哈希排序，
同一份代码在任何机器上生成的明细行、样本秩、真值都一致，因此 SEED_SUMMARY 可复现。
"""
from __future__ import annotations

DEMO_PASSWORD = "Demo@2026"
DEMO_DOMAIN = "sampleaqp.io"

DEMO_USERS: list[tuple[str, str, str]] = [
    (f"admin@sampleaqp.io", "沈望", "admin"),
    (f"analyst@sampleaqp.io", "陆珂", "analyst"),
    (f"viewer@sampleaqp.io", "周岚", "viewer"),
]

# 五个线路类型层：全项目共用同一套分层口径（3 个数据集 × 5 层）
STRATA: list[tuple[str, str]] = [
    ("LTL_LONG", "干线长途"),
    ("REGIONAL", "区域支线"),
    ("URBAN", "同城配送"),
    ("COLD_CHAIN", "冷链专线"),
    ("HEAVY", "大件重货"),
]

GENERATOR_SALT = 586898          # 抽样秩盐值：决定每层取到哪 n_h 行
GENERATOR_SEED = 5832026         # 明细生成种子（PCG64）
PRIOR_TO_DATA_STD = 0.935        # 明细离散度 / 先验 S_h：先验取自上一期普查，略保守

DATASETS: list[dict] = [
    {
        "code": "DS-WAYBILL-GMV",
        "name": "运单运费收入（近 30 天账期）",
        "scenario": "远舟物流 TMS 运单明细表，按线路类型分 5 层；经营会要「这个月 GMV 大概多少」，全表聚合要跑 40 分钟。",
        "metric_label": "运费收入 GMV",
        "unit": "元",
        "unit_scale": 100,
        "source_rows": 80_000_000,
        "strata_field": "route_type",
        "value_field": "freight_revenue_minor",
        "precision_target_pct": 2.00,
        "confidence_level": 0.95,
        "prior_period": "2026-10 普查",
        "full_scan_baseline_ms": 38600,
        "note": "演示库载入 10 万行明细；生产表 8,000 万行，基线耗时取生产实测。",
        "populations": [30000, 24000, 26000, 12000, 8000],
        "means_minor": [18999, 14800, 10500, 28500, 36250],
        "prior_std_minor": [9749.82, 10254.76, 7408.10, 12185.52, 12571.48],
        "std_ratio": PRIOR_TO_DATA_STD,
    },
    {
        "code": "DS-ONTIME-DURATION",
        "name": "运单妥投时效（小时）",
        "scenario": "同一条 TMS 运单表的时效侧写：从揽收到签收的小时数，用来回答「平均几小时送到」。",
        "metric_label": "妥投时长",
        "unit": "小时",
        "unit_scale": 10,
        "source_rows": 8_000_000,
        "strata_field": "route_type",
        "value_field": "delivery_hours_tenths",
        "precision_target_pct": 3.00,
        "confidence_level": 0.95,
        "prior_period": "2026-10 普查",
        "full_scan_baseline_ms": 12400,
        "note": "演示库 1.2 万行；时效指标比金额更集中，目标误差放宽到 3%。",
        "populations": [3600, 2880, 3120, 1440, 960],
        "means_minor": [380, 260, 140, 220, 600],
        "prior_std_minor": [62.0, 41.0, 28.0, 34.0, 85.0],
        "std_ratio": 0.95,
    },
    {
        "code": "DS-COST-PER-WAYBILL",
        "name": "单票履约成本（元）",
        "scenario": "财务口径的单票履约成本明细，用于回答「这个季度单票成本大概多少」。",
        "metric_label": "单票履约成本",
        "unit": "元",
        "unit_scale": 100,
        "source_rows": 6_000_000,
        "strata_field": "route_type",
        "value_field": "cost_minor",
        "precision_target_pct": 2.50,
        "confidence_level": 0.90,
        "prior_period": "2026-Q3 普查",
        "full_scan_baseline_ms": 9800,
        "note": "演示库 8,000 行；置信度 90%，用于演示「方案参数不同、精度不同」。",
        "populations": [2400, 1920, 2080, 960, 640],
        "means_minor": [12000, 9600, 6200, 18000, 24000],
        "prior_std_minor": [4000.0, 3600.0, 2400.0, 5200.0, 6000.0],
        "std_ratio": 0.93,
    },
]

PLANS: list[dict] = [
    {
        "code": "PLAN-001",
        "dataset_code": "DS-WAYBILL-GMV",
        "name": "经营会 GMV · 95% 置信 / 目标误差 2%",
        "confidence_level": 0.95,
        "target_error_pct": 2.00,
        "method": "neyman",
        "status": "active",
        "note": "主口径：Neyman 分配，每层最小 30 行；审批人 admin。",
        "seed_key": "seed:plan:PLAN-001",
    },
    {
        "code": "PLAN-002",
        "dataset_code": "DS-WAYBILL-GMV",
        "name": "快速口径 GMV · 95% 置信 / 目标误差 5%",
        "confidence_level": 0.95,
        "target_error_pct": 5.00,
        "method": "neyman",
        "status": "draft",
        "note": "赶时间用的粗口径；CI 会超过数据集 2% 的精度标准，自检应当判不达标。",
        "seed_key": "seed:plan:PLAN-002",
    },
]

SEED_AUDIT: list[tuple[str, str, str, str, str, str, dict]] = [
    ("seed:audit:1", "admin@sampleaqp.io", "admin", "dataset.calibrate", "dataset", "1",
     {"code": "DS-WAYBILL-GMV", "changes": {"precision_target_pct": {"to": 2.0}}}),
    ("seed:audit:2", "admin@sampleaqp.io", "admin", "plan.approve", "sample_plan", "1",
     {"code": "PLAN-001", "sample_size": 2742}),
    ("seed:audit:3", "analyst@sampleaqp.io", "analyst", "dataset.load", "dataset", "1",
     {"code": "DS-WAYBILL-GMV", "rows": 100000, "source": "tms_fixture"}),
]

SEED_ANCHOR_DATE = "2026-11-11"   # 明细的业务日期锚点（往前 30 天滚动）
SEED_DAYS = 30
