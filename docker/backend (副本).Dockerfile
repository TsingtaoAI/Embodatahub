FROM tsintaorsl-base AS development

# Install runtime dependencies for Python (rosbags)
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install rosbags --break-system-packages --no-cache-dir
USER node

WORKDIR /app/backend

CMD ["./entrypoint.sh"]


FROM node:22-slim AS build

RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

COPY pnpm-lock.yaml ./
RUN pnpm fetch

COPY . .
RUN pnpm install -r

# Build packages and backend
RUN pnpm --filter @tsintaorsl/shared build
RUN pnpm --filter @tsintaorsl/validation build
RUN pnpm --filter @tsintaorsl/api-dto build
RUN pnpm --filter @tsintaorsl/backend-common build
RUN NODE_ENV=production pnpm --filter tsintaorsl-backend build
RUN pnpm deploy --filter=tsintaorsl-backend --prod --legacy /prod/backend

FROM gcr.io/distroless/nodejs22-debian12 AS production

WORKDIR /app

COPY --from=build /app/backend/dist/main.js ./backend/dist/main.js
COPY --from=build /app/backend/package.json ./backend/package.json
COPY --from=build /app/backend/assets/favicon.png ./backend/assets/favicon.png

WORKDIR /app/backend

CMD ["dist/main.js"]
