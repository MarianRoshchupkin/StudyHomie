import argparse
from models import Resource, SessionLocal
import sys
import traceback

def clean_string(s):
    return ''.join(c for c in s if not (0xD800 <= ord(c) <= 0xDFFF))


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

    # Очистка названия от некорректных символов
    cleaned_title = clean_string(args.title)

    # Создание нового ресурса
    new_resource = Resource(
        subject=args.subject,
        type=type_russian,  # Сохраняем русский тип
        title=cleaned_title,
        link=args.link
    )

    try:
        with SessionLocal() as session:
            session.add(new_resource)
            session.commit()
    except Exception as e:
        print("Произошла ошибка при добавлении ресурса:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()