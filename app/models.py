"""
Data models for Supabase Keepalive.

Simple dataclasses for type safety and clarity.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Project:
    """Supabase project configuration."""

    id: int
    name: str
    url: str
    api_key: str
    keepalive_method: str = "rpc"
    table_name: Optional[str] = None
    enabled: bool = True
    last_status: Optional[str] = None
    last_checked: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """Create Project from database row dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            url=data["url"],
            api_key=data["api_key"],
            keepalive_method=data.get("keepalive_method", "rpc"),
            table_name=data.get("table_name"),
            enabled=bool(data.get("enabled", 1)),
            last_status=data.get("last_status"),
            last_checked=data.get("last_checked"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict:
        """Convert Project to dict."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "api_key": self.api_key,
            "keepalive_method": self.keepalive_method,
            "table_name": self.table_name,
            "enabled": self.enabled,
            "last_status": self.last_status,
            "last_checked": self.last_checked,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class KeepaliveResult:
    """Result of a keepalive operation."""

    project_id: int
    project_name: str
    success: bool
    message: str
    timestamp: str
    method_used: str

    def __str__(self) -> str:
        """String representation."""
        status = "SUCCESS" if self.success else "FAILED"
        return f"[{self.project_name}] {status}: {self.message}"
