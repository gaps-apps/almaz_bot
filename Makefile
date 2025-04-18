clean:
	docker container rm almaz_bot
	docker volume rm almaz_db

up:
	cd deploy && docker compose up --build

down:
	cd deploy && docker compose down

black:
	black ./src
	python -m isort ./src

check:
	ruff check ./src
	python -m mypy ./src

.PHONY: clean, up, down, black, check