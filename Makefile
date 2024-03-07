.DEFAULT_GOAL := build_local
COMPOSE := docker-compose -f build/docker-compose.yml
CURRENT_VERSION_TAG := v0.1
BUILDX := docker buildx build -f build/Dockerfile --platform linux/amd64,linux/arm64
EXEC := docker exec -it build-spotifymgr-1

build_local:
	docker build -f build/Dockerfile -t ilyatbn/spotifymgr:latest .

build_dev:
	$(BUILDX) -t ilyatbn/spotifymgr-dev:$(CURRENT_VERSION_TAG) -t ilyatbn/spotifymgr-dev:latest --push .

build_prod:
	$(BUILDX) -t ilyatbn/spotifymgr:$(CURRENT_VERSION_TAG) -t ilyatbn/spotifymgr:latest --push .

start:
	$(COMPOSE) up -d --remove-orphans


stop:
	$(COMPOSE) stop

restart: stop start

remove:
	$(COMPOSE) down
	$(COMPOSE) rm -v

shell:
	$(EXEC) ipython

bash:
	$(EXEC) bash

logs:
	docker logs -f build-spotifymgr-1

uvicorn:
	cd src && ../venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8181
