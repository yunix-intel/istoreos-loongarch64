#!/usr/bin/env node
/**
 * Minimal PostgreSQL migration runner for Prisma-generated migrations.
 *
 * Prisma 7 ships no Rust schema-engine for linux-loong64, so `prisma migrate
 * deploy` cannot run in this image. This script applies every
 * <migration>/migration.sql in lexical order and maintains Prisma's
 * `_prisma_migrations` table with the same columns/checksum format, so an
 * x86 host can still inspect or `prisma migrate deploy` the database later.
 *
 * Usage: DATABASE_URL=postgresql://... node prisma-migrate.mjs
 * Env:   PRISMA_MIGRATIONS_DIR (default /data/packages/prisma/migrations)
 *        MIGRATION_LOCK_TIMEOUT_MS, MIGRATION_CONNECT_RETRIES
 */
import { createHash, randomUUID } from "node:crypto";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import pg from "pg";

const { Client } = pg;

const migrationsDir =
  process.env.PRISMA_MIGRATIONS_DIR || "/data/packages/prisma/migrations";
const databaseUrl = process.env.DATABASE_URL;
const connectRetries = Number(process.env.MIGRATION_CONNECT_RETRIES || 60);
const lockWaitMs = Number(process.env.MIGRATION_LOCK_TIMEOUT_MS || 120000);

if (!databaseUrl) {
  console.error("[migrate] DATABASE_URL is required");
  process.exit(1);
}

if (!existsSync(migrationsDir) || !statSync(migrationsDir).isDirectory()) {
  console.error(`[migrate] migrations directory not found: ${migrationsDir}`);
  process.exit(1);
}

const sha256 = (buf) => createHash("sha256").update(buf).digest("hex");
const log = (...args) => console.log("[migrate]", ...args);

function migrationFolders() {
  return readdirSync(migrationsDir)
    .filter((name) => {
      const full = path.join(migrationsDir, name);
      return (
        statSync(full).isDirectory() &&
        existsSync(path.join(full, "migration.sql"))
      );
    })
    .sort();
}

const CREATE_TABLE = `
CREATE TABLE IF NOT EXISTS "_prisma_migrations" (
    "id" VARCHAR(36) PRIMARY KEY NOT NULL,
    "checksum" VARCHAR(64) NOT NULL,
    "finished_at" TIMESTAMPTZ,
    "migration_name" VARCHAR(255) NOT NULL,
    "logs" TEXT,
    "rolled_back_at" TIMESTAMPTZ,
    "started_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "applied_steps_count" INTEGER NOT NULL DEFAULT 0
)`;

async function connect() {
  let lastError;
  for (let attempt = 1; attempt <= connectRetries; attempt++) {
    const client = new Client({ connectionString: databaseUrl });
    try {
      await client.connect();
      return client;
    } catch (error) {
      lastError = error;
      await client.end().catch(() => {});
      log(`database not ready (attempt ${attempt}/${connectRetries}): ${error.message}`);
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }
  throw lastError;
}

async function main() {
  const folders = migrationFolders();
  if (folders.length === 0) {
    throw new Error(`no migrations found in ${migrationsDir}`);
  }
  log(`found ${folders.length} migration folders in ${migrationsDir}`);

  const client = await connect();
  await client.query(CREATE_TABLE);

  // Same idea as Prisma's schema-engine: serialize concurrent deployments.
  // 72707369 is an arbitrary application-specific lock key.
  await client.query(
    `SET lock_timeout = '${Math.max(1000, Math.floor(lockWaitMs))}ms'`,
  );
  await client.query("SELECT pg_advisory_lock(72707369)");

  let appliedNow = 0;
  let alreadyApplied = 0;

  try {
    for (const name of folders) {
      const file = path.join(migrationsDir, name, "migration.sql");
      const contents = readFileSync(file);
      const checksum = sha256(contents);

      const existing = await client.query(
        `SELECT id, checksum, finished_at, rolled_back_at
           FROM "_prisma_migrations"
          WHERE migration_name = $1`,
        [name],
      );

      if (existing.rowCount > 0) {
        const row = existing.rows[0];
        if (row.finished_at) {
          if (row.checksum !== checksum) {
            throw new Error(
              `migration ${name} was already applied with a different checksum ` +
                `(db=${row.checksum} file=${checksum})`,
            );
          }
          alreadyApplied++;
          continue;
        }
        // A row without finished_at means an interrupted/failed attempt.
        // Every migration below runs in its own transaction, so nothing from
        // that attempt survived; drop the bookkeeping row and retry.
        log(`retrying unfinished migration ${name}`);
        await client.query(`DELETE FROM "_prisma_migrations" WHERE id = $1`, [
          row.id,
        ]);
      }

      const id = randomUUID();
      await client.query(
        `INSERT INTO "_prisma_migrations"
           (id, checksum, migration_name, started_at, applied_steps_count)
         VALUES ($1, $2, $3, now(), 0)`,
        [id, checksum, name],
      );

      log(`applying ${name}`);
      try {
        await client.query("BEGIN");
        await client.query(contents.toString("utf8"));
        await client.query(
          `UPDATE "_prisma_migrations"
              SET finished_at = now(), applied_steps_count = 1
            WHERE id = $1`,
          [id],
        );
        await client.query("COMMIT");
        appliedNow++;
      } catch (error) {
        await client.query("ROLLBACK").catch(() => {});
        await client.query(
          `UPDATE "_prisma_migrations" SET logs = $2 WHERE id = $1`,
          [id, String(error.stack || error.message)],
        );
        throw new Error(`migration ${name} failed: ${error.message}`);
      }
    }

    const count = await client.query(
      `SELECT count(*)::int AS n FROM "_prisma_migrations" WHERE finished_at IS NOT NULL`,
    );
    log(
      `MIGRATIONS_OK applied_now=${appliedNow} already=${alreadyApplied} ` +
        `recorded=${count.rows[0].n} folders=${folders.length}`,
    );
    if (count.rows[0].n !== folders.length) {
      throw new Error(
        `recorded migrations (${count.rows[0].n}) != folders (${folders.length})`,
      );
    }
  } finally {
    await client.query("SELECT pg_advisory_unlock(72707369)").catch(() => {});
    await client.end().catch(() => {});
  }
}

main().catch((error) => {
  console.error("[migrate] FAILED:", error.message);
  process.exit(1);
});
