.PHONY: all build test clean dev lint fmt help

all: build

# --- Build ---
build: build-sdk build-gateway build-web

build-sdk:
	cd sdk && pip install -e ".[server]"

build-gateway:
	cd gateway && go build -o bin/agentura-gateway ./cmd/server

build-web:
	cd web && npm ci && npm run build

# --- Test ---
test: test-sdk test-gateway

test-sdk:
	cd sdk && pytest tests/ -v

test-gateway:
	cd gateway && go test ./... -v

# --- Dev ---
dev:
	docker compose up --build

dev-deploy:
	docker compose -f deploy/docker-compose.yml up --build

# --- Lint ---
lint:
	cd gateway && golangci-lint run ./...
	cd sdk && ruff check .

# --- Format ---
fmt:
	cd gateway && gofmt -w .
	cd sdk && ruff format .

# --- Clean ---
clean:
	rm -rf gateway/bin/ web/.next/ sdk/dist/

# --- Help ---
help:
	@echo "Available targets:"
	@echo "  make build       - Build all components (sdk, gateway, web)"
	@echo "  make test        - Run all tests"
	@echo "  make dev         - Start full stack via Docker Compose"
	@echo "  make lint        - Run linters (golangci-lint + ruff)"
	@echo "  make fmt         - Format code (gofmt + ruff)"
	@echo "  make clean       - Remove build artifacts"
