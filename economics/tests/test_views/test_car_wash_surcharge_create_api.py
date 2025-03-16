import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from car_washes.tests.factories import CarWashFactory


@pytest.mark.django_db
def test_car_wash_surcharge_create_api_success():
    car_wash = CarWashFactory()
    client = APIClient()
    url = reverse("economics:car-wash-surcharge-list-create")
    data = {
        "car_wash_id": car_wash.id,
        "reason": "some reason",
        "amount": 1000,
        "date": "2025-01-01",
    }

    response = client.post(url, data=data, format="json")
    response_data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert response_data == {
        "id": response_data["id"],
        "car_wash_id": car_wash.id,
        "reason": "some reason",
        "amount": 1000,
        "date": "2025-01-01",
        "created_at": response_data["created_at"],
    }


@pytest.mark.django_db
def test_car_wash_surcharge_create_car_wash_not_found():
    client = APIClient()
    url = reverse("economics:car-wash-surcharge-list-create")
    data = {
        "car_wash_id": 5345345,
        "reason": "some reason",
        "amount": 1000,
        "date": "2025-01-01",
    }

    response = client.post(url, data=data, format="json")
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data["type"] == "client_error"
    assert response_data["errors"][0]["code"] == "car_wash_not_found"
