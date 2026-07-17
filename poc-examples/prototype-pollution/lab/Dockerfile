FROM node:18-alpine
WORKDIR /app
COPY server.js ./
RUN echo "OSWE{prototype_pollution_lab_flag}" > /flag.txt
EXPOSE 3000
CMD ["node", "server.js"]
