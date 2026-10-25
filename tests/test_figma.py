import asyncio
import json
import httpx
import pytest
from app.figma_client import FigmaClient, FigmaError, extract_file_key

KEY = 'AbCdEf123456'

def test_extract_key():
    assert extract_file_key(f'https://www.figma.com/design/{KEY}/Example') == KEY
    assert extract_file_key(KEY) == KEY
    with pytest.raises(FigmaError):
        extract_file_key('bad')

def test_two_real_endpoint_contracts():
    calls = []
    def handler(request):
        calls.append((request.url.path, dict(request.url.params)))
        assert request.headers['X-Figma-Token'] == 'test-token'
        if request.url.path == f'/v1/files/{KEY}':
            return httpx.Response(200, json={'name':'Demo','document':{'children':[{'id':'1:2','name':'Page 1'}]}})
        if request.url.path == f'/v1/files/{KEY}/nodes':
            return httpx.Response(200, json={'nodes':{'1:2':{'document':{'name':'Page 1','type':'CANVAS'}}}})
        return httpx.Response(404, json={'err':'Not found'})
    async def exercise():
        client = FigmaClient(token='test-token', transport=httpx.MockTransport(handler))
        assert (await client.get_file(KEY))['name'] == 'Demo'
        assert '1:2' in (await client.get_nodes(KEY, ['1:2']))['nodes']
    asyncio.run(exercise())
    assert calls == [(f'/v1/files/{KEY}', {'depth':'2'}), (f'/v1/files/{KEY}/nodes', {'ids':'1:2'})]

def test_reject_invalid_nodes():
    async def exercise():
        with pytest.raises(FigmaError):
            await FigmaClient(token='test-token').get_nodes(KEY, ['invalid'])
    asyncio.run(exercise())
