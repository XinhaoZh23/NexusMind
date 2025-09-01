# Stage 1: Build the React application
FROM node:18-alpine AS build

# Set the working directory
WORKDIR /app/frontend

# Copy package.json and package-lock.json from the frontend directory
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend application source code
COPY frontend/ .

# Declare the ARG that will be passed from the docker build command
ARG VITE_API_KEY

# Set the ARG as an environment variable
ENV VITE_API_KEY=$VITE_API_KEY

# Build the application for production
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:latest

# Copy the custom Nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Copy the build output from the build stage to Nginx's web server directory
COPY --from=build /app/frontend/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx when the container launches
CMD ["nginx", "-g", "daemon off;"] 