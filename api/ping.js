import { Redis } from '@upstash/redis';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');

  const url = process.env.UPSTASH_REDIS_REST_URL || process.env.KV_REST_API_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN || process.env.KV_REST_API_TOKEN;

  const result = {
    hasUrl: !!url,
    hasToken: !!token,
    urlPrefix: url ? url.substring(0, 20) + '...' : 'missing',
  };

  if (url && token) {
    try {
      const kv = new Redis({ url, token });
      const pong = await kv.ping();
      result.ping = pong;
      result.status = 'connected';
    } catch (err) {
      result.status = 'error';
      result.error = String(err.message || err);
    }
  } else {
    result.status = 'missing env vars';
  }

  return res.status(200).json(result);
}
