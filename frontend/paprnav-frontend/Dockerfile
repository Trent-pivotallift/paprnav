ARG NODE_BASE=node:24.13.0-alpine3.23@sha256:cd6fb7efa6490f039f3471a189214d5f548c11df1ff9e5b181aa49e22c14383e
FROM ${NODE_BASE} AS dependencies
WORKDIR /workspace
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

FROM ${NODE_BASE} AS builder
WORKDIR /workspace
ENV NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_PAPRNAV_ENV=pilot \
    NEXT_PUBLIC_PAPRNAV_API_BASE_URL=""
COPY --from=dependencies /workspace/node_modules ./node_modules
COPY . .
RUN npm run build

FROM ${NODE_BASE} AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_PAPRNAV_ENV=pilot \
    NEXT_PUBLIC_PAPRNAV_API_BASE_URL="" \
    HOSTNAME=0.0.0.0 \
    PORT=3000
RUN addgroup -S -g 10001 paprnav && adduser -S -D -H -u 10001 -G paprnav paprnav
COPY --from=builder --chown=10001:10001 /workspace/public ./public
COPY --from=builder --chown=10001:10001 /workspace/.next/standalone ./
COPY --from=builder --chown=10001:10001 /workspace/.next/static ./.next/static
USER 10001:10001
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:3000/ || exit 1
CMD ["node", "server.js"]
