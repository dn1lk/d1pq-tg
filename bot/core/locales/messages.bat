pybabel extract --input-dirs=. -o locales/messages.pot -k __ -k ___:1,2
pybabel update -d locales -D messages -i locales/messages.pot

pybabel compile -d locales -D messages
