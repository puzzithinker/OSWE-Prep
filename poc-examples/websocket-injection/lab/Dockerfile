FROM node:18-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY server.js ./
RUN echo "OSWE{websocket_injection_lab_flag}" > /flag.txt
EXPOSE 8080
CMD ["node", "server.js"]
