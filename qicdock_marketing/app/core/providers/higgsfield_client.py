"""Shared async client for the Higgsfield generative-media API.

Lifecycle (docs.higgsfield.ai):
1. POST JSON to a model endpoint -> { id / request_id, status_url }
2. Poll GET /requests/{id}/status until completed/failed
3. Download output files from the returned URLs
"""
import asyncio
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://platform.higgsfield.ai"
POLL_INTERVAL_SECONDS = 5


class HiggsfieldError(Exception):
    pass


class HiggsfieldClient:
    def __init__(
        self,
        key_id: str,
        key_secret: str,
        poll_timeout_seconds: int = 600,
    ):
        self.key_id = key_id
        self.key_secret = key_secret
        self.poll_timeout_seconds = poll_timeout_seconds

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Key {self.key_id}:{self.key_secret}",
            "Content-Type": "application/json",
        }

    async def submit(self, endpoint: str, payload: dict) -> dict:
        url = f"{BASE_URL}{endpoint}"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload, headers=self._headers)
            if resp.status_code >= 400:
                raise HiggsfieldError(
                    f"Submit failed ({resp.status_code}) for {endpoint}: {resp.text[:300]}"
                )
            return resp.json()

    async def wait_for_result(self, submit_response: dict,
                              timeout_seconds: Optional[int] = None) -> list[str]:
        """Poll until completion. Returns list of output file URLs."""
        request_id = (
            submit_response.get("id")
            or submit_response.get("request_id")
            or (submit_response.get("request") or {}).get("id")
        )
        status_url = (
            submit_response.get("status_url")
            or f"{BASE_URL}/requests/{request_id}/status"
        )
        if not request_id and not status_url:
            raise HiggsfieldError(f"No request id in submit response: {submit_response}")

        if isinstance(status_url, str) and status_url.startswith("/"):
            status_url = f"{BASE_URL}{status_url}"

        timeout = timeout_seconds or self.poll_timeout_seconds
        elapsed = 0

        async with httpx.AsyncClient(timeout=30) as client:
            while elapsed < timeout:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                elapsed += POLL_INTERVAL_SECONDS

                resp = await client.get(status_url, headers=self._headers)
                if resp.status_code >= 400:
                    raise HiggsfieldError(
                        f"Status check failed ({resp.status_code}): {resp.text[:300]}"
                    )
                data = resp.json()
                status = str(data.get("status", data.get("state", ""))).lower()

                if status in {"completed", "success", "succeeded"}:
                    return self._extract_urls(data)
                if status in {"failed", "error", "nsfw", "cancelled", "canceled"}:
                    raise HiggsfieldError(
                        f"Higgsfield job {status}: {str(data)[:300]}"
                    )

            raise HiggsfieldError(f"Timed out after {timeout}s waiting for job {request_id}")

    @staticmethod
    def _extract_urls(data: dict) -> list[str]:
        """Pull output URLs from the various response shapes."""
        urls: list[str] = []

        # Shape 1: {"images": [{"url": ...}]} (docs standard for images)
        images = data.get("images") or []
        if isinstance(images, list):
            for img in images:
                if isinstance(img, dict) and img.get("url"):
                    urls.append(img["url"])

        # Shape 2: {"jobs": [{"results": {"raw": {"url": ...}}}]}
        if not urls:
            for job in data.get("jobs") or []:
                raw = (job.get("results") or {}).get("raw") or {}
                if raw.get("url"):
                    urls.append(raw["url"])

        # Shape 3: {"outputs": [{"url": ...}]} / flat results
        if not urls:
            outputs = data.get("outputs") or data.get("results") or []
            if isinstance(outputs, dict):
                outputs = [outputs]
            for out in outputs:
                if isinstance(out, dict):
                    u = out.get("url") or out.get("image_url") or out.get("video_url")
                    if u:
                        urls.append(u)

        if not urls:
            raise HiggsfieldError(f"Job completed but no output URLs found: {str(data)[:300]}")
        return urls

    async def download(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.content

    async def upload_image(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        """Upload an image to Higgsfield storage; returns the public URL.

        Flow (docs/concepts/file-uploads):
        1. POST /files/generate-upload-url -> {public_url, upload_url, upload_headers}
        2. PUT bytes to upload_url with the returned headers
        3. Use public_url as model input
        """
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{BASE_URL}/files/generate-upload-url",
                json={"content_type": mime_type},
                headers=self._headers,
            )
            if resp.status_code >= 400:
                raise HiggsfieldError(f"Upload URL fetch failed: {resp.text[:200]}")
            info = resp.json()
            upload_url = info.get("upload_url")
            public_url = info.get("public_url")
            upload_headers = info.get("upload_headers") or {"Content-Type": mime_type}

            put = await client.put(upload_url, content=image_bytes, headers=upload_headers)
            if put.status_code >= 400:
                raise HiggsfieldError(f"Image upload failed: {put.text[:200]}")

        if not public_url:
            raise HiggsfieldError("Upload response missing public_url")
        return public_url
