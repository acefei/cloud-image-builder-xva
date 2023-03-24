.PHONY: help
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

build-seed:    ## build seed.iso with the config in src/cloud-config-templates, eg: USER_DATA=user-date make build-seed
	docker compose run seed-iso-builder bash -x /app/seed-iso-builder.sh $(USER_DATA)

test-seed:
	docker compose run seed-iso-builder bash
