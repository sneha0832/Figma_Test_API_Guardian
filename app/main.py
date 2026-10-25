"""Figma Design Audit: standalone FastAPI backend for API Guardian tests."""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from app.figma_client import FigmaClient, FigmaError

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title='Figma Design Audit - API Guardian Test')
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')

class FileRequest(BaseModel):
    file: str = Field(min_length=8)

class NodeRequest(FileRequest):
    node_ids: list[str] = Field(min_length=1, max_length=10)

@app.get('/')
def home():
    return FileResponse(ROOT / 'static' / 'index.html')

@app.get('/api/health')
def health():
    return {'status': 'ok'}

@app.post('/api/figma/file')
async def file_details(body: FileRequest):
    try:
        data = await FigmaClient().get_file(body.file)
        pages = data.get('document', {}).get('children', [])
        return {'name': data.get('name'), 'last_modified': data.get('lastModified'), 'version': data.get('version'), 'pages': [{'id': p.get('id'), 'name': p.get('name'), 'type': p.get('type')} for p in pages], 'raw_endpoint': 'GET /v1/files/{file_key}'}
    except FigmaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

@app.post('/api/figma/nodes')
async def node_details(body: NodeRequest):
    try:
        data = await FigmaClient().get_nodes(body.file, body.node_ids)
        nodes = []
        for node_id, item in (data.get('nodes') or {}).items():
            doc = (item or {}).get('document') or {}
            nodes.append({'id': node_id, 'name': doc.get('name'), 'type': doc.get('type'), 'visible': doc.get('visible', True), 'children_count': len(doc.get('children') or [])})
        return {'nodes': nodes, 'raw_endpoint': 'GET /v1/files/{file_key}/nodes'}
    except FigmaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
