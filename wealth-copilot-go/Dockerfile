FROM golang:1.24-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /bin/wealth-copilot ./cmd/server

FROM alpine:3.19

RUN apk --no-cache add ca-certificates tzdata
WORKDIR /app

COPY --from=builder /bin/wealth-copilot .
COPY config/ config/

EXPOSE 8080
ENTRYPOINT ["./wealth-copilot"]
