# StarDrop Telegram Bot

Бот для ручной продажи Telegram Stars и Telegram Premium.

## 1. Куда вставить токен

1. Откройте файл `.env`.
2. Найдите строку:
   ```env
   BOT_TOKEN=PASTE_YOUR_BOT_TOKEN_HERE
   ```
3. Замените `PASTE_YOUR_BOT_TOKEN_HERE` на токен вашего бота.

Токен выдает [@BotFather](https://t.me/BotFather):

1. Откройте @BotFather в Telegram.
2. Отправьте команду `/newbot`.
3. Создайте бота и скопируйте выданный токен.

## 2. Где взять ADMIN_ID

`ADMIN_ID` — это ваш Telegram ID. Он нужен, чтобы бот понимал, кому отправлять новые заказы.

Самый простой способ:

1. Откройте в Telegram бота [@userinfobot](https://t.me/userinfobot).
2. Нажмите Start.
3. Скопируйте ваш числовой ID.
4. Вставьте его в `.env`:
   ```env
   ADMIN_ID=123456789
   ```

## 3. Как установить зависимости

Откройте терминал в папке проекта и выполните:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Если `python3.12` не установлен, установите Python 3.12 и повторите команды.

## 4. Как запустить бота

Проверьте, что `.env` заполнен реальными значениями:

```env
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_ID=ваш_числовой_telegram_id
```

Запустите:

```bash
python bot.py
```

После запуска откройте вашего бота в Telegram и отправьте команду `/start`.

## 5. Как проверить проект

```bash
pytest
python bot.py
```

Если в `.env` остались строки `PASTE_YOUR_BOT_TOKEN_HERE` или `PASTE_YOUR_TELEGRAM_ID_HERE`, бот не запустится и покажет понятную ошибку, что нужно заполнить `.env`.
