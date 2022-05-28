define README

FLEET MANAGEMENT

This file is to simplify development of the fleet management system.
All available commands are listed below.

endef
export README

help:
	@echo "$$README"
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

build-%: 		## Builds the docker image [% = server/client]
	docker build --pull --rm --file "$*/Dockerfile" --tag rikpet/easy-living:fm-$*-beta $*

push-%:			## Push docker image to docker hub [% = server/client]. Need to be signed in to Docker hub
	docker push rikpet/easy-living:fm-$*-beta

run-%:			## Runs the docker image, will not build new images [% = server/client]
	docker-compose --file $*/docker-compose.yaml up -d

deploy-%:		## Deploys the application, runs both a build and the runs the image [% = server/client]
deploy-%: build-% run-% 

pylint:			## Run pylint on repository
	pylint --fail-under=9.5 $$(git ls-files '*.py')

pytest:			## Ryn pytest
	pytest

check-wf: 		## Run github workflows
check-wf: pylint pytest
