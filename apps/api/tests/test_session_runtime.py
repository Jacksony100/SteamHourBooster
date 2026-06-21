from app.core.models import SteamAccount
from app.sessions.adapters import MockSteamClientAdapter
from app.sessions.runtime import MemoryRuntimeStore, set_runtime_store


def test_runtime_state_is_shared_across_adapter_instances():
    """A fresh adapter instance (e.g. another worker process) must see session
    liveness recorded by a different instance — proving state is not per-process."""
    set_runtime_store(MemoryRuntimeStore())
    account = SteamAccount(id=42, user_id=1, label="x", username_encrypted="x", password_encrypted="x", steamid64="test-1")

    worker_a = MockSteamClientAdapter()
    worker_b = MockSteamClientAdapter()

    # No session yet: heartbeat on a different instance fails.
    assert worker_b.heartbeat(account, []).ok is False

    # Start on instance A...
    assert worker_a.start_session(account, [730]).ok is True
    # ...instance B sees it as live.
    assert worker_b.heartbeat(account, []).ok is True

    # Stop on instance B...
    assert worker_b.stop_session(account, []).ok is True
    # ...instance A now sees no active session.
    assert worker_a.heartbeat(account, []).ok is False


def test_close_all_clears_runtime_store():
    set_runtime_store(MemoryRuntimeStore())
    account = SteamAccount(id=7, user_id=1, label="x", username_encrypted="x", password_encrypted="x", steamid64="test-2")
    adapter = MockSteamClientAdapter()
    adapter.start_session(account, [570])
    assert adapter.heartbeat(account, []).ok is True
    adapter.close_all()
    assert adapter.heartbeat(account, []).ok is False
