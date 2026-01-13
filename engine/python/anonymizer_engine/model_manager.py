import hashlib
import json
import os
import shutil
import urllib.request
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(frozen=True)
class ModelRef:
    provider: str          # "candle"
    model_id: str          # huggingface repo id or local id
    filename: str          # file within repo or local filename
    sha256: Optional[str]  # optional expected hash


class ModelManager:
    """
    Offline-first model manager.

    Design goals:
    - explicit downloads only
    - local cache directory
    - recordable version info via hash
    - no background updates
    """

    def __init__(self, models_dir: str) -> None:
        self.models_dir = os.path.abspath(models_dir)
        os.makedirs(self.models_dir, exist_ok=True)

    def model_path(self, ref: ModelRef) -> str:
        safe_model_id = ref.model_id.replace("/", "__")
        folder = os.path.join(self.models_dir, ref.provider, safe_model_id)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, ref.filename)

    def is_present(self, ref: ModelRef) -> bool:
        return os.path.exists(self.model_path(ref))

    def sha256_file(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def verify(self, ref: ModelRef) -> Dict:
        path = self.model_path(ref)
        if not os.path.exists(path):
            return {"ok": False, "reason": "missing", "path": path}

        actual = self.sha256_file(path)
        if ref.sha256 and ref.sha256.lower() != actual.lower():
            return {"ok": False, "reason": "hash_mismatch", "path": path, "expected": ref.sha256, "actual": actual}

        return {"ok": True, "path": path, "sha256": actual}

    def download_from_huggingface(
        self,
        ref: ModelRef,
        token: Optional[str] = None,
    ) -> Dict:
        """
        Downloads a single file from HuggingFace.

        This is explicit, user-initiated, and can be disabled by not calling it.
        """
        dest = self.model_path(ref)

        if os.path.exists(dest):
            return {"ok": True, "status": "already_present", "path": dest, **self.verify(ref)}

        url = f"https://huggingface.co/{ref.model_id}/resolve/main/{ref.filename}"

        tmp = dest + ".partial"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp, open(tmp, "wb") as out:
                shutil.copyfileobj(resp, out)
        except Exception as e:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            return {"ok": False, "reason": "download_failed", "error": str(e), "url": url}

        os.replace(tmp, dest)

        ver = self.verify(ref)
        if not ver.get("ok"):
            return {"ok": False, "reason": "verification_failed", "path": dest, **ver}

        return {"ok": True, "status": "downloaded", "path": dest, **ver}

    def write_model_inventory(self, inventory_path: str, inventory: Dict) -> None:
        os.makedirs(os.path.dirname(inventory_path), exist_ok=True)
        with open(inventory_path, "w", encoding="utf-8") as f:
            json.dump(inventory, f, ensure_ascii=False, indent=2)
