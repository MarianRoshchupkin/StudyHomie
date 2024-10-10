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
import openai
import os
from dotenv import load_dotenv
from models import SessionLocal, User, Resource, DiscussionGroup

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY  # Установка API ключа

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я StudyBuddy, твой помощник в учебе с поддержкой искусственного интеллекта.\n"
        "Ты можешь задавать мне вопросы или запрашивать учебные материалы по любимым предметам.\n\n"
        "Вот команды, которые ты можешь использовать:\n"
        "/start - Приветственное сообщение\n"
        "/help - Показать это сообщение помощи\n"
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
                subjects=subjects,
                progress={}
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
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Или "gpt-4", если у вас есть доступ
            messages=[
                {"role": "system", "content": "Ты умный помощник в учебе."},
                {"role": "user", "content": question}
            ],
            max_tokens=500,
            temperature=0.7
        )
        answer = response['choices'][0]['message']['content'].strip()
        await update.message.reply_text(answer)
    except Exception as e:
        logger.error(f"Ошибка при обращении к OpenAI API: {e}")
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