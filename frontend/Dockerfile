FROM node:16-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies for build)
RUN npm ci

# Copy frontend code
COPY . .

# Build the app
RUN npm run build

# Remove dev dependencies and install only production dependencies
RUN npm prune --production

# Install serve to run the built app
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Serve the built app
CMD ["serve", "-s", "dist", "-l", "3000"] 