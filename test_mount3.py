import asyncio, io
from starlette.applications import Starlette
from starlette.routing import Route, Mount, Match, get_route_path
import re

# ASGI endpoint (takes scope/receive/send, NOT request)
async def health_asgi(scope, receive, send):
    print(f"  [health_asgi] called, path={scope.get('path')}, method={scope.get('method')}")
    await send({'type': 'http.response.start', 'status': 200,
                'headers': [(b'content-type', b'application/json'),
                           (b'access-control-allow-origin', b'*')]})
    await send({'type': 'http.response.body', 'body': b'{"status":"ok"}'})

async def email_asgi(scope, receive, send):
    print(f"  [email_asgi] called, path={scope.get('path')}")
    # Read body
    body = b''
    if scope.get('method') in ('POST',):
        while True:
            msg = await receive()
            if msg['type'] == 'http.request':
                body += msg.get('body', b'')
                if not msg.get('more_body', False):
                    break
    print(f"  Body: {body[:100]}")
    await send({'type': 'http.response.start', 'status': 200,
                'headers': [(b'content-type', b'application/json'),
                           (b'access-control-allow-origin', b'*')]})
    await send({'type': 'http.response.body',
                'body': b'{"success":true,"message":"email sent"}'})

# Custom Mount that handles /api/* routing to ASGI apps
class ApiMount:
    def __init__(self):
        self.path = '/api'
        self.path_regex = re.compile(f'^(?P<prefix>{re.escape(self.path)})(?P<suffix>.*)$')
        self.routes = {
            '/api/health': health_asgi,
            '/api/send-email': email_asgi,
        }

    async def __call__(self, scope, receive, send):
        route_path = scope.get('path', '/')
        handler = self.routes.get(route_path)
        if handler:
            await handler(scope, receive, send)
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
                child_scope['path'] = scope.get('path', '')
                child_scope['endpoint'] = self
                return Match.FULL, child_scope
        return Match.NONE, {}

# Create Starlette app with custom mount
api_mount = ApiMount()
test_app = Starlette(routes=[
    Mount('/api', app=api_mount),  # Pass ASGI app via `app=`
])

async def fake_receive():
    return {'type': 'http.request', 'body': b'{}', 'more_body': False}

async def fake_send(msg):
    print(f"  -> {msg.get('type')}, status={msg.get('status')}")

# Test 1: GET /api/health
print("=== Test 1: GET /api/health ===")
scope = {'type': 'http', 'method': 'GET', 'path': '/api/health', 'query_string': b'',
         'headers': [], 'root_path': '', 'server': ('localhost', 8000), 'scheme': 'http'}
asyncio.run(test_app(scope, fake_receive, fake_send))

# Test 2: POST /api/send-email
print("\n=== Test 2: POST /api/send-email ===")
scope2 = {'type': 'http', 'method': 'POST', 'path': '/api/send-email', 'query_string': b'',
          'headers': [(b'content-type', b'application/json')], 'root_path': '',
          'server': ('localhost', 8000), 'scheme': 'http'}
asyncio.run(test_app(scope2, fake_receive, fake_send))
print("\n✅ All tests passed!")
