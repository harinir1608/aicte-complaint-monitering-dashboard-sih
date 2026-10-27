from __future__ import annotations

import os
import uuid
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

# ── Allowed file types and size limit ─────────────────────────────────────────

ALLOWED_EXTENSIONS = {
    "pdf", "docx", "doc", "jpg", "jpeg", "png", "xlsx", "xls", "csv"
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_upload(file: UploadFile) -> None:
    """Validate file extension and content-type."""
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '.{ext}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )


def _generate_storage_key(original_filename: str) -> str:
    """Return a UUID-based, non-guessable storage key that preserves the extension."""
    ext = ""
    if "." in original_filename:
        ext = "." + original_filename.rsplit(".", 1)[-1].lower()
    return f"{uuid.uuid4().hex}{ext}"


# ── Abstract base ─────────────────────────────────────────────────────────────

class StorageService(ABC):
    @abstractmethod
    def upload_file(self, file_data: bytes, filename: str, content_type: Optional[str]) -> str:
        """Upload file bytes and return the storage key."""

    @abstractmethod
    def get_file_url(self, storage_key: str) -> str:
        """Return a URL or path to access the stored file."""

    @abstractmethod
    def delete_file(self, storage_key: str) -> None:
        """Delete the stored file."""


# ── Local storage adapter ──────────────────────────────────────────────────────

class LocalStorageService(StorageService):
    """Saves files to the local filesystem under LOCAL_STORAGE_PATH."""

    def __init__(self) -> None:
        self.base_path = Path(getattr(settings, "LOCAL_STORAGE_PATH", "/tmp/aicte_uploads"))
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload_file(self, file_data: bytes, filename: str, content_type: Optional[str]) -> str:
        key = _generate_storage_key(filename)
        dest = self.base_path / key
        dest.write_bytes(file_data)
        return key

    def get_file_url(self, storage_key: str) -> str:
        return f"/api/v1/documents/{storage_key}/download"

    def delete_file(self, storage_key: str) -> None:
        target = self.base_path / storage_key
        if target.exists():
            target.unlink()


# ── Azure Blob Storage adapter ─────────────────────────────────────────────────

class AzureBlobStorageService(StorageService):
    """Stores files in Azure Blob Storage.

    Requires:
      AZURE_STORAGE_CONNECTION_STRING  or  (AZURE_STORAGE_ACCOUNT + AZURE_STORAGE_KEY)
      AZURE_STORAGE_CONTAINER_NAME
    """

    def __init__(self) -> None:
        try:
            from azure.storage.blob import BlobServiceClient  # type: ignore
        except ImportError:
            raise RuntimeError(
                "azure-storage-blob is not installed. "
                "Run: pip install azure-storage-blob"
            )

        connection_string = getattr(settings, "AZURE_STORAGE_CONNECTION_STRING", None)
        if connection_string:
            self._client = BlobServiceClient.from_connection_string(connection_string)
        else:
            account = getattr(settings, "AZURE_STORAGE_ACCOUNT", "")
            key = getattr(settings, "AZURE_STORAGE_KEY", "")
            self._client = BlobServiceClient(
                account_url=f"https://{account}.blob.core.windows.net",
                credential=key,
            )
        self.container = getattr(settings, "AZURE_STORAGE_CONTAINER_NAME", "aicte-documents")

    def upload_file(self, file_data: bytes, filename: str, content_type: Optional[str]) -> str:
        key = _generate_storage_key(filename)
        container_client = self._client.get_container_client(self.container)
        blob_client = container_client.get_blob_client(key)
        blob_client.upload_blob(
            file_data,
            overwrite=True,
            content_settings={"content_type": content_type} if content_type else None,
        )
        return key

    def get_file_url(self, storage_key: str) -> str:
        # Return a server-side proxy URL to avoid exposing raw Azure URLs.
        return f"/api/v1/documents/{storage_key}/download"

    def delete_file(self, storage_key: str) -> None:
        container_client = self._client.get_container_client(self.container)
        blob_client = container_client.get_blob_client(storage_key)
        blob_client.delete_blob(delete_snapshots="include")


# ── Factory ────────────────────────────────────────────────────────────────────

def get_storage_service() -> StorageService:
    """Return the appropriate storage service based on USE_LOCAL_STORAGE setting."""
    use_local = getattr(settings, "USE_LOCAL_STORAGE", True)
    if use_local:
        return LocalStorageService()
    return AzureBlobStorageService()
