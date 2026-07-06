import { kv } from '@vercel/kv';

export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  try {
    const clientData = req.body;
    const ip = req.headers['x-forwarded-for']?.split(',')[0]?.trim()
      || req.headers['x-real-ip']
      || req.socket?.remoteAddress
      || 'unknown';
    const userAgent = req.headers['user-agent'] || 'unknown';

    const record = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 8),
      ip,
      userAgent,
      receivedAt: new Date().toISOString(),
      ...clientData
    };

    // Store in KV (push to a list)
    const count = await kv.lpush('captures', JSON.stringify(record));
    // Trim list to last 500 entries
    await kv.ltrim('captures', 0, 499);

    console.log(`[CAPTURE] ${record.id} - IP: ${ip} - UA: ${userAgent.slice(0,60)}`);

    return res.status(200).json({ status: 'ok', id: record.id });
  } catch (err) {
    console.error('[CAPTURE ERROR]', err);
    return res.status(500).json({ error: 'server error' });
  }
}
