export const name = 'closure-ethics-http-subject';
export const version = '0.1';

export async function run(input, context) {
  const url = process.env.CE_SUBJECT_URL;
  if (!url) throw new Error('CE_SUBJECT_URL is required');

  const headers = { 'content-type': 'application/json' };
  const token = process.env.CE_SUBJECT_BEARER_TOKEN;
  if (token) headers.authorization = `Bearer ${token}`;

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(input),
    signal: context.signal,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`subject endpoint ${response.status}: ${text.slice(0, 500)}`);
  }
  const data = await response.json();
  return data;
}
