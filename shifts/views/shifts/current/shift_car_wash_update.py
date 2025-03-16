from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from car_washes.models import CarWash
from car_washes.selectors import get_car_wash_by_id
from shifts.selectors import get_staff_current_shift
from shifts.services.cars_to_wash import update_shift_car_wash
from staff.services import update_last_activity_time

__all__ = ("CurrentShiftCarWashUpdateApi",)


class CurrentShiftCarWashUpdateInputSerializer(serializers.Serializer):
    car_wash_id = serializers.IntegerField()


class CurrentShiftCarWashUpdateOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarWash
        fields = ("id", "name")


class CurrentShiftCarWashUpdateApi(APIView):
    def patch(self, request: Request, staff_id: int) -> Response:
        serializer = CurrentShiftCarWashUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serialized_data = serializer.data
        car_wash_id: int = serialized_data["car_wash_id"]

        shift = get_staff_current_shift(staff_id)
        car_wash = get_car_wash_by_id(car_wash_id)
        update_shift_car_wash(
            shift=shift,
            car_wash_id=car_wash.id,
        )

        update_last_activity_time(staff_id=shift.staff_id)

        serializer = CurrentShiftCarWashUpdateOutputSerializer(car_wash)
        return Response(serializer.data)
