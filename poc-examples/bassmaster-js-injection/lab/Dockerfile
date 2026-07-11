FROM node:18-alpine
WORKDIR /app
COPY server.js ./
RUN echo "OSWE{bassmaster_lab_flag}" > /flag.txt
EXPOSE 8080
CMD ["node", "server.js"]
