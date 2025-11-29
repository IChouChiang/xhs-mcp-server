"""Simple JSON-based storage for the orchestrator."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ..schemas import GenerationResponse, IPProfile, ResearchFinding
from ..utils.logger import get_logger


class StorageClient:
    def __init__(self, storage_path: Path) -> None:
        self._path = storage_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text(json.dumps({"sessions": []}, ensure_ascii=False, indent=2), "utf-8")
        self._logger = get_logger("services.StorageClient")

    def record_generation(
        self,
        *,
        prompt: str,
        response: GenerationResponse,
    ) -> None:
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "prompt": prompt,
            "content": response.content,
            "ip_profile": response.ip_profile.dict(by_alias=True),
            "reason": response.reason,
            "research_notes": [finding.dict() for finding in response.research_notes],
        }
        data = self._load()
        data.setdefault("sessions", []).append(payload)
        self._dump(data)
        self._logger.info("Stored generation result", extra={"ip": response.ip_profile.id})

    def list_sessions(self) -> List[Dict[str, Any]]:
        return list(self._load().get("sessions", []))

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        data = self._load()
        profiles = data.get("profiles", {})
        return profiles.get(user_id)

    def create_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        data = self._load()
        profiles = data.setdefault("profiles", {})
        profiles[user_id] = profile_data
        self._dump(data)
        return profile_data

    def update_profile(self, user_id: str, profile_patch: Dict[str, Any]) -> Dict[str, Any]:
        data = self._load()
        profiles = data.setdefault("profiles", {})
        current_profile = profiles.get(user_id, {})
        current_profile.update(profile_patch)
        profiles[user_id] = current_profile
        self._dump(data)
        return current_profile

    def _load(self) -> Dict[str, Any]:
        return json.loads(self._path.read_text("utf-8"))

    def _dump(self, data: Dict[str, Any]) -> None:
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
