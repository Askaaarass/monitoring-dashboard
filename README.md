# Аквапоника: мониторинг системы

Веб-приложение для наблюдения за аквапонной установкой: показания датчиков и
графики, состояние устройств, оповещения, индекс биомассы и административная
панель. Интерфейс и API реализованы на Django.

## Команда

- Аскеров Аскар 
- Алиаскар Алибек  
- Багдатулы Даниал

## Стек

- Python, Django
- Django REST Framework
- Django Channels и Daphne
- Redis и Celery
- SQLite
- HTML, CSS, JavaScript, Chart.js
- pandas

## Структура проекта

- `apps/` — Django-приложения: авторизация, датчики, устройства и аналитика.
- `config/` — настройки Django, маршруты, ASGI/WSGI и Celery.
- `templates/` — HTML-шаблоны интерфейса.
- `frontend/` — каталог для будущих материалов фронтенда; текущий интерфейс находится в `templates/` и статических файлах приложений.
- `backend/` — каталог для будущих материалов серверной части; текущий backend находится в `apps/` и `config/`.
- `ml/` — каталог для будущих компонентов машинного обучения.
- `docs/` — проектная документация.

## Запуск локально (Windows PowerShell)

Требуется Python и установленный пакетный менеджер pip.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DJANGO_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(50))"
python manage.py migrate
python manage.py runserver
```

Откройте http://127.0.0.1:8000/. Для работы фоновых задач Celery необходим
запущенный Redis.

## Проверки

```powershell
$env:DJANGO_SECRET_KEY = "local-development-key"
python manage.py check
python manage.py test
```
