FROM node:22-alpine AS dashboard-ui
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
ARG VITE_GATEWAY_URL=http://iot-data-gateway:8080
ENV VITE_GATEWAY_URL=$VITE_GATEWAY_URL

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
