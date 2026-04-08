# Stage 1: Build the React app
FROM node:20-alpine AS build
WORKDIR /app

# Accept build arguments
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Serve the app with Nginx
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config if needed, or use default
# EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
