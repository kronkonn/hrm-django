# HRM System — Дипломная работа

Полноценная система управления персоналом с ML-аналитикой.

## Стек
- **Backend**: Django 4.2 + DRF + PostgreSQL + JWT
- **Frontend**: Vue.js 3 + Vite + Pinia + Chart.js
- **ML**: XGBoost (риск увольнения + SHAP), K-Means + t-SNE (кластеры), Isolation Forest (аномалии), SARIMA (прогнозы)

## Структура
```
hrm-django/
├── backend/          # Django проект
│   ├── hrm/          # Настройки, URLs
│   ├── employees/    # Сотрудники, отделы, должности
│   ├── timesheets/   # Табели рабочего времени
│   ├── leaves/       # Заявки на отпуск
│   ├── recruitment/  # Вакансии и кандидаты
│   └── analytics/    # ML-модели и API аналитики
│       └── ml/       # XGBoost, K-Means, IsolationForest, SARIMA
└── frontend/         # Vue.js 3 приложение
    └── src/
        ├── api/      # Axios вызовы
        ├── stores/   # Pinia сторы
        ├── views/    # Страницы
        └── components/ # Chart.js компоненты
```

## Запуск

### Требования
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### 1. База данных
```sql
CREATE DATABASE hrm_db;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE hrm_db TO postgres;
```

### 2. Backend
```bat
start_backend.bat
```
Или вручную:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

### 3. Frontend
```bat
start_frontend.bat
```
Или вручную:
```bash
cd frontend
npm install
npm run dev
```

## Доступ
- Фронтенд: http://localhost:5173
- API: http://localhost:8000/api/
- Админка: http://localhost:8000/admin/

**Логин**: `admin` / `admin123`

## API Endpoints
| Метод | URL | Описание |
|-------|-----|----------|
| POST | /api/token/ | JWT логин |
| GET | /api/employees/list/ | Список сотрудников |
| GET | /api/employees/departments/ | Отделы |
| GET | /api/leaves/ | Заявки на отпуск |
| POST | /api/leaves/{id}/approve/ | Одобрить |
| GET | /api/recruitment/vacancies/ | Вакансии |
| GET | /api/recruitment/candidates/ | Кандидаты |
| POST | /api/analytics/run/ | Запустить ML |
| GET | /api/analytics/attrition/ | Прогнозы увольнений |
| GET | /api/analytics/clusters/ | Кластеры t-SNE |
| GET | /api/analytics/anomalies/ | Аномалии |
| GET | /api/analytics/forecasts/ | Прогнозы SARIMA |
| GET | /api/analytics/dashboard/ | Сводка дашборда |
