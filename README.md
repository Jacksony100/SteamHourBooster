# 🎮 Steam Farming Platform (Flask + Gevent)

Этот проект — платформа для управления множеством Steam-аккаунтов с возможностью фарминга времени в играх, контроля подписки, авторизации и админ-панели.

## 🚀 Основной функционал

- 🔐 Регистрация и логин пользователей с шифрованием паролей (Fernet)
- ⏳ Подписочная модель с проверкой через декораторы
- 🎮 Добавление Steam-аккаунтов (с шифрованием логинов и паролей)
- 🕹️ Фарминг игр (games_played) с интерфейсом запуска и остановки
- 📥 Получение списка игр аккаунта через Steam API
- ⛔ Получение информации о банах аккаунта
- 👑 Админ-панель (выдача подписки, бан, управление пользователями)
- 💸 Оплата подписки через криптовалюту (Coinbase Commerce, пример)
- 🧠 SQLite + Gevent + Flask + ThreadPoolExecutor

## 📸 Скриншоты

| Интерфейс | Описание |
|----------|----------|
| ![scr1](screenshots/scr1.jpg) | Форма входа |
| ![scr2](screenshots/scr2.jpg) | Форма регестрации |
| ![scr3](screenshots/scr3.jpg) | Нету подписки |
| ![scr4](screenshots/scr4.jpg) | Покупка подписки (заглушка) |
| ![scr5](screenshots/scr5.jpg) | Главная страница |
| ![scr6](screenshots/scr6.jpg) | Главная страница (белая тема) |
| ![scr7](screenshots/scr7.jpg) | Админ-Панель |

## 🛠 Установка

```bash
git clone https://github.com/Jacksony100/SteamHourBooster.git
cd steam-farming-platform
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
