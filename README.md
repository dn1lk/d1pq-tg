# //delete

-- Async Python [Telegram bot](https://t.me/d1pq_bot)

A text-generating bot based on current chat with playing functions.

## Setup

### Requirements

In [requirements.txt](requirements.txt) (:

### Environments

Before start fill [.env](.env.example) and [yc.env](yc.env.example).

### Makefile

1. Create YC serverless container: <code>make create</code>
2. Fill **YC_CATALOG_ID** and **YC_REGISTRY_ID** in [.env](.env.example) and [yc.env](yc.env.example)
3. Create YC API-gateway: <code>make create_gw</code>
4. Fill **WEBHOOK_URL** in [.env](.env.example)
5. Update YC API-gateway [creds](api-gw.yaml.example) in the service
6. Create YC YDB, fill [database.env](database.env.example)
7. *(Optional)* Create YC Redis, fill [redis.env](redis.env.example)
8. Deploy to YC: <code>make deploy</code>

It will set up Yandex Cloud serverless container, create Yandex Cloud API-gateway, setup webhook and deploy container.

-- Ready to use!
