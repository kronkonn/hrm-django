# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (from `backend/`)
```bash
# First-time setup
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data  # populates demo data

# Run dev server
python manage.py runserver  # http://localhost:8000

# Django management
python manage.py makemigrations <app>
python manage.py shell
```

### Frontend (from `frontend/`)
```bash
npm install
npm run dev    # http://localhost:5173
npm run build
```

### Default credentials
- Admin login: `admin` / `admin123`
- API base: `http://localhost:8000/api/`

---

## Architecture

### Backend — Django apps

| App | Responsibility |
|---|---|
| `hrm/` | Settings, root URLs, AES encryption utilities, global search view |
| `accounts/` | JWT auth, `UserProfile` (role), custom DRF permission classes |
| `employees/` | `Employee`, `Department`, `Position`; ML feature fields on Employee |
| `timesheets/` | Daily work records (`Timesheet`); drives `hours_fulfillment` on Employee |
| `leaves/` | Leave requests with approval flow |
| `recruitment/` | Vacancies, candidates, public application form (token-based URL) |
| `training/` | Courses, `CourseAssignment` with status/deadline tracking |
| `analytics/` | ML models + result storage; `run_analytics` view triggers all four models |
| `audit/` | `AuditMiddleware` auto-logs LOGIN/LOGOUT/CREATE/UPDATE/DELETE to `AuditLog` |

### Authentication & permissions

JWT via `rest_framework_simplejwt`. Tokens: 8h access / 7d refresh.

Roles defined in `accounts/models.py:UserProfile`: `DIRECTOR`, `HR_MANAGER`, `EMPLOYEE`, `ADMIN`.

Permission classes in `accounts/permissions.py`:
- `IsDirector` — DIRECTOR or ADMIN
- `IsHROrDirector` — HR_MANAGER, DIRECTOR, or ADMIN
- `IsAdmin` — ADMIN only

Analytics endpoints are DIRECTOR/ADMIN only. Dashboard summary is HR_MANAGER+ with analytics fields appended for DIRECTOR only.

### PII Encryption (ФЗ-152)

`hrm/encryption.py` provides `EncryptedCharField`, `EncryptedTextField`, `EncryptedDateField` — transparent AES-256-CBC via `pycryptodome`. Encrypted values are stored with an `enc:` prefix in the database.

Fields on `Employee` encrypted: `phone`, `birth_date`.

The AES key comes from `settings.AES_SECRET_KEY` (env var `AES_SECRET_KEY`). In dev, a default 32-byte key is used. The `_unwrap` method silently returns plaintext if decryption fails — this handles pre-migration rows.

### ML pipeline (`analytics/ml/`)

All four models are triggered synchronously by `POST /api/analytics/run/` and results are stored to the DB:

| Module | Model | Output table |
|---|---|---|
| `attrition.py` | XGBoost + SHAP | `AttritionPrediction` (`risk_score`, `risk_label`, `top_factors`) |
| `clustering.py` | K-Means (auto-k 3–8 by silhouette) + t-SNE | `EmployeeCluster` (`cluster_id`, `x_tsne`, `y_tsne`, `cluster_label`) |
| `anomaly.py` | Isolation Forest (contamination=0.05) + mean±2σ rules | `Anomaly` |
| `forecasting.py` | SARIMA, 3-month horizon, 95% CI | `MetricForecast` for 5 metrics: headcount, avg_salary, sick_days, overtime, turnover |

`build_real_history()` pulls the last 24 months of real DB data; `_generate_synthetic_fallback()` is used when fewer than 3 months of real data exist.

Recommendations (`GET /api/analytics/recommendations/`) are generated on-the-fly from stored ML results — no separate model.

### Frontend — Vue 3 + Vite

**API layer** (`src/api/index.js`): single Axios instance with `baseURL=/api`. Interceptor attaches `Bearer` token and auto-refreshes on 401 (one retry); on refresh failure, clears localStorage and redirects to `/login`.

**Pinia stores** (`src/stores/`): `auth`, `employees`, `analytics`, `recruitment`, `training`. Auth store persists tokens and role to `localStorage`.

**Router** (`src/router/index.js`): `beforeEach` guard enforces `requiresAuth` and per-route `roles` array. Default route: `/my-profile` for EMPLOYEE, `/dashboard` for all others.

**Role-based UI**: `canAccessAnalytics` (DIRECTOR/ADMIN) and `canAccessHR` (HR+) computed in `authStore` control sidebar links and component visibility.

**Chart components** (`src/components/`): `ClusterChart.vue` (t-SNE scatter), `ForecastChart.vue` (SARIMA line), `RiskHeatmap.vue`, `DepartmentBubbleChart.vue` — all use Chart.js 4.
