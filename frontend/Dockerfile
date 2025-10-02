# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim

WORKDIR /app

ENV NODE_ENV=development \
    NEXT_TELEMETRY_DISABLED=1 \
    WATCHPACK_POLLING=true \
    CHOKIDAR_USEPOLLING=true

# Dependencies will be installed at runtime to support bind mounts reliably
COPY package*.json ./

# Expose dev port
EXPOSE 3000

CMD ["sh", "-lc", "npm ci && npm run dev"]


