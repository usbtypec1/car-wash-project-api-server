import datetime
from collections.abc import Iterable
from dataclasses import dataclass

from django.core.paginator import Paginator

from staff.exceptions import StaffNotFoundError
from staff.models import AdminStaff, Staff

__all__ = (
    'get_staff_by_id',
    'get_all_staff',
    'ensure_staff_exists',
    'get_staff',
    'StaffItem',
    'get_admin_ids',
    'StaffListPage',
)


@dataclass(frozen=True, slots=True)
class StaffItem:
    id: int
    full_name: str
    car_sharing_phone_number: str
    console_phone_number: str
    created_at: datetime.datetime
    banned_at: datetime.datetime | None


def get_admin_ids() -> tuple[int, ...]:
    return tuple(AdminStaff.objects.values_list('id', flat=True))


def get_staff_by_id(staff_id: int) -> Staff:
    try:
        return Staff.objects.get(id=staff_id)
    except Staff.DoesNotExist:
        raise StaffNotFoundError


def ensure_staff_exists(staff_id: int) -> None:
    if not Staff.objects.filter(id=staff_id).exists():
        raise StaffNotFoundError


@dataclass(frozen=True, slots=True)
class StaffListItem:
    id: int
    full_name: str
    car_sharing_phone_number: str
    console_phone_number: str
    created_at: datetime.datetime
    banned_at: datetime.datetime | None
    last_activity_at: datetime.datetime


@dataclass(frozen=True, slots=True)
class StaffListPage:
    staff: list[StaffListItem]
    is_end_of_list_reached: bool
    total_count: int


def map_staff_list(staff_list: Iterable[dict]) -> list[StaffListItem]:
    return [
        StaffListItem(
            id=staff['id'],
            full_name=staff['full_name'],
            car_sharing_phone_number=staff['car_sharing_phone_number'],
            console_phone_number=staff['console_phone_number'],
            created_at=staff['created_at'],
            banned_at=staff['banned_at'],
            last_activity_at=staff['last_activity_at'],
        )
        for staff in staff_list
    ]


def get_all_staff(
        *,
        order_by: str,
        include_banned: bool,
        limit: int,
        offset: int,
) -> StaffListPage:
    staff_list = (
        Staff.objects
        .order_by(order_by)
        .values(
            'id',
            'full_name',
            'car_sharing_phone_number',
            'console_phone_number',
            'banned_at',
            'created_at',
            'last_activity_at',
        )
    )
    if not include_banned:
        staff_list = staff_list.filter(banned_at__isnull=True)

    paginator = Paginator(staff_list, limit)
    page_number = (offset // limit) + 1
    current_page = paginator.get_page(page_number)

    is_end_of_list_reached = not current_page.has_next()

    return StaffListPage(
        staff=map_staff_list(current_page.object_list),
        is_end_of_list_reached=is_end_of_list_reached,
        total_count=paginator.count,
    )


def get_staff(
        *,
        staff_ids: Iterable[int] | None = None,
) -> list[StaffItem]:
    staff_list = Staff.objects.all()

    if staff_ids is not None:
        staff_list = staff_list.filter(id__in=staff_ids)

    staff_list = staff_list.values(
        'id',
        'full_name',
        'car_sharing_phone_number',
        'console_phone_number',
        'created_at',
        'banned_at',
    ).order_by('full_name')

    return [
        StaffItem(
            id=staff['id'],
            full_name=staff['full_name'],
            car_sharing_phone_number=staff['car_sharing_phone_number'],
            console_phone_number=staff['console_phone_number'],
            created_at=staff['created_at'],
            banned_at=staff['banned_at'],
        )
        for staff in staff_list
    ]
