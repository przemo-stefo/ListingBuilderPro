# deploy/grzegorz152/frontend/Dockerfile
# Purpose: Multi-stage production build for Next.js frontend on grzegorz152
# NOT for: Local development or Vercel deployment

FROM node:20-alpine AS builder

WORKDIR /app

# WHY: Copy lock+manifest first for Docker layer caching
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# WHY: Build-time env vars for Next.js static optimization
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# --- Runtime stage ---
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# WHY: Run as non-root for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# WHY: standalone output includes only what's needed (~50MB vs ~500MB)
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
