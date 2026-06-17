import asyncio, io
from starlette.applications import Starlette
from starlette.routing import Route, Mount, Match, get_route_path
from starlette.responses import JSONResponse
import re

# Test: Mount with custom ASGI app
class TestMount:
    def __init__(self, path):
        self.path = path.rstrip('/')
        self.path_regex = re.compile(f'^(?P<prefix>{re.escape(self.path)})(?P<suffix>.*)$')

    async def __call__(self, scope, receive, send):
        print(f"  [TestMount.__call__] path={scope.get('path')}, prefix={self.path}")
        await send({'type': 'http.response.start', 'status': 200,
                    'headers': [(b'content-type', b'text/plain')]})
        await send({'type': 'http.response.body',
                    'body': f'Mount matched! path={scope.get("path")}'.encode()})

    def matches(self, scope):
        if scope['type'] in ('http', 'websocket'):
            route_path = get_route_path(scope)
            print(f"  [TestMount.matches] route_path={route_path}")
            m = self.path_regex.match(route_path)
            print(f"  [TestMount.matches] match result: {m}")
            if m:
                child_scope = dict(scope)
                child_scope['root_path'] = scope.get('root_path', '') + self.path
                child_scope['path'] = scope.get('path', '')
                child_scope['endpoint'] = self
                return Match.FULL, child_scope
        return Match.NONE, {}

async def simple_health(scope, receive, send):
    print(f"[simple_health] called with path={scope.get('path')}")
    await send({'type': 'http.response.start', 'status': 200,
                'headers': [(b'content-type', b'application/json')]})
    await send({'type': 'http.response.body', 'body': b'{"simple":true}'})

test_app = Starlette(routes=[
    Route('/api/simple', simple_health),
    Mount('/api', app=TestMount('/api')),
])

async def fake_receive():
    return {'type': 'http.request', 'body': b'', 'more_body': False}

messages = []
async def fake_send(msg):
    messages.append(msg)

# Test 1: /api/simple
print("=== Test 1: GET /api/simple ===")
scope = {'type': 'http', 'method': 'GET', 'path': '/api/simple', 'query_string': b'',
         'headers': [], 'root_path': '', 'server': ('localhost', 8000), 'scheme': 'http'}
messages = []
asyncio.run(test_app(scope, fake_receive, fake_send))
print("Messages:", messages)
print()
