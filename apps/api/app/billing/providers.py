import hmac
import json
from dataclasses import dataclass
from hashlib import sha256
from uuid import uuid4

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class ProviderCheckout:
    provider: str
    provider_payment_id: str
    checkout_url: str
    status: str = "pending"


@dataclass(frozen=True)
class ProviderEvent:
    provider: str
    event_type: str
    idempotency_key: str
    provider_payment_id: str | None
    status: str
    verified: bool
    payload: dict


class BillingProvider:
    name = "base"

    def create_checkout(self, *, plan_code: str, plan_name: str, amount_cents: int, currency: str, idempotency_key: str, user_id: int) -> ProviderCheckout:
        raise NotImplementedError

    def parse_webhook(self, raw_body: bytes, signature: str | None) -> ProviderEvent:
        raise NotImplementedError


class MockProvider(BillingProvider):
    name = "mock"

    def create_checkout(self, *, plan_code: str, plan_name: str, amount_cents: int, currency: str, idempotency_key: str, user_id: int) -> ProviderCheckout:
        return ProviderCheckout(
            provider=self.name,
            provider_payment_id=f"mock_{idempotency_key}",
            checkout_url=f"/billing/pending?payment={idempotency_key}",
        )

    def parse_webhook(self, raw_body: bytes, signature: str | None) -> ProviderEvent:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
        event_id = str(payload.get("event_id") or payload.get("id") or uuid4())
        status = str(payload.get("status") or "paid")
        return ProviderEvent(
            provider=self.name,
            event_type=str(payload.get("event_type") or f"payment.{status}"),
            idempotency_key=f"mock:{event_id}",
            provider_payment_id=payload.get("provider_payment_id"),
            status=status,
            verified=True,
            payload=payload,
        )


class CoinbaseProvider(BillingProvider):
    name = "coinbase"

    def create_checkout(self, *, plan_code: str, plan_name: str, amount_cents: int, currency: str, idempotency_key: str, user_id: int) -> ProviderCheckout:
        settings = get_settings()
        if not settings.coinbase_api_key:
            raise RuntimeError("COINBASE_API_KEY is not configured")

        body = {
            "name": plan_name,
            "description": f"DeckPilot {plan_name}",
            "local_price": {"amount": f"{amount_cents / 100:.2f}", "currency": currency},
            "pricing_type": "fixed_price",
            "metadata": {
                "plan_code": plan_code,
                "user_id": str(user_id),
                "idempotency_key": idempotency_key,
            },
        }
        response = httpx.post(
            settings.coinbase_charge_url,
            headers={
                "X-CC-Api-Key": settings.coinbase_api_key,
                "X-CC-Version": "2018-03-22",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()["data"]
        return ProviderCheckout(
            provider=self.name,
            provider_payment_id=data["id"],
            checkout_url=data["hosted_url"],
        )

    def parse_webhook(self, raw_body: bytes, signature: str | None) -> ProviderEvent:
        settings = get_settings()
        if not settings.coinbase_webhook_secret or not signature:
            verified = False
        else:
            expected = hmac.new(settings.coinbase_webhook_secret.encode("utf-8"), raw_body, sha256).hexdigest()
            verified = hmac.compare_digest(expected, signature)

        payload = json.loads(raw_body.decode("utf-8") or "{}")
        event = payload.get("event", {})
        data = event.get("data", {})
        timeline = data.get("timeline") or []
        latest_status = (timeline[-1].get("status") if timeline else event.get("type") or "").lower()
        if latest_status in {"completed", "confirmed", "charge:confirmed"}:
            status = "paid"
        elif latest_status in {"failed", "expired"}:
            status = "failed"
        else:
            status = "pending"
        metadata = data.get("metadata") or {}
        event_key = event.get("id") or data.get("id") or uuid4()

        return ProviderEvent(
            provider=self.name,
            event_type=str(event.get("type") or "coinbase.unknown"),
            idempotency_key=f"coinbase:{event_key}",
            provider_payment_id=data.get("id"),
            status=status,
            verified=verified,
            payload={**payload, "_metadata": metadata},
        )


def provider_for(name: str | None = None) -> BillingProvider:
    settings = get_settings()
    provider_name = (name or settings.billing_provider).lower()
    if settings.environment == "production" and provider_name == "mock":
        raise ValueError("Mock billing provider is forbidden in production")
    if provider_name == "coinbase":
        return CoinbaseProvider()
    if provider_name == "mock":
        return MockProvider()
    raise ValueError(f"Unsupported billing provider: {provider_name}")
