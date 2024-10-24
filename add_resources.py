import argparse
from models import Resource, SessionLocal
import sys

def main():
    parser = argparse.ArgumentParser(description='Добавление ресурса в базу данных.')
    parser.add_argument('--subject', required=True, help='Предмет')
    parser.add_argument('--type', choices=['Article', 'Video', 'Tutorial'], required=True, help='Тип ресурса')
    parser.add_argument('--title', required=True, help='Название ресурса')
    parser.add_argument('--link', required=True, help='Ссылка на ресурс')

    args = parser.parse_args()

    # Маппинг английских типов на русские
    type_mapping_reverse = {
        'Article': 'Статья',
        'Video': 'Видео',
        'Tutorial': 'Туториал'
    }

    type_russian = type_mapping_reverse.get(args.type)
    if not type_russian:
        print("Неверный тип ресурса.")
        sys.exit(1)

    # Создание нового ресурса
    new_resource = Resource(
        subject=args.subject,
        type=type_russian,  # Сохраняем русский тип
        title=args.title,
        link=args.link
    )

    try:
        with SessionLocal() as session:
            session.add(new_resource)
            session.commit()
        print(f"Ресурс '{args.title}' успешно добавлен.")
    except Exception as e:
        print(f"Ошибка при добавлении ресурса: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()