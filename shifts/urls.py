from django.urls import include, path
from rest_framework.routers import DefaultRouter

from shifts.views import (
    AvailableDateApi,
    CarsToWashCountByEachStaffApi,
    CarsWithoutWindshieldWasherApi,
    CarToWashCreateApi,
    CarToWashListApi,
    CurrentShiftCarWashUpdateApi,
    ReportApi,
    RetrieveUpdateCarsToWashApi,
    ShiftCreateApi,
    ShiftFinishApi,
    ShiftLastCreatedDateListApi,
    ShiftListApi,
    ShiftListForSpecificDateApi,
    ShiftRetrieveDeleteApi,
    ShiftStartApi,
    StaffCurrentShiftRetrieveApi,
    StaffShiftListApi,
    ShiftRetrieveApi,
)

router = DefaultRouter()
router.register(
    r'available-dates',
    AvailableDateApi,
    basename='available-date',
)

app_name = 'shifts'
urlpatterns = [
    path(
        r'',
        ShiftListApi.as_view(),
        name='list',
    ),
    path(
        'specific-date/',
        ShiftListForSpecificDateApi.as_view(),
        name='specific-date',
    ),
    path(
        r'reports/staff/<int:staff_id>/',
        ReportApi.as_view(),
        name='report',
    ),
    path(
        r'staff/<int:staff_id>/last-created/',
        ShiftLastCreatedDateListApi.as_view(),
        name='last-created',
    ),
    path(
        r'create/',
        ShiftCreateApi.as_view(),
        name='create',
    ),
    path(
        r'<int:shift_id>/',
        ShiftRetrieveDeleteApi.as_view(),
        name='delete',
    ),
    path(
        r'start/',
        ShiftStartApi.as_view(),
        name='start',
    ),
    path(
        r'finish/',
        ShiftFinishApi.as_view(),
        name='finish',
    ),
    path(
        r'current/<int:staff_id>/car-washes/',
        CurrentShiftCarWashUpdateApi.as_view(),
        name='current-shift-car-wash',
    ),
    path(
        r'current/<int:staff_id>/',
        StaffCurrentShiftRetrieveApi.as_view(),
        name='current-shift',
    ),
    path(
        r'staff/<int:staff_id>/',
        StaffShiftListApi.as_view(),
    ),
    path(
        r'cars/<int:car_id>/',
        RetrieveUpdateCarsToWashApi.as_view(),
        name='car-update',
    ),
    path(
        r'cars/',
        CarToWashCreateApi.as_view(),
        name='car-create',
    ),
    path(
        r'cars/staff/<int:staff_id>/',
        CarToWashListApi.as_view(),
        name='car-list',
    ),
    path(
        r'cars/count-by-staff/',
        CarsToWashCountByEachStaffApi.as_view(),
        name='car-count-by-staff',
    ),
    path(
        r'cars/without-windshield-washer/',
        CarsWithoutWindshieldWasherApi.as_view(),
        name='car-without-windshield-washer',
    ),
    path(r'<int:shift_id>/', ShiftRetrieveApi.as_view(), name='retrieve'),
    path(r'', include(router.urls)),
]
