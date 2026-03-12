

FROM node:20-alpine as build-stage
WORKDIR /app


COPY package*.json ./


RUN npm install --ignore-scripts --legacy-peer-deps


COPY . .

ENV JSC_TRANSFORM_OPTIMIZER=0 

RUN npx quasar prepare

RUN npm run build || echo "Build failed via npm, trying direct quasar build..." && npx quasar build

FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/dist/spa /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]