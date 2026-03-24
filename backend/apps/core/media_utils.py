from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.utils.text import slugify


ALLOWED_UPLOAD_EXTENSIONS = {
    "avatar": {".png", ".jpg", ".jpeg", ".webp", ".gif"},
    "city-cover": {".png", ".jpg", ".jpeg", ".webp", ".gif"},
    "attraction-image": {".png", ".jpg", ".jpeg", ".webp", ".gif"},
    "post-cover": {".png", ".jpg", ".jpeg", ".webp", ".gif"},
    "excel-import": {".xlsx"},
    "attachment": {".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf", ".doc", ".docx", ".xlsx"},
}


@dataclass(frozen=True)
class SavedUpload:
    storage_key: str
    url: str
    content: bytes
    content_type: str
    original_name: str
    size: int


def _clean_folder_name(folder: str) -> str:
    slug = slugify(folder or "misc")
    return slug or "misc"


def _clean_relative_path(relative_path: str) -> str:
    return relative_path.replace("\\", "/").strip("/")


def _build_storage_key(relative_path: str) -> str:
    normalized = _clean_relative_path(relative_path)
    prefix = str(getattr(settings, "OSS_MEDIA_PREFIX", "") or "").strip("/")
    return f"{prefix}/{normalized}" if prefix else normalized


def _build_signed_url(storage_key: str) -> str:
    expires = int(getattr(settings, "OSS_SIGN_URL_EXPIRE_SECONDS", 315360000))
    return _get_oss_bucket().sign_url("GET", storage_key, expires, slash_safe=True)


def ensure_upload_extension(filename: str, category: str) -> str:
    suffix = Path(filename).suffix.lower()
    allowed = ALLOWED_UPLOAD_EXTENSIONS.get(category) or ALLOWED_UPLOAD_EXTENSIONS["attachment"]
    if suffix not in allowed:
        raise ValueError(f"涓嶆敮鎸佺殑鏂囦欢绫诲瀷: {suffix or 'unknown'}")
    return suffix


def _guess_content_type(filename: str, uploaded_file) -> str:
    return (
        getattr(uploaded_file, "content_type", "")
        or mimetypes.guess_type(filename)[0]
        or "application/octet-stream"
    )


def _read_uploaded_content(uploaded_file) -> bytes:
    chunks = []
    for chunk in uploaded_file.chunks():
        chunks.append(chunk)
    return b"".join(chunks)


def _validate_oss_settings() -> None:
    missing = [
        name
        for name in ("OSS_ACCESS_KEY_ID", "OSS_ACCESS_KEY_SECRET", "OSS_BUCKET_NAME", "OSS_ENDPOINT")
        if not getattr(settings, name, "")
    ]
    if missing:
        raise RuntimeError(f"Missing OSS settings: {', '.join(missing)}")


@lru_cache(maxsize=1)
def _get_oss_bucket():
    _validate_oss_settings()
    try:
        import oss2
    except ModuleNotFoundError as exc:
        raise RuntimeError("oss2 is not installed.") from exc

    auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
    return oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)


def _write_oss_file(relative_path: str, content: bytes, content_type: str) -> str:
    storage_key = _build_storage_key(relative_path)
    try:
        bucket = _get_oss_bucket()
        bucket.put_object(storage_key, content, headers={"Content-Type": content_type})
    except Exception as exc:
        raise RuntimeError("Failed to upload file to OSS.") from exc
    return storage_key


def save_uploaded_file(uploaded_file, *, folder: str, category: str) -> SavedUpload:
    suffix = ensure_upload_extension(uploaded_file.name, category)
    folder_name = _clean_folder_name(folder)
    relative_path = f"{folder_name}/{uuid4().hex}{suffix}"
    content = _read_uploaded_content(uploaded_file)
    content_type = _guess_content_type(uploaded_file.name, uploaded_file)
    storage_key = _write_oss_file(relative_path, content, content_type)

    return SavedUpload(
        storage_key=storage_key,
        url=_build_signed_url(storage_key),
        content=content,
        content_type=content_type,
        original_name=uploaded_file.name,
        size=len(content),
    )
