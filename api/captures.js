import { Redis } from '@upstash/redis';

function getRedis() {
  const url = process.env.UPSTASH_REDIS_REST_URL || process.env.KV_REST_API_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN || process.env.KV_REST_API_TOKEN;
  if (!url || !token) return null;
  return new Redis({ url, token });
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'GET only' });

  if (req.query.key !== '2262') {
    return res.status(401).json({ error: 'unauthorized' });
  }

  try {
    const kv = getRedis();
    if (!kv) {
      return res.status(500).json({
        error: 'Redis not configured',
        detail: 'Missing UPSTASH_REDIS_REST_URL or KV_REST_API_URL env vars'
      });
    }

    // Fetch all capture IDs (stored in a set)
    const ids = await kv.smembers('capture_ids');
    const captures = [];

    if (ids && Array.isArray(ids)) {
      for (const id of ids) {
        try {
          const data = await kv.get(`capture:${id}`);
          if (data) captures.push(typeof data === 'string' ? JSON.parse(data) : data);
        } catch (e) {
          // skip bad entries
        }
      }
    }

    captures.reverse(); // newest first
    return res.status(200).json({ total: captures.length, captures });
  } catch (err) {
    console.error('[LIST ERROR]', err.message || err);
    return res.status(500).json({ error: 'server error', detail: String(err.message || err) });
  }
}
