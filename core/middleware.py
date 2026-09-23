import logging
import re
import time
import uuid


from django.conf import settings
from django.core.exceptions import BadRequest, PermissionDenied, SuspiciousFileOperation
from django.http import Http404, JsonResponse
from django.core.signals import got_request_exception


from .context import reset_request_id, set_request_id

access_logger = logging.getLogger("access")
error_logger = logging.getLogger("app.errors")


#it only accepts "safe incoming IDs: stops log injection"
_SAFE_REQUEST_ID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.header = getattr(settings, "REQUEST_ID_HEADER", "HTTP_X_REQUEST_ID")
        self.meta_key = "HTTP_" + self.header.upper().replace("-","-")

    def __call__(self, request):
        incomming = request.META.get(self.meta_key)
        _request_id = incomming if incomming and _SAFE_REQUEST_ID.match(incomming) else str(uuid.uuid4())

        request.request_id = _request_id
        token = set_request_id(_request_id)
        try:
            response = self.get_response(request)

        finally:
            reset_request_id(token)

        response[self.header] = _request_id
        return response     


def get_client_ip(request, trusted_proxies: int) -> str:
    """
    Behind N trusted proxies the real client is the N-th entry from the END of X-Forwarded-For.
    Entries further left are client-controlled and can be spoofed.
    """
    remote = request.META.get("REMOTE_ADDR", "")
    if trusted_proxies <= 0:
        return remote                                   # not behind a proxy: ignore the header entirely
    parts = [p.strip() for p in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",") if p.strip()]
    return parts[-trusted_proxies] if len(parts) >= trusted_proxies else remote


class AccessLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exclude = tuple(getattr(settings, "ACCESS_LOG_EXCLUDE_PATHS", ("/healthz/",)))
        self.trusted_proxies = getattr(settings, "TRUSTED_PROXY_COUNT", 0)

    def __call__(self, request):
        if request.path.startswith(self.exclude):       # health checks would drown real traffic
            return self.get_response(request)

        start = time.perf_counter()
        response = self.get_response(request)          # everything inside runs here
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        # DRF authenticates INSIDE the view and copies the result onto the Django request,
        # so after get_response() this is the token/JWT/session user, not just the session user.
        user = getattr(request, "user", None)
        user_id = user.pk if getattr(user, "is_authenticated", False) else None

        status = response.status_code
        level = logging.ERROR if status >= 500 else logging.WARNING if status >= 400 else logging.INFO

        access_logger.log(
            level,
            "%s %s -> %s", request.method, request.path, status,
            extra={
                "http_method": request.method,
                "http_path": request.path,              # path only: query strings can carry tokens
                "status_code": status,
                "duration_ms": duration_ms,
                "user_id": user_id,
                "client_ip": get_client_ip(request, self.trusted_proxies),
            },
        )
        return response
            
    