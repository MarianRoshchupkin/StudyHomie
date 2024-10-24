import click
import sys
import subprocess
from models import init_db, Base, engine
from alembic.config import Config
from alembic import command
from dotenv import load_dotenv
import validators

# Загрузка переменных окружения
load_dotenv()

# Определение доступных предметов
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

@click.group()
def cli():
    """Утилита для управления проектом StudyHomie."""
    pass


@cli.command()
def initdb():
    """
    Инициализирует базу данных, создавая все таблицы.
    """
    click.echo("Инициализация базы данных...")
    try:
        init_db()
        click.echo("Таблицы успешно созданы!")
    except Exception as e:
        click.echo(f"Ошибка при инициализации базы данных: {e}")


@cli.command()
@click.option('--message', default="New migration", help='Описание миграции.')
def migrate(message):
    """
    Создаёт новую миграцию и применяет её.
    """
    click.echo("Создание новой миграции...")
    try:
        # Создание миграции
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", message], check=True)
        click.echo("Миграция создана успешно.")

        # Применение миграции
        click.echo("Применение миграций...")
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        click.echo("Миграции успешно применены.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Ошибка при выполнении миграций: {e}")


@cli.command()
def runbot():
    """
    Запускает Telegram-бота после применения миграций.
    """
    click.echo("Применение миграций перед запуском бота...")
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        click.echo("Миграции успешно применены.")
    except Exception as e:
        click.echo(f"Ошибка при применении миграций: {e}")
        sys.exit(1)

    click.echo("Запуск Telegram-бота...")
    try:
        subprocess.run([sys.executable, "bot.py"], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Ошибка при запуске бота: {e}")


@cli.command()
def resetdb():
    """
    Полностью сбрасывает базу данных (удаляет все таблицы) и инициализирует её заново.
    """
    confirm = click.prompt(
        "Вы уверены, что хотите сбросить базу данных? Это действие необратимо. Введите 'yes' чтобы продолжить",
        default="no")
    if confirm.lower() == 'yes':
        click.echo("Сброс базы данных...")
        try:
            # Удаление всех таблиц
            Base.metadata.drop_all(engine)
            click.echo("Все таблицы удалены.")

            # Инициализация базы данных заново
            init_db()
            click.echo("База данных инициализирована заново.")
        except Exception as e:
            click.echo(f"Ошибка при сбросе базы данных: {e}")
    else:
        click.echo("Сброс базы данных отменён.")


@cli.command()
def status():
    """
    Показывает текущий статус миграций.
    """
    click.echo("Проверка статуса миграций...")
    try:
        alembic_cfg = Config("alembic.ini")
        command.current(alembic_cfg)
    except Exception as e:
        click.echo(f"Ошибка при получении статуса миграций: {e}")


@cli.command()
def downgrade():
    """
    Откатывает последнюю миграцию.
    """
    click.echo("Откат последней миграции...")
    try:
        alembic_cfg = Config("alembic.ini")
        command.downgrade(alembic_cfg, "-1")
        click.echo("Последняя миграция откатена.")
    except Exception as e:
        click.echo(f"Ошибка при откате миграции: {e}")


@cli.command()
@click.option(
    '--subject',
    type=click.IntRange(1, len(AVAILABLE_SUBJECTS)),
    prompt='Выберите предмет:\n' + '\n'.join([f'{i + 1}. {s}' for i, s in enumerate(AVAILABLE_SUBJECTS)]),
    help='Номер предмета'
)
@click.option(
    '--type',
    type=click.IntRange(1, 3),
    prompt='Тип ресурса (1. Статья, 2. Видео, 3. Туториал)',
    help='Тип ресурса'
)
@click.option('--title', prompt='Название статьи, видео или туториала', help='Название статьи, видео или туториала')
@click.option('--link', prompt='Ссылка на ресурс', help='Ссылка на ресурс')
def addresource(subject, type, title, link):
    """
    Добавляет новый учебный ресурс в базу данных.
    """
    click.echo("Добавление нового учебного ресурса.")
    try:
        # Маппинг чисел на типы ресурсов
        type_mapping_display = {1: 'Статья', 2: 'Видео', 3: 'Туториал'}
        type_mapping_internal = {1: 'Article', 2: 'Video', 3: 'Tutorial'}

        type_selected_display = type_mapping_display.get(type)
        type_selected_internal = type_mapping_internal.get(type)

        if not type_selected_display or not type_selected_internal:
            raise ValueError("Неверный выбор типа ресурса.")

        # Маппинг числа на предмет
        subject_selected = AVAILABLE_SUBJECTS[subject - 1]

        # Валидация и обработка переданных параметров
        subject_selected = subject_selected.strip()
        if not subject_selected:
            raise ValueError("Предмет не может быть пустым.")

        title = title.strip()
        if not title:
            raise ValueError("Название ресурса не может быть пустым.")

        if not validators.url(link):
            raise ValueError("Некорректный формат URL.")

        # Подтверждение введённых данных
        click.echo("\nВы добавляете ресурс со следующими данными:")
        click.echo(f"Предмет: {subject_selected}")
        click.echo(f"Тип: {type_selected_display}")
        click.echo(f"Название: {title}")
        click.echo(f"Ссылка: {link}")

        confirm = click.confirm("Вы уверены, что хотите добавить этот ресурс?", default=True)
        if not confirm:
            click.echo("Добавление ресурса отменено.")
            sys.exit(0)

        # Вызов скрипта add_resources.py с аргументами
        subprocess.run([
            sys.executable,
            "add_resources.py",
            "--subject", subject_selected,
            "--type", type_selected_internal,  # Передаём английский тип
            "--title", title,
            "--link", link
        ], check=True)
        click.echo(f"Ресурс '{title}' успешно добавлен.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Ошибка при добавлении ресурса: {e}")
    except ValueError as ve:
        click.echo(f"Ошибка ввода: {ve}")
    except Exception as e:
        click.echo(f"Произошла непредвиденная ошибка: {e}")


if __name__ == '__main__':
    cli()