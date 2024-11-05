from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from shifts.selectors import get_active_shift
from shifts.serializers import CarToWashCreateInputSerializer
from shifts.services.cars_to_wash import create_car_to_wash

__all__ = ('CarToWashCreateApi',)


class CarToWashCreateApi(APIView):

    def post(self, request: Request) -> Response:
        serializer = CarToWashCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serialized_data = serializer.data

        staff_id: int = serialized_data["staff_id"]
        number: str = serialized_data["number"]
        car_class: str = serialized_data["car_class"]
        wash_type: str = serialized_data["wash_type"]
        windshield_washer_refilled_bottle_percentage: int = serialized_data[
            "windshield_washer_refilled_bottle_percentage"
        ]
        additional_services = serializer.validated_data["additional_services"]

        shift = get_active_shift(staff_id)

        create_car_to_wash(
            shift=shift,
            number=number,
            car_class=car_class,
            wash_type=wash_type,
            windshield_washer_refilled_bottle_percentage=(
                windshield_washer_refilled_bottle_percentage
            ),
            additional_services=additional_services,
        )
        return Response(status=status.HTTP_201_CREATED)
