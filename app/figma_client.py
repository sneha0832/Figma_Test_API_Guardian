"""Real Figma REST API client. Two independent requests: file and file nodes."""
import os
import re
import httpx
from dotenv import load_dotenv

load_dotenv()
BASE_URL = 'https://api.figma.com/v1'
FILE_KEY_PATTERN = re.compile(r'^[A-Za-z0-9_-]{8,}$')

class FigmaError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code

def extract_file_key(value: str) -> str:
    """Accept either a Figma file key or an ordinary design file URL."""
    value = value.strip()
    match = re.search(r'figma\.com/(?:file|design)/([A-Za-z0-9_-]+)', value)
    key = match.group(1) if match else value
    if not FILE_KEY_PATTERN.fullmatch(key):
        raise FigmaError('Enter a valid Figma design URL or file key.', 400)
    return key

class FigmaClient:
    def __init__(self, transport=None, token=None):
        self.token = token if token is not None else os.getenv('FIGMA_TOKEN', '').strip()
        self.transport = transport

    async def request(self, path: str, params=None):
        if not self.token or self.token.startswith('replace_with_'):
            raise FigmaError('Set FIGMA_TOKEN in your .env file.', 503)
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=25, transport=self.transport) as client:
            try:
                response = await client.get(path, params=params, headers={'X-Figma-Token': self.token})
            except httpx.RequestError:
                raise FigmaError('Could not reach Figma API.') from None
        if response.status_code >= 400:
            # Avoid leaking tokens or raw request internals.
            try:
                detail = response.json().get('err') or response.json().get('message')
            except ValueError:
                detail = None
            raise FigmaError(f'Figma API HTTP {response.status_code}: {str(detail)[:250] if detail else "Request failed"}', response.status_code)
        return response.json()

    async def get_file(self, key):
        # REQUEST 1: GET /v1/files/{file_key}
        return await self.request(f'/files/{extract_file_key(key)}', {'depth': 2})

    async def get_nodes(self, key, node_ids):
        # REQUEST 2: GET /v1/files/{file_key}/nodes?ids=...
        if not node_ids or len(node_ids) > 10 or any(not re.fullmatch(r'[0-9]+:[0-9]+', node) for node in node_ids):
            raise FigmaError('Provide 1-10 valid Figma node IDs (e.g. 1:2).', 400)
        return await self.request(f'/files/{extract_file_key(key)}/nodes', {'ids': ','.join(node_ids)})
