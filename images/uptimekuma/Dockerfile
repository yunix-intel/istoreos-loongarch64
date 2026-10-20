# uptime-kuma 2.5.6 loong64 镜像 / openEuler 24.03 底包
# 选型说明: FROM 本地 openeuler 底包 + dnf 装 nodejs(20.18.2, 满足 engines>=20.4.0)。
# 未采用拷宿主机 node 二进制: 宿主是 Loongnix, 与 openEuler 用户态(glibc/libstdc++)版本不同,
# 拷二进制有缺库/ABI 风险; 源里是官方 loong64 包, 最干净。
# 与官方 Dockerfile 的差异(有意裁剪): 去 dumb-init(openEuler 源无此包, node 直跑 PID1);
# 去 healthcheck 二进制(需 go 交叉编译, 官方靠预编多架构镜像才有, loong64 无);
# 去 apprise/chromium/mariadb(通知推送/截图/外置库等附加功能, 核心站点监控不需要)。

FROM openeuler/openeuler:24.03 AS build
RUN dnf install -y nodejs npm gcc gcc-c++ make python3 && dnf clean all && node --version && npm --version
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build && npm prune --omit=dev && mkdir -p ./data

FROM openeuler/openeuler:24.03 AS release
RUN dnf install -y nodejs && dnf clean all && node --version
WORKDIR /app
ENV UPTIME_KUMA_IS_CONTAINER=1 NODE_ENV=production
COPY --from=build /app /app
EXPOSE 3001
VOLUME /app/data
# openEuler 源 node 停在 20.18.2, require(ESM) 需此 flag(20.19+ 才默认开); 源有 node>=20.19 后可删此 flag。
CMD ["node", "--experimental-require-module", "server/server.js"]
