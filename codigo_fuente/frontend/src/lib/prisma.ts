import { PrismaClient } from "@prisma/client";
import { PrismaBetterSqlite3 } from "@prisma/adapter-better-sqlite3";

// Inicializar el adaptador de base de datos de Prisma 7 para SQLite
const adapter = new PrismaBetterSqlite3({
  url: process.env.DATABASE_URL || "file:../backend/sysmap.db"
});

const globalForPrisma = global as unknown as { prisma: PrismaClient };

export const prisma =
  globalForPrisma.prisma ||
  new PrismaClient({
    adapter,
    log: ["query"],
  });

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;


