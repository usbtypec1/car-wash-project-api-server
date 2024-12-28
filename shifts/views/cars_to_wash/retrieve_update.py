from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from shifts.exceptions import CarToWashNotFoundError
from shifts.models import CarToWash
from shifts.serializers import (
    CarToWashDetailOutputSerializer,
    UpdateCarToWashInputSerializer,
)
from shifts.services.cars_to_wash import update_car_to_wash_additional_services

__all__ = ('RetrieveUpdateCarsToWashApi',)


class RetrieveUpdateCarsToWashApi(APIView):
    def get(self, request: Request, car_id: int) -> Response:
        try:
            car = (
            CarToWash.objects.select_related('car_wash')
            .prefetch_related('additional_services')
            .get(id=car_id)
        )
        except CarToWash.DoesNotExist:
            raise CarToWashNotFoundError(car_to_wash_id=car_id)

        serializer = CarToWashDetailOutputSerializer(car)
        return Response(serializer.data)

    def patch(self, request: Request, car_id: int) -> Response:
        serializer = UpdateCarToWashInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serialized_data = serializer.validated_data

        additional_services: list[dict] = serialized_data['additional_services']

        update_car_to_wash_additional_services(
            car_id=car_id,
            additional_services=additional_services,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
