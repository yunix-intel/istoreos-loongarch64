// Small CDP reverse proxy for LBrowser.
//
// LBrowser 3.4.2293.2 always binds its DevTools HTTP/WebSocket endpoint to
// 127.0.0.1, even when --remote-debugging-address=0.0.0.0 is passed.  This
// proxy listens on 0.0.0.0:9222, forwards to 127.0.0.1:9223, and rewrites the
// host:port inside /json/version and /json/list so Playwright/Patchright can
// connect from another container.
import http from 'node:http';
import net from 'node:net';

const listenHost = process.env.CDP_LISTEN_HOST || '0.0.0.0';
const listenPort = Number(process.env.CDP_LISTEN_PORT || 9222);
const upstreamHost = process.env.CDP_UPSTREAM_HOST || '127.0.0.1';
const upstreamPort = Number(process.env.CDP_UPSTREAM_PORT || 9223);
const upstreamAuthority = `${upstreamHost}:${upstreamPort}`;

function rewriteBody(body, externalAuthority) {
  return body
    .replaceAll(`ws://${upstreamAuthority}`, `ws://${externalAuthority}`)
    .replaceAll(`http://${upstreamAuthority}`, `http://${externalAuthority}`);
}

const server = http.createServer((req, res) => {
  const headers = { ...req.headers, host: upstreamAuthority };
  const upstream = http.request(
    { host: upstreamHost, port: upstreamPort, path: req.url, method: req.method, headers },
    (upstreamRes) => {
      const isJson = String(upstreamRes.headers['content-type'] || '').includes('application/json');
      if (!isJson) {
        res.writeHead(upstreamRes.statusCode || 502, upstreamRes.headers);
        upstreamRes.pipe(res);
        return;
      }

      const chunks = [];
      upstreamRes.on('data', (chunk) => chunks.push(chunk));
      upstreamRes.on('end', () => {
        const externalAuthority = req.headers.host || `${listenHost}:${listenPort}`;
        const body = rewriteBody(Buffer.concat(chunks).toString('utf8'), externalAuthority);
        const outHeaders = { ...upstreamRes.headers };
        delete outHeaders['content-length'];
        delete outHeaders['transfer-encoding'];
        outHeaders['content-length'] = Buffer.byteLength(body);
        res.writeHead(upstreamRes.statusCode || 502, outHeaders);
        res.end(body);
      });
    },
  );

  upstream.on('error', (err) => {
    res.writeHead(502, { 'content-type': 'text/plain' });
    res.end(`CDP upstream error: ${err.message}\n`);
  });
  req.pipe(upstream);
});

server.on('upgrade', (req, clientSocket, head) => {
  const upstream = net.connect(upstreamPort, upstreamHost, () => {
    const headers = { ...req.headers, host: upstreamAuthority };
    let raw = `${req.method} ${req.url} HTTP/${req.httpVersion}\r\n`;
    for (const [name, value] of Object.entries(headers)) {
      if (Array.isArray(value)) {
        for (const item of value) raw += `${name}: ${item}\r\n`;
      } else if (value !== undefined) {
        raw += `${name}: ${value}\r\n`;
      }
    }
    raw += '\r\n';
    upstream.write(raw);
    if (head?.length) upstream.write(head);
    clientSocket.pipe(upstream);
    upstream.pipe(clientSocket);
  });

  upstream.on('error', () => clientSocket.destroy());
  clientSocket.on('error', () => upstream.destroy());
});

server.on('clientError', (_err, socket) => {
  if (socket.writable) socket.end('HTTP/1.1 400 Bad Request\r\n\r\n');
});

server.listen(listenPort, listenHost, () => {
  console.log(`CDP proxy listening on ${listenHost}:${listenPort} -> ${upstreamAuthority}`);
});
