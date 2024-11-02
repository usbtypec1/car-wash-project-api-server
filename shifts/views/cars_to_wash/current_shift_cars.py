from rest_framework import serializers, views
from rest_framework.response import Response
from django.db.models import Prefetch

from shifts.models import CarToWash, CarToWashAdditionalService



class CarToWashAdditionalServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarToWashAdditionalService
        fields = ['name', 'count']


class CarToWashSerializer(serializers.ModelSerializer):
    additional_services = CarToWashAdditionalServiceSerializer(
        source='cartowashadditionalservice_set',
        many=True,
        read_only=True
    )

    class Meta:
        model = CarToWash
        fields = [
            'id',
            'number',
            'car_class',
            'wash_type',
            'windshield_washer_refilled_bottle_percentage',
            'created_at',
            'additional_services',
        ]


class CarToWashListApi(views.APIView):
    def get(self, request, *args, **kwargs):
        queryset = CarToWash.objects.all().prefetch_related(
            Prefetch(
                'cartowashadditionalservice_set',
                queryset=CarToWashAdditionalService.objects.all(),
                to_attr='additional_services_prefetched'
            )
        )

        serializer = CarToWashSerializer(queryset, many=True)
        return Response({'cars': serializer.data})