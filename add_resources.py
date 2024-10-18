import argparse
import os
from models import SessionLocal, Resource, init_db
from dotenv import load_dotenv


def add_resource(subject, type_, title, link):
    db_session = SessionLocal()
    try:
        resource = Resource(
            subject=subject,
            type=type_,
            title=title,
            link=link
        )
        db_session.add(resource)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
    finally:
        db_session.close()


def main():
    load_dotenv()
    init_db()

    parser = argparse.ArgumentParser(description="Добавление нового учебного ресурса.")
    parser.add_argument('--subject', required=True, help='Тема ресурса (например, Математика)')
    parser.add_argument('--type', required=True, choices=['Article', 'Video', 'Tutorial'], help='Тип ресурса')
    parser.add_argument('--title', required=True, help='Название ресурса')
    parser.add_argument('--link', required=True, help='Ссылка на ресурс')

    args = parser.parse_args()

    add_resource(args.subject, args.type, args.title, args.link)


if __name__ == '__main__':
    main()