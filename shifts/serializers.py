from rest_framework import serializers

from car_washes.models import CarWash, CarWashService
from shifts.models import (
    AvailableDate,
    CarToWash,
    CarToWashAdditionalService,
    Shift,
)

__all__ = (
    'AdditionalServiceSerializer',
    'CarToWashCreateInputSerializer',
    'CarToWashCreateOutputSerializer',
    'AvailableDateSerializer',
    'DateSerializer',
    'ShiftListForSpecificDateOutputSerializer',
    'ShiftRetrieveOutputSerializer',
    'StaffCurrentShiftRetrieveOutputSerializer',
    'ShiftListInputSerializer',
    'ShiftListOutputSerializer',
    'ShiftCreateInputSerializer',
    'UpdateCarToWashInputSerializer',
    'CarToWashDetailOutputSerializer',
    'CarToWashAdditionalServiceSerializer',
)


class DateSerializer(serializers.Serializer):
    date = serializers.DateField()


class AdditionalServiceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    count = serializers.IntegerField(default=1)


class CarToWashCreateInputSerializer(serializers.ModelSerializer):
    staff_id = serializers.IntegerField()
    additional_services = AdditionalServiceSerializer(many=True, default=list)

    class Meta:
        model = CarToWash
        fields = (
            'staff_id',
            'number',
            'car_class',
            'wash_type',
            'windshield_washer_refilled_bottle_percentage',
            'additional_services',
        )


class CarToWashCreateOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    shift_id = serializers.IntegerField()
    number = serializers.CharField()
    class_type = serializers.CharField()
    wash_type = serializers.CharField()
    windshield_washer_refilled_bottle_percentage = serializers.IntegerField()
    car_wash_id = serializers.IntegerField()
    additional_services = AdditionalServiceSerializer(many=True)


class AvailableDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableDate
        fields = ('id', 'month', 'year')


class ShiftListForSpecificDateOutputSerializer(
    serializers.ModelSerializer,
):
    class Meta:
        model = Shift
        fields = (
            'id',
            'date',
            'staff',
            'is_started',
            'is_finished',
            'created_at',
        )
        depth = 1


class ShiftRetrieveOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = (
            'id',
            'date',
            'car_wash',
            'staff',
            'is_started',
            'is_finished',
            'created_at',
        )
        depth = 1


class StaffCurrentShiftRetrieveOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = (
            'id',
            'date',
            'car_wash',
            'staff',
            'is_started',
            'is_finished',
            'created_at',
        )
        depth = 1


class ShiftListInputSerializer(serializers.Serializer):
    date_from = serializers.DateField(default=None, allow_null=True)
    date_to = serializers.DateField(default=None, allow_null=True)
    staff_ids = serializers.ListField(
        child=serializers.IntegerField(),
        default=None,
        allow_null=True,
        allow_empty=False,
    )
    limit = serializers.IntegerField(default=10, min_value=1, max_value=1000)
    offset = serializers.IntegerField(default=0, min_value=0)


class ShiftListOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = (
            'id',
            'date',
            'car_wash',
            'staff',
            'is_started',
            'is_finished',
            'created_at',
        )
        depth = 1


class ShiftCreateInputSerializer(serializers.Serializer):
    staff_id = serializers.IntegerField()
    dates = serializers.ListField(child=serializers.DateField())
    immediate_start = serializers.BooleanField(default=False)
    car_wash_id = serializers.IntegerField(default=None, allow_null=True)
    is_extra = serializers.BooleanField(default=False)

    def validate(self, data: dict) -> dict:
        if data['immediate_start'] and 'car_wash_id' not in data:
            raise serializers.ValidationError(
                'car_wash_id is required for immediate_start',
            )
        return data


class CarToWashAdditionalServiceSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='service_id')

    class Meta:
        model = CarToWashAdditionalService
        fields = ['id', 'count']


class CarWashSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarWash
        fields = [
            'id',
            'name',
        ]


class CarToWashDetailOutputSerializer(serializers.ModelSerializer):
    class_type = serializers.CharField(source='car_class')
    car_wash = CarWashSerializer(allow_null=True)
    additional_services = CarToWashAdditionalServiceSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = CarToWash
        fields = [
            'id',
            'number',
            'wash_type',
            'class_type',
            'windshield_washer_refilled_bottle_percentage',
            'created_at',
            'additional_services',
            'car_wash',
        ]


class UpdateCarToWashInputSerializer(serializers.Serializer):
    additional_services = AdditionalServiceSerializer(many=True, default=list)
