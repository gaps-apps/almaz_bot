clean:
	docker container rm almaz_bot
	docker volume rm almaz_db

up:
	docker compose up --build

down:
	docker compose down

black:
	black .
	python -m isort .

.PHONY: clean, up, down, black