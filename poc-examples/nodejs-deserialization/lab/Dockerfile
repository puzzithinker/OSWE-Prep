FROM node:18-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY server.js ./
RUN echo "OSWE{node_deserial_lab_flag}" > /flag.txt
EXPOSE 3000
CMD ["node", "server.js"]
