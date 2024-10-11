import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode
import os
from dotenv import load_dotenv
from models import SessionLocal, User, Resource
import requests
import uuid
from datetime import datetime
import urllib3

# Подавление предупреждений о небезопасных соединениях
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GIGACHAT_AUTHORIZATION_KEY = os.getenv('GIGACHAT_AUTHORIZATION_KEY')
GIGACHAT_CLIENT_ID = os.getenv('GIGACHAT_CLIENT_ID')
DATABASE_URL = os.getenv('DATABASE_URL')

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class GigaChatAPI:
    def __init__(self, authorization_key):
        self.authorization_key = authorization_key
        self.access_token = None
        self.token_expiry = datetime.utcnow()

    def get_access_token(self):
        # Проверяем, истёк ли токен или отсутствует
        if self.access_token is None or datetime.utcnow() >= self.token_expiry:
            self.request_access_token()
        return self.access_token

    def request_access_token(self):
        url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'Authorization': f'Basic {self.authorization_key}',
            'RqUID': str(uuid.uuid4())
        }
        data = {
            'scope': 'GIGACHAT_API_PERS'
        }
        try:
            response = requests.post(url, headers=headers, data=data, verify=False)
            response.raise_for_status()
            token_info = response.json()
            self.access_token = token_info['access_token']
            # Преобразуем expires_at из миллисекунд в datetime
            self.token_expiry = datetime.utcfromtimestamp(token_info['expires_at'] / 1000)
            logger.info("Access token получен успешно.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении Access Token: {e}")
            raise

    def send_message(self, user_message):
        url = 'https://gigachat.devices.sberbank.ru/api/v1/chat/completions'
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.get_access_token()}',
            'Content-Type': 'application/json',
            'X-Client-ID': GIGACHAT_CLIENT_ID,
            'X-Request-ID': str(uuid.uuid4()),
            'X-Session-ID': str(uuid.uuid4())
        }
        payload = {
            "model": "GigaChat",
            "messages": [
                {"role": "system", "content": "Ты умный помощник в учебе."},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        try:
            response = requests.post(url, headers=headers, json=payload, verify=False)
            response.raise_for_status()
            response_data = response.json()
            # Извлекаем ответ модели
            answer = response_data['choices'][0]['message']['content'].strip()
            return answer
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при обращении к GigaChat API: {e}")
            return "Извините, я не смог обработать ваш запрос в данный момент."

# Инициализация GigaChat API
giga_chat_api = GigaChatAPI(GIGACHAT_AUTHORIZATION_KEY)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я StudyHomie, твой помощник в учебе с поддержкой искусственного интеллекта.\n\n"
        "Ты можешь задавать мне вопросы или запрашивать учебные материалы по любимым предметам.\n\n"
        "Вот команды, которые ты можешь использовать:\n"
        "/start - Приветственное сообщение\n"
        "/setsubjects - Установить интересующие тебя предметы\n"
        "/resources - Получить учебные материалы\n"
        "Или просто задай свой вопрос, и я постараюсь помочь!"
    )


# Команда /setsubjects
async def set_subjects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = ' '.join(context.args)
    if not user_input:
        await update.message.reply_text(
            "Пожалуйста, укажи свои предметы, разделенные запятыми. Пример: /setsubjects Математика, Физика"
        )
        return
    subjects = [subject.strip() for subject in user_input.split(',')]

    db_session = SessionLocal()
    try:
        user = db_session.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user:
            user = User(
                telegram_id=update.effective_user.id,
                username=update.effective_user.username,
                subjects=subjects
            )
            db_session.add(user)
        else:
            user.subjects = subjects
        db_session.commit()
    except Exception as e:
        logger.error(f"Ошибка при установке предметов: {e}")
        await update.message.reply_text("Произошла ошибка при установке твоих предметов. Пожалуйста, попробуй снова.")
    finally:
        db_session.close()

    await update.message.reply_text(f"Твои предметы установлены: {', '.join(subjects)}")


# Команда /resources
async def get_resources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_session = SessionLocal()
    try:
        user = db_session.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user or not user.subjects:
            await update.message.reply_text(
                "Ты еще не установил свои предметы. Используй команду /setsubjects, чтобы указать свои интересы."
            )
            return
        resources = db_session.query(Resource).filter(Resource.subject.in_(user.subjects)).all()
        if not resources:
            await update.message.reply_text("Не найдено материалов по твоим предметам.")
            return
        message = "Вот некоторые учебные материалы для тебя:\n\n"
        for res in resources:
            message += f"**{res.subject} - {res.type}**\n[{res.title}]({res.link})\n\n"
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Ошибка при получении материалов: {e}")
        await update.message.reply_text("Произошла ошибка при получении материалов. Пожалуйста, попробуй снова.")
    finally:
        db_session.close()


# Обработка вопросов
async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    await update.message.reply_text("Дай мне подумать над этим...")
    try:
        answer = giga_chat_api.send_message(question)
        await update.message.reply_text(answer)
    except Exception as e:
        logger.error(f"Ошибка при обращении к GigaChat API: {e}")
        await update.message.reply_text("Извините, я не смог обработать ваш запрос в данный момент.")


def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('setsubjects', set_subjects))
    application.add_handler(CommandHandler('resources', get_resources))

    # Обработчик сообщений для вопросов
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()