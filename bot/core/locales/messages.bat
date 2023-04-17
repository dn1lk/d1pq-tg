cd bot

pybabel extract --input-dirs=. -o core/locales/messages.pot -k __ -k ___:1,2
pybabel update -d core/locales -D messages -i core/locales/messages.pot

pybabel compile -d core/locales -D messages
