import click
import sys
import subprocess
from models import init_db, Base, engine
from alembic.config import Config
from alembic import command
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

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


if __name__ == '__main__':
    cli()