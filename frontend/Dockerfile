FROM node:20-alpine

WORKDIR /app

# Copy dependency manifests first for better layer caching
COPY package.json package-lock.json ./

# Install dependencies deterministically from the committed lockfile
RUN npm ci --no-audit --no-fund

# Copy the rest of the application source
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
