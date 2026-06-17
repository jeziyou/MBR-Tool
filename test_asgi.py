# 最小化测试：直接添加 Starlette Route，看是否能工作
import subprocess, time, sys, os
sys.path.insert(0, '/workspace')

# 先测试最简单的 Starlette 路由注入
import asyncio
from starlette.applications import Starlette
from starlette.routing import Route, Mount, Match, get_route_path
from starlette.responses import JSONResponse
import re
import io

# Flask app
from flask import Flask, request, jsonify
test_flask = Flask(__name__)

@test_flask.route("/api/test", methods=["POST"])
def test_api():
    return jsonify({"success": True, "method": request.method})

# ASGI wrapper for Flask
async def flask_asgi(scope, receive, send):
    environ = {
        'REQUEST_METHOD': scope.get('method', 'GET'),
        'SCRIPT_NAME': '',
        'PATH_INFO': scope.get('path', '/'),
        'QUERY_STRING': scope.get('query_string', b'').decode(),
        'SERVER_NAME': scope.get('server', ('localhost', 80))[0],
        'SERVER_PORT': str(scope.get('server', ('localhost', 80))[1]),
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': scope.get('scheme', 'http'),
        'wsgi.input': io.BytesIO(b''),
        'wsgi.errors': None,
        'wsgi.multithread': True,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '0',
    }
    headers = {}
    for k, v in scope.get('headers', []):
        kn = (k.decode() if isinstance(k, bytes) else k).upper().replace('-', '_')
        kv = v.decode() if isinstance(v, bytes) else v
        environ[f'HTTP_{kn}'] = kv
        headers[kn.lower()] = kv
    
    body = b''
    if environ['REQUEST_METHOD'] in ('POST', 'PUT'):
        while True:
            msg = await receive()
            if msg['type'] == 'http.request':
                body += msg.get('body', b'')
                if not msg.get('more_body', False):
                    break
    environ['wsgi.input'] = io.BytesIO(body)
    environ['CONTENT_LENGTH'] = str(len(body))

    resp_started = []
    def start_resp(status, headers, exc=None):
        resp_started.append({'status': int(status.split()[0]), 'headers': headers})
    result = test_flask(environ, start_resp)
    info = resp_started[0]
    asgi_hdrs = [(h.encode() if isinstance(h, str) else h, v.encode() if isinstance(v, str) else v) for h, v in info['headers']]
    await send({'type': 'http.response.start', 'status': info['status'], 'headers': asgi_hdrs})
    for chunk in result:
        await send({'type': 'http.response.body', 'body': chunk if isinstance(chunk, bytes) else chunk.encode()})

# 简单 Starlette route test
async def simple_health(scope, receive, send):
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'application/json')]})
    await send({'type': 'http.response.body', 'body': b'{"simple":true}'})

# Test app
test_app = Starlette(routes=[
    Route('/api/simple', simple_health),
    Mount('/api', app=flask_asgi),
])

# ASGI call simulation
scope = {'type': 'http', 'method': 'GET', 'path': '/api/simple', 'query_string': b'', 
         'headers': [], 'root_path': '', 'server': ('localhost', 8000), 'scheme': 'http'}

async def fake_receive():
    return {'type': 'http.request', 'body': b'', 'more_body': False}

messages = []
async def fake_send(msg):
    messages.append(msg)

print("Testing /api/simple...")
asyncio.run(test_app(scope, fake_receive, fake_send))
print("Messages:", messages)

# Test POST to Flask
scope2 = {'type': 'http', 'method': 'POST', 'path': '/api/test', 'query_string': b'',
          'headers': [(b'content-type', b'application/json')],
          'root_path': '', 'server': ('localhost', 8000), 'scheme': 'http'}

messages2 = []
asyncio.run(test_app(scope2, fake_receive, fake_send))
print("\nMessages for POST /api/test:", messages2)
