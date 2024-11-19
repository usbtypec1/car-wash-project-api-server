from rest_framework import serializers

from car_washes.models import CarWash, CarWashService

__all__ = (
    'CarWashListOutputSerializer',
    'CarWashRetrieveOutputSerializer',
    'CarWashServiceSerializer',
    'CarWashCreateOutputSerializer',
    'CarWashCreateInputSerializer',
    'CarWashServicesInputSerializer',
    'CarWashUpdateInputSerializer',
    'CarWashServicePriceUpsertInputSerializer',
    'CarWashServicePriceUpsertOutputSerializer',
)


class CarWashListOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarWash
        fields = ('id', 'name', 'created_at', 'updated_at')


class CarWashServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarWashService
        fields = ('id', 'name', 'price', 'created_at', 'updated_at')


class CarWashRetrieveOutputSerializer(serializers.ModelSerializer):
    services = CarWashServiceSerializer(many=True)

    class Meta:
        model = CarWash
        fields = ('id', 'name', 'created_at', 'updated_at', 'services')


class CarWashUpdateInputSerializer(serializers.Serializer):
    class Meta:
        model = CarWash
        fields = ('name',)


class CarWashCreateInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)


class CarWashCreateOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarWash
        fields = ('id', 'name', 'created_at', 'updated_at')


class CarWashServicesInputSerializer(serializers.Serializer):
    depth = serializers.IntegerField(
        default=2,
        min_value=0,
        max_value=5,
    )
    flat = serializers.BooleanField(default=False)


class CarWashServicePriceUpsertInputSerializer(serializers.Serializer):
    price = serializers.IntegerField(min_value=1, max_value=1_000_000)


class CarWashServicePriceUpsertOutputSerializer(serializers.Serializer):
    car_wash_id = serializers.IntegerField()
    service_id = serializers.UUIDField()
    price = serializers.IntegerField()
    updated_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()
