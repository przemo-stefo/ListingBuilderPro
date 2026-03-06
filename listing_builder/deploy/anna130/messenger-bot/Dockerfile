# deploy/anna130/messenger-bot/Dockerfile
# Purpose: Puppeteer-based Messenger sender for Radar Radnego
# NOT for: Running Chrome permanently — launches only per-request

FROM node:20-slim

# Chromium deps
RUN apt-get update && apt-get install -y \
    chromium \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgbm1 \
    libnspr4 \
    libnss3 \
    libxss1 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Tell Puppeteer to use system Chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

WORKDIR /app
COPY package.json .
RUN npm install --production
COPY server.js .

# Persistent cookie storage
RUN mkdir -p /app/data
VOLUME /app/data

EXPOSE 3111
CMD ["node", "server.js"]
