import datetime
from dataclasses import dataclass
from enum import auto, StrEnum
from typing import Final, TypeAlias, TypedDict

from economics.exceptions import (
    CarTransporterPenaltyNotFoundError,
    CarTransporterSurchargeNotFoundError, InvalidPenaltyConsequenceError,
)
from economics.models import Penalty, Surcharge
from economics.selectors import compute_staff_penalties_count
from shifts.selectors import get_shift_by_id


class PenaltyReason(StrEnum):
    NOT_SHOWING_UP = auto()
    EARLY_LEAVE = auto()
    LATE_REPORT = auto()


@dataclass(frozen=True, slots=True)
class PenaltyAmountAndConsequence:
    amount: int
    consequence: str | None


class PenaltyConfig(TypedDict):
    threshold: int | float
    amount: int
    consequence: Penalty.Consequence | None


PenaltyConfigs: TypeAlias = tuple[PenaltyConfig, ...]
PenaltyReasonToConfigs: TypeAlias = dict[PenaltyReason, PenaltyConfigs]

PENALTY_CONFIGS: Final[PenaltyReasonToConfigs] = {
    PenaltyReason.LATE_REPORT: (
        {
            'threshold': 0,
            'amount': 0,
            'consequence': Penalty.Consequence.WARN,
        },
        {
            'threshold': 1,
            'amount': 100,
            'consequence': None,
        },
        {
            'threshold': float('inf'),
            'amount': 300,
            'consequence': None,
        },
    ),
    PenaltyReason.NOT_SHOWING_UP: (
        {
            'threshold': 0,
            'amount': 500,
            'consequence': None,
        },
        {
            'threshold': 1,
            'amount': 1000,
            'consequence': None,
        },
        {
            'threshold': 2,
            'amount': 1000,
            'consequence': Penalty.Consequence.DISMISSAL,
        },
        {
            'threshold': float('inf'),
            'amount': 0,
            'consequence': Penalty.Consequence.DISMISSAL,
        },
    ),
}


def compute_penalty_amount_and_consequence(
        *,
        staff_id: int,
        reason: PenaltyReason | str,
) -> PenaltyAmountAndConsequence:
    """
    Compute penalty amount and consequence based on staff violation reason
    and history.

    Args:
        staff_id: The ID of the staff member
        reason: The reason for the penalty

    Returns:
        PenaltyAmountAndConsequence with calculated amount and potential
        consequence

    Raises:
        InvalidPenaltyConsequenceError if an unsupported penalty reason is
        provided
    """
    if reason == PenaltyReason.EARLY_LEAVE:
        return PenaltyAmountAndConsequence(amount=1000, consequence=None)

    penalties_count = compute_staff_penalties_count(
        staff_id=staff_id,
        reason=reason,
    )

    penalty_config = PENALTY_CONFIGS.get(reason, tuple())

    for config in penalty_config:
        threshold = config['threshold']
        amount = config['amount']
        consequence = config['consequence']

        if penalties_count <= threshold:
            return PenaltyAmountAndConsequence(
                amount=amount,
                consequence=consequence
            )

    raise InvalidPenaltyConsequenceError(
        staff_id=staff_id,
        penalty_reason=reason,
        penalties_count=penalties_count,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class PenaltyCreateResult:
    id: int
    staff_id: int
    staff_full_name: str
    shift_id: int
    shift_date: datetime.date
    reason: str
    consequence: str | None
    amount: int
    created_at: datetime.datetime


def create_penalty(
        *,
        shift_id: int,
        reason: str,
        amount: int | None,
) -> PenaltyCreateResult:
    """
    Give penalty for staff member.
    If penalty amount is not provided,
    it will be automatically computed from penalty reason.

    Keyword Args:
        shift_id: shift penalty related to.
        reason: reason for penalty.
        amount: penalty amount.

    Returns:
        Created penalty.
    """
    shift = get_shift_by_id(shift_id)

    consequence: str | None = None
    if amount is None:
        penalty_amount_and_consequence = (
            compute_penalty_amount_and_consequence(
                staff_id=shift.staff_id,
                reason=reason,
            ))
        amount = penalty_amount_and_consequence.amount
        consequence = penalty_amount_and_consequence.consequence

    penalty = Penalty(
        shift_id=shift_id,
        reason=reason,
        amount=amount,
        consequence=consequence,
    )
    penalty.save()

    return PenaltyCreateResult(
        id=penalty.id,
        staff_id=shift.staff_id,
        staff_full_name=shift.staff.full_name,
        shift_id=shift_id,
        shift_date=shift.date,
        reason=reason,
        consequence=consequence,
        amount=amount,
        created_at=penalty.created_at,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class CarTransporterPenaltyDeleteInteractor:
    penalty_id: int

    def execute(self) -> None:
        deleted_count = Penalty.objects.filter(id=self.penalty_id).delete()
        if deleted_count == 0:
            raise CarTransporterPenaltyNotFoundError


@dataclass(frozen=True, slots=True, kw_only=True)
class CarTransporterSurchargeDeleteInteractor:
    surcharge_id: int

    def execute(self) -> None:
        deleted_count = Surcharge.objects.filter(id=self.surcharge_id).delete()
        if deleted_count == 0:
            raise CarTransporterSurchargeNotFoundError
