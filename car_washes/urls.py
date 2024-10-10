from django.urls import path

from car_washes.views import (
    CarWashListCreateApi,
    CarWashRetrieveUpdateDeleteApi,
)

urlpatterns = [
    path(r'', CarWashListCreateApi.as_view(), name='car-wash-list-create'),
    path(
        r'<int:car_wash_id>/',
        CarWashRetrieveUpdateDeleteApi.as_view(),
        name='car-wash-detail-update-delete',
    ),
]
