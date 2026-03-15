from dataclasses import dataclass


@dataclass
class VaultEntry:

    service: str
    site: str
    login: str
    password: str
    status: str
    updated: str
    note: str