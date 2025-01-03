build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs

clean:
	docker compose down --rmi all -v

stop:
	docker compose stop

requirements:
	pip install -r backend/requirements.txt
