clean:
	docker container rm almaz_bot
	docker volume rm almaz_db

up:
	cd deploy && docker compose up --build

down:
	cd deploy && docker compose down

check:
	ruff check ./src && ruff format ./src
	flake8 ./src --select=WPS --ignore WPS115 --exclude src/tests
	mypy ./src --exclude src/tests

.PHONY: clean, up, down, black, check