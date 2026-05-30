from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path

from .config import TENANT_CONFIG_PATH


@dataclass(frozen=True)
class TenantPolicy:
    tenant_id: str
    token_hash: str
    allowed_providers: list[str]
    allow_byok: bool


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _matches(stored_hash: str, token: str) -> bool:
    if stored_hash.startswith("sha256:"):
        stored_hash = stored_hash.split(":", 1)[1]
    return hmac.compare_digest(stored_hash, _hash_token(token))


def load_tenant_policies(path: Path | None = None) -> dict[str, TenantPolicy]:
    config_path = path or TENANT_CONFIG_PATH
    if not config_path.exists():
        return {}
    data = json.loads(config_path.read_text(encoding="utf-8"))
    tenants = data.get("tenants", {})
    policies: dict[str, TenantPolicy] = {}
    for tenant_id, config in tenants.items():
        token_hash = str(config.get("token_hash", "")).strip()
        if not token_hash:
            continue
        allowed = [item.lower() for item in config.get("allowed_providers", [])]
        allow_byok = bool(config.get("allow_byok", False))
        policies[tenant_id] = TenantPolicy(
            tenant_id=tenant_id,
            token_hash=token_hash,
            allowed_providers=allowed,
            allow_byok=allow_byok,
        )
    return policies


def validate_tenant(
    tenant_id: str | None, token: str | None, policies: dict[str, TenantPolicy]
) -> TenantPolicy | None:
    if not tenant_id or not token:
        return None
    policy = policies.get(tenant_id)
    if not policy:
        return None
    if not _matches(policy.token_hash, token):
        return None
    return policy
