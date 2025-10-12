
# Use official Node.js image as the base image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Install Angular CLI globally
RUN npm install -g @angular/cli@latest

# Copy the rest of the application code
COPY . .

# Build the Angular app in production mode
RUN npm run build -- --output-path=dist

# Expose port 4200
EXPOSE 4200

# Serve the application
CMD ["ng", "serve", "--host", "0.0.0.0"]
