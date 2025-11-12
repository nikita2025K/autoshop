Автомагазин — backend API на FastAPI

Запуск (Windows PowerShell):

# 1. Создать виртуальное окружение
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить приложение
uvicorn app.main:app --reload --port 8000

API автоматически доступно по ссылке http://127.0.0.1:8000/docs

