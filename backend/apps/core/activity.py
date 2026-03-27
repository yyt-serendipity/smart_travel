from __future__ import annotations

from collections.abc import Mapping

from apps.backoffice.models import OperationLog


def _get_client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _serialize_target(target) -> dict:
    # Some audit events point at plain dict payloads instead of Django model instances.
    if target is None:
        return {"target_type": "", "target_id": None, "target_name": ""}
    if isinstance(target, Mapping):
        return {
            "target_type": str(target.get("type", "")),
            "target_id": target.get("id"),
            "target_name": str(target.get("name", "")),
        }
    return {
        "target_type": target.__class__.__name__,
        "target_id": getattr(target, "pk", None),
        "target_name": str(target)[:255],
    }


def log_operation(request, category: str, action: str, *, status: str = OperationLog.STATUS_SUCCESS, target=None, detail=None):
    if request is None:
        return None

    target_data = _serialize_target(target)
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        user = None

    return OperationLog.objects.create(
        user=user,
        category=category,
        action=action,
        status=status,
        target_type=target_data["target_type"],
        target_id=target_data["target_id"],
        target_name=target_data["target_name"],
        request_path=request.path[:255],
        request_method=request.method[:12],
        ip_address=_get_client_ip(request)[:64],
        detail=detail or {},
    )
