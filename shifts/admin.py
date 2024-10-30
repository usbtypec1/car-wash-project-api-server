from django.contrib import admin

from shifts.models import Shift, CarToWash, CarToWashAdditionalService


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    pass


@admin.register(CarToWash)
class CarToWashAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)


@admin.register(CarToWashAdditionalService)
class CarToWashAdditionalServiceAdmin(admin.ModelAdmin):
    pass
