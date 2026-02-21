.PHONY: build run test lint clean proto docker-up docker-down migrate

APP_NAME := wealth-copilot
BUILD_DIR := bin
GO_FILES := $(shell find . -name '*.go' -not -path './vendor/*')

build:
	go build -o $(BUILD_DIR)/$(APP_NAME) ./cmd/server

run: build
	./$(BUILD_DIR)/$(APP_NAME)

test:
	go test ./... -v -race -count=1

test-cover:
	go test ./... -coverprofile=coverage.out -race
	go tool cover -html=coverage.out -o coverage.html

lint:
	golangci-lint run ./...

clean:
	rm -rf $(BUILD_DIR) coverage.out coverage.html

proto:
	buf generate proto/

docker-up:
	docker compose up -d

docker-down:
	docker compose down

migrate:
	@echo "Run migrations via GORM AutoMigrate on startup"

fmt:
	gofmt -w $(GO_FILES)

vet:
	go vet ./...
