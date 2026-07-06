import { Redis } from '@upstash/redis';

const kv = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL || process.env.KV_REST_API_URL || '',
  token: process.env.UPSTASH_REDIS_REST_TOKEN || process.env.KV_REST_API_TOKEN || ''
});

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'GET only' });

  const key = req.query.key;
  const expected = process.env.ADMIN_KEY;
  if (!key || key !== expected) {
    return res.status(401).json({ error: 'unauthorized' });
  }

  try {
    const raw = await kv.lrange('captures', 0, -1);
    const data = raw.map(r => JSON.parse(r));
    return res.status(200).json({ total: data.length, captures: data });
  } catch (err) {
    console.error('[LIST ERROR]', err.message || err);
    return res.status(500).json({ error: 'server error', detail: err.message });
  }
}
