# sampleaqp · 分层抽样近似查询与置信估计台

> 用 2,742 行样本回答「8,000 万行运单大概多少」——分层抽样 + Horvitz–Thompson 点估计，给出 95% 置信区间，并与全量真值对照。

## 1. 真实场景

- **模拟客户**：远舟物流 · 数据分析组（7 人）。TMS 运单明细表 8,000 万行，业务方在经营会上总要一个「大概多少」。
- **现有工作流**：分析师写全表聚合 SQL，跑 40 分钟；赶时间就 `ORDER BY RAND() LIMIT 10000` 给个点估计，被质疑「误差多少」就重跑；每条线路/时效层该抽多少行，没有口径。
- **三个痛点**：① 全量太慢，老板不等；② 抽样没有置信区间，说不清可信度；③ 各线路层的样本量不会分，冷层抽太多、热层抽太少。
- **上下游**：上游＝运单明细（本地确定性 fixture，含分层字段与真实偏斜分布）→ 本系统替代「全量慢查 + 裸抽样 + Excel 拍脑袋」→ 下游＝经营会近似指标、误差说明与对外口径。

## 2. 角色与权限

| 角色 | 账号 | 权限 | 典型动作 |
|---|---|---|---|
| admin 分析负责人 | `admin@sampleaqp.io` | 全部 | 校准数据集精度标准、刷新全量基线、审批方案、跑查询、自检、导出 |
| analyst 分析师 | `analyst@sampleaqp.io` | 不含审批与校准 | 建方案、跑近似查询、跑精度自检、签自检提交 |
| viewer 业务方 | `viewer@sampleaqp.io` | 只读 + 自检知悉 | 看近似结果与置信区间、在复核链最后一步签「已知悉」、导出说明 |

密码统一 `Demo@2026`。低权角色调高权接口会返回真实 **403**（中间件层强制，不是前端藏按钮）：

| 请求 | 角色 | 结果 |
|---|---|---|
| `POST /api/plans` | viewer | 403 |
| `POST /api/queries/run` | viewer | 403 |
| `PATCH /api/datasets/1` | analyst | 403 |
| `POST /api/plans/1/approve` | analyst | 403 |
| `POST /api/qc/{id}/signoff`（stage=analyst） | viewer | 403 |
| `GET /api/audit` | viewer / analyst | 403 |

## 3. 主要功能（一条链路四个模块）

1. **数据集概览**：三份数据集（GMV / 时效 / 成本）× 5 个线路层，展示 N_h、层占比、先验 S_h、层均值、精度标准；admin 可校准精度标准、投递后台「全量基线刷新」。
2. **抽样方案编辑**：输入置信度 + 目标误差 → 后端算法给出总样本量、每层 n_h、Neyman 权重、预计 CI、层容量约束；草稿须 admin 审批。
3. **近似查询**：按方案抽行 → HT 点估计 + 有限总体校正方差 + 95% CI，并现场执行同口径全量聚合做对照；输出各层贡献、方差占比、耗时与提速。
4. **精度自检**：相对误差 / CI 宽度 / 层最小样本 / 覆盖率 / 提速比五项检查，给出达标结论；三角色复核链（分析师提交 → 负责人复核 → 业务方知悉）完成后可导出。
5. **导出估算说明 Markdown**：含方案参数、点估计与 CI、全量真值对照、各层贡献表、检查项与复核链。

## 4. 算法（后端 Python 真算，前端只展示）

### 算法 1：分层样本量与分配（`backend/src/services/sampling_service.py`）

```
T    = Σ N_h · S_h                        （Neyman 层波动总量）
n    = max(60, int((z · T / (e · Y))²))    （Y = Σ N_h·ȳ_h，向下取整）
n_h  = n · N_h·S_h / Σ N_h·S_h             （Neyman 分配）
```

- 某层 `S_h = 0` 或选择比例分配时退化为 `n_h ∝ N_h`，并在方案上提示「已退化」。
- 每层最小样本 **30**，不足补足、总样本上浮；`n_h > N_h` 时截断到层容量，缺口按未封顶层的权重重分配。
- 最大余数法取整，保证 `Σ n_h == n`；输出每层 `n_h`、权重与预计 CI 贡献。

### 算法 2：Horvitz–Thompson 估计与 CI（`backend/src/services/estimation_service.py`）

```
Ŷ       = Σ_h N_h · ȳ_h
V(Ŷ)    = Σ_h N_h² · (1 - n_h/N_h) · s_h² / n_h     （有限总体校正）
CI      = Ŷ ± z·√V,   相对误差 = z·√V / Ŷ
```

- `z` 按置信度取 1.2816 / 1.6449 / 1.9600 / 2.5758；非表内置信度用 Acklam 反函数近似（不引入 scipy）。
- 与全量真值对比：真值由同一数据集、同一过滤范围的 `SUM(value_minor)` **真实聚合**得出，不是写死的对照值。
- 抽样确定性：明细行在 seed 时写入 64bit 混合哈希 `sample_rank`，查询按 `(dataset_id, stratum_code, sample_rank)` 取每层最小的 n_h 行 —— 同一方案 + 同一数据集永远得到同样样本，可复现、可复核。

### 失败态

- 数据集无明细行 → `DATASET_EMPTY`（422），前端给可恢复空态。
- 方案未审批就查询 → `PLAN_NOT_ACTIVE`（409）。
- 层容量不足 / 先验 S_h 缺失 → 返回 `capacity_warning`，算法降级但不静默。
- 复核链顺序错误 / 角色不符 → `QC_ORDER` / `FORBIDDEN`（409 / 403）。

## 5. 快速启动

```bash
cp .env.example .env
docker compose up -d --build
# 等 5 个服务 healthy（约 60-120s），浏览器打开 http://localhost:18256
```

seed 由 `SEED_DEMO=true` 在 backend 启动时自动执行一次（失败只记日志，不阻塞启动）。也可手工重跑：

```bash
docker compose exec -T backend python -m scripts.seed_demo
```

结束后打印（幂等，两次逐字一致）：

```
SEED_SUMMARY brand=sampleaqp datasets=3 strata=5 rows=120000 plans=2 users=3
```

演示数据规模：**120,000 行**明细（GMV 10 万行 / 时效 1.2 万行 / 成本 8,000 行），生产表规模按 8,000 万行标注（数据集字段 `source_rows`）。

## 6. 主流程（演示脚本）

1. `admin@sampleaqp.io` 登录 → 数据集概览确认 GMV 数据集精度标准 2%、全量真值 ¥18,301,700.00。
2. `analyst@sampleaqp.io` → 抽样方案：置信 95% / 目标误差 2% / Neyman → 生成草稿 `n=2,742`，5 层分配 `[820, 690, 540, 410, 282]`。
3. `admin` 审批该方案（`PLAN-001` 已由 seed 审批，可直接用）。
4. `analyst` → 近似查询：点估计 **¥18,264,926.85**，95% CI **±1.87%**；与真值相对误差 **0.20%**（标准 ≤2%，达标）。
5. 二次方案：目标误差 5% → `n=438`，CI **±4.58%** > 2% 标准 → 自检判 **未达标**（提醒提高置信或降低误差）。
6. 精度自检：分析师提交 → 负责人复核 → 业务方知悉，三签完成后导出 `sampleaqp-estimate-AQ-*.md`。

## 7. 技术栈

| 层 | 技术 |
|---|---|
| frontend | React 18 + TypeScript + Vite 5，Nginx 1.27 托管，自绘 SVG 图表 |
| backend | Python 3.11 + FastAPI 0.115 + SQLAlchemy 2.0 + Pydantic v2 |
| worker | Celery 5.4 + Redis 7（心跳 + 全量基线刷新任务） |
| db | MySQL 8.0（utf8mb4） |
| 认证 | JWT（HS256）+ bcrypt 密码哈希 |
| 观测 | 审计日志（HTTP + 领域双层）+ Redis 固定窗口限流 |

## 8. 目录

```
gb-583/
├── docker-compose.yml          # 5 服务：frontend/backend/worker/db/redis
├── .env.example
├── backend/
│   ├── Dockerfile / requirements.txt
│   ├── migrations/             # 0001_initial.sql（与 ORM 对齐）
│   ├── scripts/                # seed_demo.py / demo_config.py / worker_healthcheck.sh
│   └── src/
│       ├── config/             # settings / database / celery_app / app
│       ├── constants/          # roles / enums / limits / error_codes
│       ├── models/             # user / dataset / waybill / sample_plan / approx_query / qc_check / audit
│       ├── schemas/            # auth / dataset / plan / query / qc / common
│       ├── services/           # sampling / estimation / dataset / plan / query / qc / export / audit / auth
│       ├── controllers/        # 薄控制器
│       ├── routes/             # /api/*（health/auth/datasets/plans/queries/qc/audit）
│       ├── middlewares/        # auth / rbac / rate_limit / audit_logger / error_handler
│       ├── utils/              # numbers(统计量) / security / errors / logger / timeutil
│       ├── tasks.py            # Celery 任务
│       └── main.py
└── frontend/
    ├── Dockerfile / nginx.conf / vite.config.ts / tsconfig.json
    └── src/
        ├── api/                # client / auth / datasets / plans / queries / qc / health
        ├── stores/             # auth / ui / dataset / plan / query / qc
        ├── types/              # models.ts
        ├── components/common/  # StatTile / RulerBar / StratumChart / CiPlot / RangeBar / VerdictPill / VialTag / EmptyState / Toasts
        ├── components/layout/  # AppShell
        ├── hooks/              # useStore / useAsync / useToast
        ├── pages/              # Login / Datasets / Plans / Queries / Qc
        ├── router/             # index / guards
        ├── constants/          # enums / roles / ui
        ├── utils/              # format / errorMessage
        └── styles/             # tokens.css / global.css
```

## 9. 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `COMPOSE_PROJECT_NAME` | `sampleaqp` | 容器名前缀 |
| `FRONTEND_PORT` | `18256` | 前端映射端口（容器 80） |
| `BACKEND_PORT` | `19256` | 后端映射端口（容器 8000） |
| `DB_PORT` | `17756` | MySQL 映射端口（容器 3306） |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_ROOT_PASSWORD` | `sampleaqp*` | MySQL 凭据 |
| `JWT_SECRET` | 示例值 | JWT 签名密钥（生产必须改） |
| `REDIS_URL` | `redis://redis:6379/0` | Celery broker / 限流 / 心跳 |
| `SEED_DEMO` | `true` | 启动时自动 seed |
| `RATE_LIMIT_PER_MINUTE` / `RATE_LIMIT_WRITE_PER_MINUTE` | `300` / `60` | 限流额度 |
| `APP_TIMEZONE_OFFSET_MINUTES` | `480` | 时间显示时区（UTC+8） |
| `NPM_REGISTRY` | `https://registry.npmmirror.com` | 前端构建 registry（可覆盖） |

## 10. Docker 说明

- 5 个服务都有 healthcheck：`db`（mysqladmin ping）、`redis`（PING）、`backend`（`/api/health`）、`worker`（Redis 心跳 + Celery ping 兜底）、`frontend`（wget 首页）。
- 启动顺序用 `service_healthy`：backend/worker 依赖 db+redis healthy，worker 再依赖 backend healthy，frontend 依赖 backend healthy。
- 命名卷：`db_data`（MySQL 数据）、`redis_data`（AOF）。
- 前端 Nginx：`location /api/ { proxy_pass http://backend:8000/; }` + SPA 回落 `try_files ... /index.html`；后端路由同时挂 `/api` 与根路径，两处一致。
- 收尾：`docker compose down -v --remove-orphans`。

## 11. 共享枚举出现位置

| 枚举组 | 后端 | 前端 |
|---|---|---|
| `Role`（admin/analyst/viewer） | `backend/src/constants/roles.py` | `frontend/src/constants/roles.ts` + `types/models.ts` |
| `AllocationMethod` / `PlanStatus` / `QueryStatus` | `backend/src/constants/enums.py` | `frontend/src/constants/enums.ts` |
| `QcVerdict` / `ReviewState` / `SignoffStage` | `backend/src/constants/enums.py` | `frontend/src/constants/enums.ts` + `pages/Qc.tsx` |
| `CheckCode`（五项检查） | `backend/src/constants/enums.py` | `frontend/src/constants/enums.ts`（`CHECK_HINTS`） |

## 12. License

MIT（示例项目，仅用于评审演示）。演示数据为确定性生成的合成运单，不含任何真实客户数据。
