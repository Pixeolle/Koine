FROM node:24.19.0-alpine AS build

WORKDIR /frontend

ARG PUBLIC_API_URL
ARG PUBLIC_WS_URL
ARG INTERNAL_API_URL
ENV PUBLIC_API_URL=$PUBLIC_API_URL
ENV PUBLIC_WS_URL=$PUBLIC_WS_URL
ENV INTERNAL_API_URL=$INTERNAL_API_URL

COPY ./frontend/public ./public/
COPY ./frontend/src ./src/
COPY ./frontend/astro.config.mjs ./frontend/components.json ./frontend/package.json ./frontend/svelte.config.js ./frontend/tsconfig.json ./

RUN --mount=type=secret,id=npmrc,target=/frontend/.npmrc \
    npm install

RUN npm run build

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=4321

CMD ["node", "./dist/server/entry.mjs"]
