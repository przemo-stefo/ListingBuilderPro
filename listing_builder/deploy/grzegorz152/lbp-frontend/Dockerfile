# deploy/grzegorz152/lbp-frontend/Dockerfile
# Purpose: Multi-stage production build for LBP Next.js frontend on grzegorz152
# NOT for: Local development or Vercel deployment

FROM node:20-alpine AS builder

WORKDIR /app

# WHY ARG: NEXT_PUBLIC_ vars must exist at build time — Next.js inlines them into JS bundles
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY

# WHY: Copy lock+manifest first for Docker layer caching
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

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

# WHY: sharp required for Next.js image optimization in standalone mode
RUN npm i sharp@0.33

# WHY: standalone output includes only what's needed (~50MB vs ~500MB)
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# WHY: Next.js needs writable cache dir for image optimization + ISR
RUN mkdir -p .next/cache && chown -R nextjs:nodejs .next/cache

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
