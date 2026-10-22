const dns = require('node:dns');
const express = require('express');
const cors = require('cors');
const { Noco } = require('./dist/bundle.js');

dns.setDefaultResultOrder('ipv4first');

const server = express();
server.enable('trust proxy');
server.use(cors());
server.set('view engine', 'ejs');

(async () => {
  const httpServer = server.listen(process.env.PORT || 8080, async () => {
    server.use(await Noco.init({}, httpServer, server));
  });
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
