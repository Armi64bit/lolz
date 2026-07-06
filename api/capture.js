import { Redis } from '@upstash/redis';

function getRedis() {
  const url = process.env.UPSTASH_REDIS_REST_URL || process.env.KV_REST_API_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN || process.env.KV_REST_API_TOKEN;
  if (!url || !token) return null;
  return new Redis({ url, token });
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  try {
    const kv = getRedis();
    if (!kv) {
      return res.status(500).json({
        error: 'Redis not configured',
        detail: 'Missing UPSTASH_REDIS_REST_URL or KV_REST_API_URL env vars'
      });
    }

    const clientData = req.body;
    const ip = req.headers['x-forwarded-for']?.split(',')[0]?.trim()
      || req.headers['x-real-ip']
      || req.socket?.remoteAddress
      || 'unknown';
    const userAgent = req.headers['user-agent'] || 'unknown';

    const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    const record = { id, ip, userAgent, receivedAt: new Date().toISOString(), ...clientData };

    // Store individual capture record
    await kv.set(`capture:${id}`, JSON.stringify(record));
    // Track ID in a set
    await kv.sadd('capture_ids', id);
    // Trim: keep only last 500 IDs
    const allIds = await kv.smembers('capture_ids');
    if (allIds && Array.isArray(allIds) && allIds.length > 500) {
      const toRemove = allIds.slice(0, allIds.length - 500);
      for (const oldId of toRemove) {
        await kv.del(`capture:${oldId}`);
        await kv.srem('capture_ids', oldId);
      }
    }

    console.log(`[CAPTURE] ${id} - IP: ${ip}`);
    return res.status(200).json({ status: 'ok', id });
  } catch (err) {
    console.error('[CAPTURE ERROR]', err.message || err);
    return res.status(500).json({ error: 'server error', detail: String(err.message || err) });
  }
}
