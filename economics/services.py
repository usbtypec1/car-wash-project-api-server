from dataclasses import dataclass
from datetime import datetime

from economics.models import Penalty, Surcharge

__all__ = (
    'create_penalty_and_send_notification',
    'create_surcharge_and_send_notification',
)


@dataclass(frozen=True, slots=True)
class SurchargeCreateResult:
    id: int
    staff_id: int
    reason: str
    amount: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PenaltyCreateResult:
    id: int
    staff_id: int
    reason: str
    created_at: datetime


def format_penalty_notification_text(
        reason: str
) -> str:
    return f'<b>🛑 Вы получили штраф по причине:</b> {reason}'


def create_penalty_and_send_notification(
        *,
        staff_id: int,
        reason: str,
) -> PenaltyCreateResult:
    penalty = Penalty.objects.create(
        staff_id=staff_id,
        reason=reason,
    )
    return PenaltyCreateResult(
        id=penalty.id,
        staff_id=penalty.staff_id,
        reason=penalty.reason,
        created_at=penalty.created_at,
    )


def format_surcharge_notification_text(
        reason: str,
        amount: int,
) -> str:
    return (
        f'<b>💰 Вы получили доплату в размере {amount}'
        f' по причине:</b> {reason}'
    )


def create_surcharge_and_send_notification(
        *,
        staff_id: int,
        reason: str,
        amount: int,
) -> SurchargeCreateResult:
    surcharge = Surcharge.objects.create(
        staff_id=staff_id,
        reason=reason,
        amount=amount,
    )
    return SurchargeCreateResult(
        id=surcharge.id,
        staff_id=surcharge.staff_id,
        reason=surcharge.reason,
        amount=surcharge.amount,
        created_at=surcharge.created_at,
    )
