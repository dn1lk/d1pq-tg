include .env
include yc.env

export IMAGE_NAME=cr.yandex/$(YC_REGISTRY_ID)/$(SERVERLESS_CONTAINER_NAME)

YC_APIGW_FILE_SPEC = api-gw.yaml

LOCALE_DIR = bot/core/locales
LOCALE_DOMAIN = messages

WEBHOOK_PATH ?= webhook/bot$(BOT_TOKEN)


# Yandex Cloud
create: ## create serverless container
	yc serverless container create --folder-id $(YC_CATALOG_ID) --name $(SERVERLESS_CONTAINER_NAME)
	yc serverless container allow-unauthenticated-invoke --folder-id $(YC_CATALOG_ID) --name  $(SERVERLESS_CONTAINER_NAME)

$(YC_APIGW_FILE_SPEC): ## setup API gateway spec
	$(shell sed "s|WEBHOOK_URL|$(WEBHOOK_URL)|;s|WEBHOOK_PATH|$(WEBHOOK_PATH)|;s|SERVERLESS_CONTAINER_ID|$(SERVERLESS_CONTAINER_ID)|;s|SERVICE_ACCOUNT_ID|$(YC_SERVICE_ACCOUNT_ID)|" $(YC_APIGW_FILE_SPEC).example > $(YC_APIGW_FILE_SPEC))
create_gw: $(YC_APIGW_FILE_SPEC)
	yc serverless api-gateway create --folder-id $(YC_CATALOG_ID) --name $(YC_APIGW_NAME) --spec $(YC_APIGW_FILE_SPEC)

bot/$(YC_SERVICE_ACCOUNT_FILE_CREDENTIALS): ## setup serverless account creds
	yc iam key create \
		--folder-id $(YC_CATALOG_ID) \
		--service-account-name $(YC_SERVICE_ACCOUNT_NAME) \
		--output bot/$(YC_SERVICE_ACCOUNT_FILE_CREDENTIALS) \
		--folder-id $(YC_CATALOG_ID)


# Webhook
get_webhook:
	curl --request POST --url "https://api.telegram.org/bot$(BOT_TOKEN)/getWebhookInfo"

set_webhook:
	cd bot && $(shell sed 's|^||g' *.env .env | tr -s "\r\n" " " | cut -c2-) python webhook.py


# Locale
update_locale:
	pybabel extract --project=d1pq --input-dirs=bot -o $(LOCALE_DIR)/$(LOCALE_DOMAIN).pot -k __ -k ___:1,2
	pybabel update --update-header-comment -d $(LOCALE_DIR) -D $(LOCALE_DOMAIN) -i $(LOCALE_DIR)/$(LOCALE_DOMAIN).pot

compile_locale: update_locale
	pybabel compile -d $(LOCALE_DIR) -D $(LOCALE_DOMAIN)


# Docker
login: bot/$(YC_SERVICE_ACCOUNT_FILE_CREDENTIALS) ## login docker with service account creds
	cat bot/$(YC_SERVICE_ACCOUNT_FILE_CREDENTIALS) | docker login \
		--username json_key \
		--password-stdin cr.yandex

build: login compile_locale
	$(shell for env_file in .env *.env; do sed 's|=.*|=|' $$env_file > $$env_file.example; done)
	docker compose build

up: build ## run locale build
	docker compose up

push: build
	docker compose push

deploy: push set_webhook
	yc serverless container revision deploy \
		--folder-id $(YC_CATALOG_ID) \
		--container-name $(SERVERLESS_CONTAINER_NAME) \
		--image '$(IMAGE_NAME):latest' \
		--core-fraction 20 \
		--memory 512MB \
		--concurrency 5 \
		--execution-timeout 10m \
		--environment '$(shell sed 's|^|,|g' *.env .env | tr -s "\r\n" "," | cut -c2-)' \
		--service-account-id $(YC_SERVICE_ACCOUNT_ID)

all: create create_gw deploy