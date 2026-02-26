.PHONY: build test lint docker-build docker-push install-crds uninstall-crds run

IMG ?= agentura/operator:latest

build:
	go build -o bin/operator ./cmd/main.go

test:
	go test ./... -v

lint:
	golangci-lint run

run: build
	./bin/operator

docker-build:
	docker build -t $(IMG) .

docker-push: docker-build
	docker push $(IMG)

install-crds:
	kubectl apply -f config/crd/bases/

uninstall-crds:
	kubectl delete -f config/crd/bases/

deploy: install-crds
	kubectl apply -k ../deploy/k8s/operator/

undeploy:
	kubectl delete -k ../deploy/k8s/operator/
