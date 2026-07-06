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

  const key = req.body?.key;
  if (key !== '2262') return res.status(401).json({ error: 'unauthorized' });

  try {
    const kv = getRedis();
    if (!kv) return res.status(500).json({ error: 'Redis not configured' });

    const ids = await kv.smembers('capture_ids');
    if (ids && Array.isArray(ids)) {
      for (const id of ids) {
        await kv.del(`capture:${id}`);
      }
    }
    await kv.del('capture_ids');

    return res.status(200).json({ status: 'cleared' });
  } catch (err) {
    console.error('[CLEAR ERROR]', err.message || err);
    return res.status(500).json({ error: 'server error', detail: String(err.message || err) });
  }
}
