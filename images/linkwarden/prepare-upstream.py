#!/usr/bin/env python3
"""Apply Linkwarden loong64 source changes to a v2.16.3 checkout.

Run from anywhere:  python3 -I prepare-upstream.py /path/to/linkwarden
The checkout must be linkwarden/linkwarden at commit 952ac454 (v2.16.3+1).
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()


def read(p):
    return (ROOT / p).read_text()


def write(p, s):
    (ROOT / p).write_text(s)


def edit_json(p, fn):
    data = json.loads(read(p))
    fn(data)
    write(p, json.dumps(data, indent=2) + "\n")


# --- apps/web/package.json: drop sharp + bcrypt native -----------------------
def web(d):
    deps = d["dependencies"]
    deps.pop("sharp", None)
    deps.pop("bcrypt", None)
    deps["bcryptjs"] = "^3.0.3"
    d["devDependencies"].pop("@types/bcrypt", None)
    # The build host is Ubuntu 26.04, which Playwright 1.57 refuses. No browser
    # is downloaded anyway; LBrowser is a runtime sidecar.
    d.get("scripts", {}).pop("postinstall", None)


edit_json("apps/web/package.json", web)


# --- root postinstall: do not depend on the removed web playwright hook ------
def root_pkg(d):
    d.setdefault("scripts", {})["postinstall"] = "patch-package"


edit_json("package.json", root_pkg)


# --- packages/prisma/package.json: Prisma 7 + pg driver adapter --------------
def prisma_pkg(d):
    d["dependencies"] = {
        "@prisma/adapter-pg": "7.10.1",
        "@prisma/client": "7.10.1",
        "pg": "8.23.1",
    }
    d.setdefault("devDependencies", {})
    d["devDependencies"]["prisma"] = "7.10.1"


edit_json("packages/prisma/package.json", prisma_pkg)


# --- schema.prisma: v7 moved the URL to prisma.config.ts ---------------------
schema = read("packages/prisma/schema.prisma")
schema = re.sub(r'\n\s*url\s*=\s*env\("DATABASE_URL"\)', "", schema, count=1)
write("packages/prisma/schema.prisma", schema)

write(
    "packages/prisma/prisma.config.ts",
    '''import { defineConfig, env } from "prisma/config";

export default defineConfig({
  schema: "schema.prisma",
  migrations: {
    path: "migrations",
  },
  datasource: {
    url: env("DATABASE_URL"),
  },
});
''',
)

# --- packages/prisma/index.ts: driver adapter is mandatory in v7 --------------
write(
    "packages/prisma/index.ts",
    '''import { PrismaClient } from "@prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";

const globalForPrisma = global as unknown as { prisma: PrismaClient };

const adapter = new PrismaPg({
  connectionString: process.env.DATABASE_URL,
});

export const prisma =
  globalForPrisma.prisma ||
  new PrismaClient({
    adapter,
    log:
      process.env.DEBUG === "true"
        ? ["query", "info", "warn", "error"]
        : ["warn", "error"],
  });

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;
''',
)

# --- bcrypt -> bcryptjs (same sync/async API, compatible hashes) --------------
for rel in [
    "apps/web/lib/api/verifyByCredentials.ts",
    "apps/web/lib/api/controllers/users/userId/updateUserById.ts",
    "apps/web/lib/api/controllers/users/userId/deleteUserById.ts",
    "apps/web/lib/api/controllers/users/postUser.ts",
    "apps/web/pages/api/v1/auth/[...nextauth].ts",
    "apps/web/pages/api/v1/auth/reset-password.ts",
]:
    text = read(rel)
    new = text.replace('from "bcrypt"', 'from "bcryptjs"')
    if new == text and 'from "bcryptjs"' not in text:
        raise SystemExit(f"bcrypt import not found in {rel}")
    write(rel, new)

# --- next.config.js: no sharp, raw images, keep Prisma external --------------
nextconfig = read("apps/web/next.config.js")
nextconfig = nextconfig.replace(
    """  images: {
    remotePatterns: [""",
    """  images: {
    unoptimized: true,
    remotePatterns: [""",
)
if "serverExternalPackages" not in nextconfig:
    nextconfig = nextconfig.replace(
        """  transpilePackages: ["@linkwarden/prisma"],""",
        """  transpilePackages: ["@linkwarden/prisma"],
  serverExternalPackages: ["@prisma/client", "@prisma/adapter-pg", "pg"],""",
    )
write("apps/web/next.config.js", nextconfig)

# --- the one direct PrismaClient bypassing the shared adapter ----------------
batch_path = "apps/worker/lib/getLinkBatch.ts"
batch = read(batch_path)
if 'import { PrismaClient, Prisma } from "@linkwarden/prisma/client";' in batch:
    batch = batch.replace(
        'import { PrismaClient, Prisma } from "@linkwarden/prisma/client";\n\nconst prisma = new PrismaClient();',
        'import { Prisma } from "@linkwarden/prisma/client";\nimport { prisma } from "@linkwarden/prisma";',
    )
    write(batch_path, batch)

# --- worker: DISABLE_BROWSER must not try to launch a browser ----------------
lp_path = "apps/worker/workers/linkProcessing.ts"
lp = read(lp_path)
if "BROWSE_DISABLED" not in lp:
    lp = lp.replace(
        '''const BROWSER_IDLE_TIMEOUT_MS = 60_000;''',
        '''const BROWSER_IDLE_TIMEOUT_MS = 60_000;
// archiveHandler skips all preservation when this is set, but the loop still
// needs to drain links. Keep the web process usable without any browser.
const BROWSE_DISABLED =
  (process.env.DISABLE_BROWSER || process.env.DISABLE_PRESERVATION) === "true";''',
    )
lp = lp.replace(
    """async function linkProcessingPersistent(interval: number) {
  let browser = await launchBrowser();""",
    """async function linkProcessingPersistent(interval: number) {
  let browser = BROWSE_DISABLED
    ? (null as unknown as Browser)
    : await launchBrowser();""",
)
lp = lp.replace(
    """    if (Date.now() - browserStartTs >= BROWSER_MAX_AGE_MS) {
      await restartBrowser("30-minute rotation");""",
    """    if (!BROWSE_DISABLED && Date.now() - browserStartTs >= BROWSER_MAX_AGE_MS) {
      await restartBrowser("30-minute rotation");""",
)
lp = lp.replace(
    """    const activeBrowser = await ensureBrowser();""",
    """    const activeBrowser = BROWSE_DISABLED
      ? (null as unknown as Browser)
      : await ensureBrowser();""",
)
write(lp_path, lp)

print("patched", ROOT)
