# Development image for the Injection Lab web app.
# Compose bind-mounts the source at /app and keeps node_modules and .next in
# anonymous volumes, so the dependencies installed here are the ones used at runtime.
FROM node:24-alpine

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
