FROM node:24

WORKDIR /app

COPY package.json ./

RUN npm install

COPY . .

CMD ["sh", "-c", "npm run test:frontend && npm run test:backend"]
