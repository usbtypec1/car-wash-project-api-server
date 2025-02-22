import collections
import datetime
import operator
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache, reduce
from typing import Final, TypeAlias, TypedDict
from uuid import UUID

from django.db import transaction
from django.db.models import Count, Q, QuerySet, Sum
from django.utils import timezone

from car_washes.models import CarWash
from core.services import get_current_shift_date
from shifts.exceptions import (
    MonthNotAvailableError, ShiftAlreadyExistsError,
    ShiftNotFoundError,
    StaffHasActiveShiftError,
)
from shifts.models import (
    AvailableDate, CarToWash, CarToWashAdditionalService, Shift,
    ShiftFinishPhoto,
)
from shifts.selectors import has_any_finished_shift
from staff.models import Staff


@dataclass(frozen=True, slots=True, kw_only=True)
class ShiftsDeleteOnStaffBanInteractor:
    """
    Interactor to delete shifts of staff if he gets banned.
    """
    staff_id: int
    from_date: datetime.date

    def execute(self) -> None:
        (
            Shift.objects
            .filter(staff_id=self.staff_id, date__gte=self.from_date)
            .delete()
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ShiftItem:
    id: int
    date: datetime.date


@dataclass(frozen=True, slots=True, kw_only=True)
class ShiftsCreateResult:
    staff_id: int
    staff_full_name: str
    shifts: list[ShiftItem]


@dataclass(frozen=True, slots=True)
class ShiftTestCreateResult:
    staff_id: int
    staff_full_name: str
    shift_id: int
    shift_date: datetime.date


@dataclass(frozen=True, slots=True)
class ShiftExtraCreateResult:
    staff_id: int
    staff_full_name: str
    shift_id: int
    shift_date: datetime.date


def get_existing_shift_dates(
        *,
        staff_id: int,
        expected_dates: Iterable[datetime.date],
) -> set[datetime.date]:
    """
    Get existing shift dates from the database.

    Keyword Args:
        staff_id: staff id.
        expected_dates: existing shifts within these dates.

    Returns:
        set[datetime.date]: dates of existing shifts.
    """
    return set(
        Shift.objects
        .filter(
            staff_id=staff_id,
            date__in=expected_dates,
            is_test=False,
        )
        .values_list('date', flat=True)
    )


def validate_conflict_shift_dates(
        *,
        staff_id: int,
        expected_dates: Iterable[datetime.date],
) -> None:
    """
    Check if there are any conflicts with existing shifts.

    Keyword Args:
        staff_id: staff id.
        expected_dates: dates of shifts to be created.

    Raises:
        ShiftAlreadyExistsError: If shift already exists on any expected date.
    """
    existing_shift_dates = get_existing_shift_dates(
        staff_id=staff_id,
        expected_dates=expected_dates,
    )
    print(existing_shift_dates, set(expected_dates))
    conflict_dates = set(expected_dates).intersection(existing_shift_dates)
    if conflict_dates:
        raise ShiftAlreadyExistsError(conflict_dates=conflict_dates)


@transaction.atomic
def create_test_shift(
        *,
        staff: Staff,
        date: datetime.date,
) -> ShiftTestCreateResult:
    """
    Create test shift for staff for specific date or refresh test shift.

    Keyword Args:
        staff: staff ORM object.
        date: date of test shift.

    Returns:
        ShiftTestCreateResult object.
    """
    Shift.objects.filter(staff_id=staff.id, is_test=True).delete()
    shift = Shift(
        staff_id=staff.id,
        date=date,
        is_test=True,
    )
    shift.full_clean()
    shift.save()
    return ShiftTestCreateResult(
        staff_id=staff.id,
        staff_full_name=staff.full_name,
        shift_id=shift.id,
        shift_date=shift.date,
    )


class StaffIdAndDateTypedDict(TypedDict):
    staff_id: int
    date: datetime.date


StaffIdAndDate: TypeAlias = tuple[int, datetime.date]


@dataclass(frozen=True, slots=True, kw_only=True)
class ConflictAndNonConflictShifts:
    conflict_shifts: list[StaffIdAndDateTypedDict]
    non_conflict_shifts: list[StaffIdAndDateTypedDict]


def separate_conflict_non_test_shifts(
        shifts: Iterable[StaffIdAndDateTypedDict],
) -> ConflictAndNonConflictShifts:
    expected_shifts: set[StaffIdAndDate] = {
        (shift['staff_id'], shift['date'])
        for shift in shifts
    }
    filters = reduce(
        operator.or_,
        [Q(staff_id=staff_id, date=date) for staff_id, date in expected_shifts]
    )

    existing_shifts: QuerySet[Shift | dict] = (
        Shift.objects
        .filter(filters, is_test=False)
        .values('staff_id', 'date')
    )
    existing_shifts: set[StaffIdAndDate] = {
        (shift['staff_id'], shift['date'])
        for shift in existing_shifts
    }

    conflict_shifts = expected_shifts.intersection(existing_shifts)
    non_conflict_shifts = expected_shifts - conflict_shifts

    return ConflictAndNonConflictShifts(
        conflict_shifts=[
            {'staff_id': staff_id, 'date': date}
            for staff_id, date in conflict_shifts
        ],
        non_conflict_shifts=[
            {'staff_id': staff_id, 'date': date}
            for staff_id, date in non_conflict_shifts
        ],
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class MissingAndExistingStaffIds:
    missing_staff_ids: tuple[int, ...]
    existing_staff_ids: tuple[int, ...]


def separate_staff_by_existence(
        staff_ids: Iterable[int],
) -> MissingAndExistingStaffIds:
    staff_ids = set(staff_ids)
    existing_staff_ids = set(
        Staff.objects
        .filter(id__in=staff_ids)
        .values_list('id', flat=True)
    )
    missing_staff_ids = tuple(staff_ids - existing_staff_ids)
    existing_staff_ids = tuple(existing_staff_ids)
    return MissingAndExistingStaffIds(
        missing_staff_ids=missing_staff_ids,
        existing_staff_ids=existing_staff_ids,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class CreatedExtraShift:
    id: int
    staff_id: int
    date: datetime.date
    created_at: datetime.datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtraShiftsCreateResult:
    missing_staff_ids: tuple[int, ...]
    created_shifts: list[CreatedExtraShift]
    conflict_shifts: list[StaffIdAndDateTypedDict]


@dataclass(frozen=True, slots=True, kw_only=True)
class ShiftExtraCreateInteractor:
    shifts: list[StaffIdAndDateTypedDict]

    def get_shifts_of_staff(
            self,
            staff_ids: Iterable[int],
    ) -> list[StaffIdAndDateTypedDict]:
        staff_ids = set(staff_ids)
        return [
            shift for shift in self.shifts
            if shift['staff_id'] in staff_ids
        ]

    @transaction.atomic
    def execute(self):
        staff_ids = [shift['staff_id'] for shift in self.shifts]
        separated_staff = separate_staff_by_existence(staff_ids)
        shifts_of_existing_staff = self.get_shifts_of_staff(
            separated_staff.existing_staff_ids,
        )
        separated_shifts = separate_conflict_non_test_shifts(
            shifts=shifts_of_existing_staff
        )
        shifts_to_create = [
            Shift(
                staff_id=shift['staff_id'],
                date=shift['date'],
                is_extra=True,
            )
            for shift in separated_shifts.non_conflict_shifts
        ]
        created_shifts = Shift.objects.bulk_create(shifts_to_create)
        created_shifts = [
            CreatedExtraShift(
                id=shift.id,
                staff_id=shift.staff_id,
                date=shift.date,
                created_at=shift.created_at,
            )
            for shift in created_shifts
        ]
        return ExtraShiftsCreateResult(
            created_shifts=created_shifts,
            missing_staff_ids=separated_staff.missing_staff_ids,
            conflict_shifts=separated_shifts.conflict_shifts,
        )


def create_regular_shifts(
        *,
        staff: Staff,
        dates: Iterable[datetime.date],
) -> ShiftsCreateResult:
    """
    Create regular shifts for staff for specific dates.

    Keyword Args:
        staff: staff to create shifts for.
        dates: shift dates to create.

    Raises:
        ShiftAlreadyExistsError: If shift already exists on any date.

    Returns:
        ShiftsCreateResult object.
    """

    validate_conflict_shift_dates(staff_id=staff.id, expected_dates=dates)

    shifts_to_create = [Shift(staff=staff, date=date) for date in dates]
    shifts = Shift.objects.bulk_create(shifts_to_create)

    shifts = [
        ShiftItem(id=shift.id, date=shift.date)
        for shift in shifts
    ]
    return ShiftsCreateResult(
        staff_id=staff.id,
        staff_full_name=staff.full_name,
        shifts=shifts,
    )


def start_shift(
        *,
        shift_id: int,
        car_wash_id: int,
) -> Shift:
    try:
        shift = (
            Shift.objects.select_related('car_wash', 'staff')
            .only('id', 'date', 'car_wash', 'staff')
            .get(id=shift_id)
        )
    except Shift.DoesNotExist:
        raise ShiftNotFoundError

    if shift.is_started:
        raise StaffHasActiveShiftError

    shift.started_at = timezone.now()
    shift.car_wash_id = car_wash_id
    shift.save(update_fields=('started_at', 'car_wash_id'))

    return shift


def ensure_staff_has_no_active_shift(staff_id: int) -> None:
    if Shift.objects.filter(
            staff_id=staff_id,
            started_at__isnull=False,
            finished_at__isnull=True,
    ).exists():
        raise StaffHasActiveShiftError


@dataclass(frozen=True, slots=True, kw_only=True)
class CarWashTransferredCarsSummary:
    car_wash_id: int
    car_wash_name: str
    comfort_cars_count: int
    business_cars_count: int
    vans_count: int
    planned_cars_count: int
    urgent_cars_count: int
    dry_cleaning_count: int
    total_cars_count: int
    refilled_cars_count: int
    not_refilled_cars_count: int
    trunk_vacuum_count: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ShiftSummary:
    staff_id: int
    staff_full_name: str
    shift_id: int
    car_washes: list[CarWashTransferredCarsSummary]


@dataclass(frozen=True, slots=True)
class ShiftFinishResult(ShiftSummary):
    is_first_shift: bool
    finish_photo_file_ids: list[str]


TRUNK_VACUUM_SERVICE_ID: Final[UUID] = UUID(
    '8d263cb9-f11c-456e-b055-ee89655682f1'
)


def compute_trunk_vacuum_count(
        *,
        car_wash_id: int,
        shift_id: int,
) -> int:
    result = (
        CarToWashAdditionalService.objects
        .filter(
            car__car_wash_id=car_wash_id,
            car__shift_id=shift_id,
            service_id=TRUNK_VACUUM_SERVICE_ID,
        )
        .aggregate(count=Sum('count'))
    )
    return result['count'] or 0


def compute_dry_cleaning_items_count(
        *,
        car_wash_id: int,
        shift_id: int,
) -> int:
    result = (
        CarToWashAdditionalService.objects
        .filter(
            car__car_wash_id=car_wash_id,
            car__shift_id=shift_id,
            service__is_dry_cleaning=True,
        )
        .aggregate(count=Sum('count'))
    )
    return result['count'] or 0


class ShiftSummaryInteractor:

    def __init__(self, shift_id: int):
        self.__shift_id = shift_id

    @lru_cache
    def get_shift(self) -> Shift:
        return (
            Shift.objects
            .select_related('staff', 'car_wash')
            .get(id=self.__shift_id)
        )

    def get_cars_to_wash(self) -> QuerySet[CarToWash]:
        return (
            CarToWash.objects
            .select_related('car_wash')
            .filter(shift=self.get_shift())
        )

    def execute(self) -> ShiftSummary:
        shift = self.get_shift()
        cars_to_wash = self.get_cars_to_wash()

        car_wash_id_to_name: dict[int, str] = {
            car_wash['id']: car_wash['name']
            for car_wash in CarWash.objects.values('id', 'name')
        }

        car_wash_id_to_cars = collections.defaultdict(list)
        for car in cars_to_wash:
            car_wash_id_to_cars[car.car_wash_id].append(car)

        car_washes_summaries: list[CarWashTransferredCarsSummary] = []

        for car_wash_id, cars in car_wash_id_to_cars.items():
            wash_type_to_count = collections.defaultdict(int)
            car_class_to_count = collections.defaultdict(int)
            refilled_cars_count = 0

            for car in cars:
                wash_type_to_count[car.wash_type] += 1
                car_class_to_count[car.car_class] += 1
                refilled_cars_count += int(
                    car.is_windshield_washer_refilled
                )

            car_wash_name = car_wash_id_to_name.get(car_wash_id, 'не выбрано')
            total_cars_count = len(cars)
            not_refilled_cars_count = total_cars_count - refilled_cars_count

            dry_cleaning_items_count = compute_dry_cleaning_items_count(
                car_wash_id=car_wash_id,
                shift_id=shift.id,
            )
            trunk_vacuum_count = compute_trunk_vacuum_count(
                car_wash_id=car_wash_id,
                shift_id=shift.id,
            )

            car_wash_transferred_cars_summary = CarWashTransferredCarsSummary(
                car_wash_id=car_wash_id,
                car_wash_name=car_wash_name,
                comfort_cars_count=car_class_to_count[
                    CarToWash.CarType.COMFORT],
                business_cars_count=car_class_to_count[
                    CarToWash.CarType.BUSINESS],
                vans_count=car_class_to_count[CarToWash.CarType.VAN],
                planned_cars_count=wash_type_to_count[
                    CarToWash.WashType.PLANNED],
                urgent_cars_count=wash_type_to_count[
                    CarToWash.WashType.URGENT],
                dry_cleaning_count=dry_cleaning_items_count,
                total_cars_count=total_cars_count,
                refilled_cars_count=refilled_cars_count,
                not_refilled_cars_count=not_refilled_cars_count,
                trunk_vacuum_count=trunk_vacuum_count,
            )
            car_washes_summaries.append(car_wash_transferred_cars_summary)

        return ShiftSummary(
            staff_id=shift.staff.id,
            staff_full_name=shift.staff.full_name,
            shift_id=shift.id,
            car_washes=car_washes_summaries,
        )


class ShiftFinishInteractor:

    def __init__(
            self,
            *,
            shift: Shift,
            shift_summary: ShiftSummary,
            photo_file_ids: Iterable[str],
    ):
        self.__shift = shift
        self.__shift_summary = shift_summary
        self.__photo_file_ids = list(photo_file_ids)

    def save_shift_finish_date(self) -> None:
        if self.__shift.finished_at is not None:
            return

        self.__shift.finished_at = timezone.now()
        self.__shift.save(update_fields=('finished_at',))

    def delete_shift_finish_photos(self) -> None:
        ShiftFinishPhoto.objects.filter(shift_id=self.__shift.id).delete()

    def create_shift_finish_photos(self) -> list[ShiftFinishPhoto]:
        finish_photos = [
            ShiftFinishPhoto(file_id=file_id, shift_id=self.__shift.id)
            for file_id in self.__photo_file_ids
        ]
        return ShiftFinishPhoto.objects.bulk_create(finish_photos)

    def create_result(
            self,
            is_first_shift: bool,
    ) -> ShiftFinishResult:
        return ShiftFinishResult(
            is_first_shift=is_first_shift,
            shift_id=self.__shift_summary.shift_id,
            staff_id=self.__shift_summary.staff_id,
            staff_full_name=self.__shift.staff.full_name,
            car_washes=self.__shift_summary.car_washes,
            finish_photo_file_ids=self.__photo_file_ids,
        )

    @transaction.atomic
    def finish_shift(self) -> ShiftFinishResult:
        is_first_shift = not has_any_finished_shift(self.__shift.staff_id)
        self.save_shift_finish_date()
        self.delete_shift_finish_photos()
        self.create_shift_finish_photos()
        return self.create_result(is_first_shift=is_first_shift)


def get_shifts_by_staff_id(
        *,
        staff_id: int,
        month: int | None,
        year: int | None,
) -> QuerySet[Shift]:
    shifts = Shift.objects.select_related('car_wash').filter(staff_id=staff_id)
    if month is not None:
        shifts = shifts.filter(date__month=month)
    if year is not None:
        shifts = shifts.filter(date__year=year)
    return shifts


def delete_shift_by_id(shift_id: int) -> None:
    deleted_count, _ = Shift.objects.filter(id=shift_id).delete()
    if deleted_count == 0:
        raise ShiftNotFoundError


def ensure_shift_exists(shift_id: int) -> None:
    if not Shift.objects.filter(id=shift_id).exists():
        raise ShiftNotFoundError


def mark_shift_as_rejected_now(
        shift_id: int,
) -> bool:
    updated_count = (
        Shift.objects
        .filter(id=shift_id)
        .update(rejected_at=timezone.now())
    )
    return bool(updated_count)


@dataclass(frozen=True, slots=True, kw_only=True)
class StaffIdAndName:
    id: int
    full_name: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DeadSoulsForMonth:
    month: int
    year: int
    staff_list: list[StaffIdAndName]


def ensure_month_is_available(*, month: int, year: int) -> None:
    if not AvailableDate.objects.filter(month=month, year=year).exists():
        raise MonthNotAvailableError(month=month, year=year)


def map_dict_to_staff_id_and_name(
        staff_list: Iterable[dict],
) -> list[StaffIdAndName]:
    return [
        StaffIdAndName(id=staff['id'], full_name=staff['full_name'])
        for staff in staff_list
    ]


def get_staff_with_one_test_shift(
        *,
        year: int,
        month: int,
) -> list[StaffIdAndName]:
    staff_list = (
        Staff.objects
        .filter(
            banned_at__isnull=True,
            shift__date__year=year,
            shift__date__month=month,
        )
        .annotate(
            test_shift_count=Count('shift', filter=Q(shift__is_test=True)),
            all_shift_count=Count('shift'),
        )
        .filter(
            test_shift_count=1,
            all_shift_count=1,
        )
        .values('id', 'full_name')
    )
    return map_dict_to_staff_id_and_name(staff_list)


def get_staff_with_no_shifts(
        *,
        year: int,
        month: int,
) -> list[StaffIdAndName]:
    staff_list = (
        Staff.objects
        .filter(banned_at__isnull=True)
        .exclude(
            shift__date__year=year,
            shift__date__month=month,
        )
        .distinct('id')
        .values('id', 'full_name')
    )
    return map_dict_to_staff_id_and_name(staff_list)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeadSoulsReadInteractor:
    month: int
    year: int

    def execute(self):
        ensure_month_is_available(month=self.month, year=self.year)

        staff_list = {
            *get_staff_with_no_shifts(month=self.month, year=self.year),
            *get_staff_with_one_test_shift(month=self.month, year=self.year),
        }

        return DeadSoulsForMonth(
            month=self.month,
            year=self.year,
            staff_list=list(staff_list),
        )


def get_staff_ids_with_not_started_shifts_for_today() -> set[int]:
    return set(
        Shift.objects
        .filter(
            date=get_current_shift_date(),
            started_at__isnull=True,
            rejected_at__isnull=True,
        )
        .values_list('staff_id', flat=True)
    )
