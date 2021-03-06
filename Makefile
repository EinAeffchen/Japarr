build:
	docker build -t japarr .

push:
	docker tag japarr einaeffchen/japarr:0.1
	docker push einaeffchen/japarr:0.1

build-develop: build
	docker tag japarr einaeffchen/japarr:develop
	docker push einaeffchen/japarr:develop

up:
	docker-compose up -d

deploy: build push up

test: build
	docker run --rm --entrypoint=python japarr -m pytest /src/japarr/tests \
	japarr
