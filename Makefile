POETRY := python3.10 -m poetry

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' ${MAKEFILE_LIST} | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

install: ## install
	$(POETRY) install

init: install ## init
	$(POETRY) run pre-commit install

dev.start: install ## start dev server
	$(POETRY) run python src/manage.py runserver

requirements.txt: install ## generate requirements.txt
	$(POETRY) export -f requirements.txt --output requirements.txt

docker.compose.build:  ## docker compose build
	docker compose build

docker.compose.up: docker.compose.build ## docker compose up
	docker compose up

docker.compose.up.d: docker.compose.build ## docker compose up -d
	docker compose up -d

docker.compose.down: ## docker compose down
	docker compose down

docker.compose.down.volumes: ## docker compose down -v
	docker compose down -v

docker.compose.run.bash.%: docker.compose.build ## docker compose run <service-name> bash
	docker compose run $* bash

# Flags

.PHONY: *
