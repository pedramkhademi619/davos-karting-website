FROM node:20.18.0-alpine3.20 AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

# Inlined at build time; docker-compose.yml passes them from .env (no defaults here, so a value lives only in .env):
# the main site and the booking subdomain (src/lib/urls.ts; an empty booking URL keeps booking on the main site), and
# the venue's phone number and location (src/lib/venue.ts).
ARG NEXT_PUBLIC_SITE_URL
ARG NEXT_PUBLIC_BOOKING_URL
ARG NEXT_PUBLIC_CONTACT_PHONE
ARG NEXT_PUBLIC_VENUE_LATITUDE
ARG NEXT_PUBLIC_VENUE_LONGITUDE
ENV NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL \
    NEXT_PUBLIC_BOOKING_URL=$NEXT_PUBLIC_BOOKING_URL \
    NEXT_PUBLIC_CONTACT_PHONE=$NEXT_PUBLIC_CONTACT_PHONE \
    NEXT_PUBLIC_VENUE_LATITUDE=$NEXT_PUBLIC_VENUE_LATITUDE \
    NEXT_PUBLIC_VENUE_LONGITUDE=$NEXT_PUBLIC_VENUE_LONGITUDE

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000

CMD ["node", "server.js"]
