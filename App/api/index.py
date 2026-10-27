import os
import sys

# Tambahkan root direktori ke sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app  # noqa: E402  (butuh sys.path di atas)

MOUNT_PREFIXES = ("/api/index.py", "/api/index", "/api")
# Route aplikasi yang memang berawalan /api/ sehingga tidak boleh di-strip
NATIVE_API_ROUTES = ("/api/format", "/api/download", "/api/active-learning")


def rewrite_path(path: str) -> str:
    """Memetakan path fungsi serverless Vercel ke path route aplikasi."""
    for prefix in MOUNT_PREFIXES:
        if path == prefix:
            return "/"
        if path.startswith(prefix + "/"):
            if prefix == "/api" and path.startswith(NATIVE_API_ROUTES):
                return path
            return path[len(prefix):]
    return path


class VercelPathMiddleware:
    """Middleware penyesuai route untuk Vercel Serverless."""

    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            scope["path"] = rewrite_path(scope.get("path", ""))
        await self.asgi_app(scope, receive, send)


app.add_middleware(VercelPathMiddleware)
