from dataclasses import dataclass
from typing import Protocol

from app.core.config import get_settings
from app.core.models import SteamAccount


@dataclass(frozen=True)
class SteamClientResult:
    ok: bool
    steamid64: str | None = None
    steam_guard_required: bool = False
    error: str | None = None


class SteamClientAdapter(Protocol):
    def login_account(self, username: str, password: str, steam_guard_code: str | None = None) -> SteamClientResult: ...

    def logout_account(self, account: SteamAccount) -> SteamClientResult: ...

    def start_session(self, account: SteamAccount, game_ids: list[int]) -> SteamClientResult: ...

    def heartbeat(self, account: SteamAccount, game_ids: list[int]) -> SteamClientResult: ...

    def stop_session(self, account: SteamAccount, game_ids: list[int]) -> SteamClientResult: ...

    def close_all(self) -> None: ...


class MockSteamClientAdapter:
    """Safe dev/test adapter.

    It simulates transparent session lifecycle state only. It does not implement
    stealth, platform-risk evasion, Steam Guard circumvention, network-routing evasion, or hidden behavior.
    """

    def __init__(self, *, fail_start: bool = False, fail_stop: bool = False, guard_required: bool = False) -> None:
        self.fail_start = fail_start
        self.fail_stop = fail_stop
        self.guard_required = guard_required
        self.started_accounts: set[int] = set()

    def login_account(self, username: str, password: str, steam_guard_code: str | None = None) -> SteamClientResult:
        if self.guard_required and not steam_guard_code:
            return SteamClientResult(ok=False, steam_guard_required=True, error="Steam Guard code required")
        return SteamClientResult(ok=True, steamid64=f"test-{abs(hash(username)) % 10_000_000}")

    def logout_account(self, account: SteamAccount) -> SteamClientResult:
        self.started_accounts.discard(account.id)
        return SteamClientResult(ok=True)

    def start_session(self, account: SteamAccount, game_ids: list[int]) -> SteamClientResult:
        if self.fail_start:
            return SteamClientResult(ok=False, error="Mock Steam client failed to start session")
        self.started_accounts.add(account.id)
        return SteamClientResult(ok=True, steamid64=account.steamid64)

    def heartbeat(self, account: SteamAccount, game_ids: list[int]) -> SteamClientResult:
        if account.id not in self.started_accounts:
            return SteamClientResult(ok=False, error="Mock Steam client has no active session")
        return SteamClientResult(ok=True, steamid64=account.steamid64)

    def stop_session(self, account: SteamAccount, game_ids: list[int]) -> SteamClientResult:
        if self.fail_stop:
            return SteamClientResult(ok=False, error="Mock Steam client failed to stop session")
        self.started_accounts.discard(account.id)
        return SteamClientResult(ok=True)

    def close_all(self) -> None:
        self.started_accounts.clear()


class DisabledSteamClientAdapter(MockSteamClientAdapter):
    def login_account(self, username: str, password: str, steam_guard_code: str | None = None) -> SteamClientResult:
        return SteamClientResult(ok=False, error="Real Steam client adapter is not enabled in this build")

    def start_session(self, account: SteamAccount, game_ids: list[int]) -> SteamClientResult:
        return SteamClientResult(ok=False, error="Real Steam client adapter is not enabled in this build")


_adapter: SteamClientAdapter | None = None


def set_steam_client_adapter(adapter: SteamClientAdapter | None) -> None:
    global _adapter
    _adapter = adapter


def get_steam_client_adapter() -> SteamClientAdapter:
    global _adapter
    if _adapter:
        return _adapter
    settings = get_settings()
    if settings.steam_integration_mode == "demo" or settings.steam_test_mode:
        _adapter = MockSteamClientAdapter()
    else:
        _adapter = DisabledSteamClientAdapter()
    return _adapter
