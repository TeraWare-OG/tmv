const http = require('http');
const crypto = require('crypto');
const { execSync } = require('child_process');

const PORT = 9000;
const SECRET = process.env.WEBHOOK_SECRET || 'changeme';

function verifySignature(payload, signature) {
  if (!signature) return false;
  const hmac = crypto.createHmac('sha256', SECRET);
  hmac.update(payload);
  const expected = 'sha256=' + hmac.digest('hex');
  try {
    return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
  } catch {
    return false;
  }
}

const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok' }));
    return;
  }
  if (req.method !== 'POST' || req.url !== '/webhook') {
    res.writeHead(404);
    res.end('Not Found');
    return;
  }

  let body = '';
  req.on('data', (c) => (body += c));
  req.on('end', () => {
    if (!verifySignature(body, req.headers['x-hub-signature-256'])) {
      console.log(`[${new Date().toISOString()}] Ungültige Signatur`);
      res.writeHead(401);
      res.end('Unauthorized');
      return;
    }
    let payload;
    try { payload = JSON.parse(body); } catch { res.writeHead(400); res.end('Bad Request'); return; }

    if (payload.ref !== 'refs/heads/main') {
      res.writeHead(200);
      res.end('Ignored: not main branch');
      return;
    }

    console.log(`[${new Date().toISOString()}] Deploy gestartet...`);
    res.writeHead(200);
    res.end('Deploy gestartet');

    try {
      execSync('sh /app/deploy/deploy.sh', { cwd: '/app', stdio: 'inherit', timeout: 300000 });
      console.log(`[${new Date().toISOString()}] Deploy erfolgreich`);
    } catch (err) {
      console.error(`[${new Date().toISOString()}] Deploy fehlgeschlagen:`, err.message);
    }
  });
});

server.listen(PORT, () => console.log(`Webhook-Server läuft auf Port ${PORT}`));
