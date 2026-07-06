import { Redis } from '@upstash/redis';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'GET only' });

  const key = req.query.key;
  if (key !== '2262') {
    return res.status(401).json({ error: 'unauthorized' });
  }

  try {
    const url = process.env.UPSTASH_REDIS_REST_URL || process.env.KV_REST_API_URL;
    const token = process.env.UPSTASH_REDIS_REST_TOKEN || process.env.KV_REST_API_TOKEN;
    if (!url || !token) {
      return res.status(500).json({ error: 'Redis not configured', detail: 'Missing UPSTASH_REDIS_REST_URL or token env vars' });
    }
    const kv = new Redis({ url, token });
    const raw = await kv.lrange('captures', 0, -1);
    const data = raw.map(r => JSON.parse(r));
    return res.status(200).json({ total: data.length, captures: data });
  } catch (err) {
    console.error('[LIST ERROR]', err.message || err);
    return res.status(500).json({ error: 'server error', detail: err.message });
  }
}
