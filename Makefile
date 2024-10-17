initdb:
	python manage.py initdb

migrate:
	python manage.py migrate --message "$(msg)"

runbot:
	python manage.py runbot

resetdb:
	python manage.py resetdb

status:
	python manage.py status

downgrade:
	python manage.py downgrade