import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
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

# Список доступных предметов
AVAILABLE_SUBJECTS = [
    'Математика',
    'Физика',
    'Химия',
    'Биология',
    'История',
    'Литература',
    'Информатика',
    'География',
    'Английский язык',
    'Русский язык'
]

# Глобальный словарь для отслеживания выбранных предметов пользователями
user_subject_selections = {}

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
            response = requests.post(url, headers=headers, data=data, verify=False)  # verify=False временно
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
            response = requests.post(url, headers=headers, json=payload, verify=False)  # verify=False временно
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
        "/help - Показать это сообщение помощи\n"
        "/setsubjects - Установить интересующие тебя предметы\n"
        "/resources - Получить учебные материалы\n\n"
        "Или просто задай свой вопрос, и я постараюсь помочь!"
    )

# Команда /welcome
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Начать", callback_data="start_app")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Добро пожаловать! Нажмите кнопку ниже, чтобы начать.",
        reply_markup=reply_markup
    )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Вот команды, которые ты можешь использовать:\n"
        "/help - Показать это сообщение помощи\n"
        "/setsubjects - Установить интересующие тебя предметы\n"
        "/resources - Получить учебные материалы\n\n"
        "Или просто задай свой вопрос, и я постараюсь помочь!"
    )
    await update.message.reply_text(help_text)

# Команда /setsubjects
async def set_subjects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_subject_selections[user_id] = set()  # Инициализируем пустое множество для выбранных предметов

    keyboard = []
    for subject in AVAILABLE_SUBJECTS:
        keyboard.append([InlineKeyboardButton(subject, callback_data=f"subject_{subject}")])
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="done")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Пожалуйста, выберите ваши предметы, нажимая на соответствующие кнопки. После выбора нажмите '✅ Готово'.",
        reply_markup=reply_markup
    )

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

# Обработка Callback Queries
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Подтверждаем получение нажатия

    user_id = query.from_user.id
    data = query.data

    if data == "start_app":
        # Вызываем функцию start
        await start(update, context)
    elif data.startswith("subject_"):
        subject = data.split("subject_")[1]
        if subject in user_subject_selections.get(user_id, set()):
            user_subject_selections[user_id].remove(subject)
            # Обновляем кнопку на невыбранную
            new_text = f"❌ {subject}"
        else:
            user_subject_selections.setdefault(user_id, set()).add(subject)
            # Обновляем кнопку на выбранную
            new_text = f"✅ {subject}"

        # Перестраиваем клавиатуру с обновлённым статусом кнопок
        keyboard = []
        for subj in AVAILABLE_SUBJECTS:
            if subj in user_subject_selections[user_id]:
                button_text = f"✅ {subj}"
            else:
                button_text = f"❌ {subj}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"subject_{subj}")])
        keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="done")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Пожалуйста, выберите ваши предметы, нажимая на соответствующие кнопки. После выбора нажмите '✅ Готово'.",
            reply_markup=reply_markup
        )

    elif data == "done":
        selected_subjects = list(user_subject_selections.get(user_id, set()))
        if not selected_subjects:
            await query.edit_message_text("Вы не выбрали ни одного предмета. Пожалуйста, попробуйте снова команду /setsubjects.")
            user_subject_selections.pop(user_id, None)
            return

        # Сохраняем выбранные предметы в базу данных
        db_session = SessionLocal()
        try:
            user = db_session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                user = User(
                    telegram_id=user_id,
                    username=query.from_user.username,
                    subjects=selected_subjects
                )
                db_session.add(user)
            else:
                user.subjects = selected_subjects
            db_session.commit()
            await query.edit_message_text(f"Твои предметы успешно установлены: {', '.join(selected_subjects)}")
        except Exception as e:
            logger.error(f"Ошибка при установке предметов: {e}")
            await query.edit_message_text("Произошла ошибка при установке твоих предметов. Пожалуйста, попробуй снова.")
        finally:
            db_session.close()
            user_subject_selections.pop(user_id, None)


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
    application.add_handler(CommandHandler('welcome', welcome))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('setsubjects', set_subjects))
    application.add_handler(CommandHandler('resources', get_resources))

    # Обработчик Callback Queries
    application.add_handler(CallbackQueryHandler(button_handler))

    # Обработчик сообщений для вопросов
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()