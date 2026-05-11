@echo off
echo ============================================
echo   HRM System - Backend (Django)
echo ============================================

cd /d "%~dp0backend"

:: Создаём виртуальное окружение если нет
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Активируем venv
call venv\Scripts\activate.bat

:: Устанавливаем зависимости
echo Installing dependencies...
pip install -r requirements.txt --quiet

:: Выполняем миграции
echo Running migrations...
python manage.py makemigrations
python manage.py migrate

:: Заполняем тестовыми данными
echo Seeding test data...
python manage.py seed_data

:: Запускаем сервер
echo.
echo Backend running at http://localhost:8000
echo Admin panel: http://localhost:8000/admin  (admin / admin123)
echo.
python manage.py runserver 0.0.0.0:8000
