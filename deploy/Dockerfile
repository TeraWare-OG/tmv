FROM node:20-alpine

RUN apk add --no-cache git docker-cli docker-cli-compose bash

WORKDIR /webhook
COPY webhook.js .

EXPOSE 9000
CMD ["node", "/webhook/webhook.js"]
