.PHONY: all play init test stop clean

all: test

play:
	asciinema play hyrise-r-demo.cast

init:
	pipenv install

test:
	python3.5 deployment.py

stop:
	docker ps \
		--quiet \
		--filter ancestor=$(NAME) \
	| xargs \
		--no-run-if-empty \
		docker stop

clean: stop
	docker system prune \
		--force
