clean:
	docker container rm almaz_bot
	docker volume rm almaz_db

up:
	cd deploy && docker compose up --build

down:
	cd deploy && docker compose down

black:
	black ./src
	isort ./src

check:
	ruff check ./src --exclude src/tests
	mypy ./src --exclude src/tests

.PHONY: clean, up, down, black, check