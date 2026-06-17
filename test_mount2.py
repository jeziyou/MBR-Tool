import asyncio, io
from starlette.applications import Starlette
from starlette.routing import Route, Mount, Match, get_route_path
import re

# Test: ASGI app as Route endpoint
async def simple_health(scope, receive, send):
    print(f"  [simple_health] called, path={scope.get('path')}")
    await send({'type': 'http.response.start', 'status': 200,
                'headers': [(b'content-type', b'application/json')]})
    await send({'type': 'http.response.body', 'body': b'{"simple":true}'})

# Route with ASGI app endpoint
simple_route = Route('/api/simple', simple_health)  # Will this work?

# Mount with ASGI app
class TestMount:
    def __init__(self, path, inner):
        self.path = path.rstrip('/')
        self.inner = inner
        self.path_regex = re.compile(f'^(?P<prefix>{re.escape(self.path)})(?P<suffix>.*)$')

    async def __call__(self, scope, receive, send):
        print(f"  [TestMount] called, path={scope.get('path')}")
        # After update, scope['path'] is the remaining part
        remaining = scope.get('path', '/')
        if remaining.startswith('/api/health'):
            await self.inner(scope, receive, send)
        else:
            await send({'type': 'http.response.start', 'status': 404,
                        'headers': [(b'content-type', b'text/plain')]})
            await send({'type': 'http.response.body', 'body': b'Not found'})

    def matches(self, scope):
        if scope['type'] in ('http', 'websocket'):
            route_path = get_route_path(scope)
            m = self.path_regex.match(route_path)
            if m:
                child_scope = dict(scope)
                child_scope['root_path'] = scope.get('root_path', '') + self.path
                child_scope['path'] = scope.get('path', '')  # Full path
                child_scope['endpoint'] = self
                return Match.FULL, child_scope
        return Match.NONE, {}

# Mount should intercept all /api/* paths
mount_app = TestMount('/api', simple_health)
test_app = Starlette(routes=[
    Route('/api/simple', simple_health),
    Mount('/api', app=mount_app),  # Using Mount with custom ASGI app
])

async def fake_receive():
    return {'type': 'http.request', 'body': b'', 'more_body': False}

messages = []
async def fake_send(msg):
    messages.append(msg)

# Test 1: GET /api/simple
print("=== Test 1: GET /api/simple ===")
scope = {'type': 'http', 'method': 'GET', 'path': '/api/simple', 'query_string': b'',
         'headers': [], 'root_path': '', 'server': ('localhost', 8000), 'scheme': 'http'}
messages = []
asyncio.run(test_app(scope, fake_receive, fake_send))
print("Result:", messages)
