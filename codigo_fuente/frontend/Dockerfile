FROM node:20-alpine AS builder

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar módulos nativos de C++ (como better-sqlite3)
RUN apk add --no-cache python3 make g++

# Instalar dependencias
COPY package*.json ./
RUN npm ci

# Copiar el código fuente y el esquema de Prisma
COPY . .

# Generar cliente de Prisma
RUN npx prisma generate

# Compilar Next.js para producción
RUN npm run build

# Stage de ejecución ligero
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

# Copiar los compilados y dependencias necesarias para producción
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/prisma ./prisma
COPY --from=builder /app/prisma.config.ts ./
COPY --from=builder /app/tsconfig.json ./

EXPOSE 3000

# Ejecutar el servidor Next.js
CMD ["npm", "run", "start"]
