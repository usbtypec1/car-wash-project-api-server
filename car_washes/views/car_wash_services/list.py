from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from car_washes.selectors import get_root_car_wash_services
from car_washes.serializers import CarWashServicesInputSerializer

__all__ = ('CarWashServicesApi',)


class CarWashServicesApi(APIView):

    def get(self, request: Request) -> Response:
        serializer = CarWashServicesInputSerializer(
            data=request.query_params,
        )
        serializer.is_valid(raise_exception=True)
        serialized_data = serializer.data

        depth: int = serialized_data['depth']
        car_wash_id: int | None = serialized_data['car_wash_id']

        car_wash_services = get_root_car_wash_services(
            car_wash_id=car_wash_id,
            depth=depth,
        )
        return Response({'services': car_wash_services})
