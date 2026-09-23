from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CustomerEntity:
    name: str
    href: str | None
    platform: str
