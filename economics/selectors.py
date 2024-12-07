from economics.models import Penalty, StaffServicePrice
from shifts.exceptions import StaffServicePriceNotFoundError
from shifts.models import CarToWash

__all__ = ('compute_car_transfer_price', 'compute_staff_penalties_count')


def compute_car_transfer_price(
        *,
        class_type: str,
        wash_type: str,
        is_extra_shift: bool,
) -> int:
    if wash_type == CarToWash.WashType.URGENT:
        service_name = StaffServicePrice.ServiceType.URGENT_CAR_WASH
    else:
        if is_extra_shift:
            service_name = (
                StaffServicePrice.ServiceType.CAR_TRANSPORTER_EXTRA_SHIFT
            )
        else:
            car_class_type_to_service_name: dict[str, str] = {
                CarToWash.CarType.COMFORT:
                    StaffServicePrice.ServiceType.COMFORT_CLASS_CAR_TRANSFER,
                CarToWash.CarType.BUSINESS:
                    StaffServicePrice.ServiceType.BUSINESS_CLASS_CAR_TRANSFER,
                CarToWash.CarType.VAN:
                    StaffServicePrice.ServiceType.VAN_TRANSFER,
            }
            service_name = car_class_type_to_service_name[class_type]

    try:
        staff_service_price = StaffServicePrice.objects.get(
            service=service_name
        )
    except StaffServicePrice.DoesNotExist:
        raise StaffServicePriceNotFoundError
    return staff_service_price.price


def compute_staff_penalties_count(
        *,
        staff_id: int,
        reason: str,
) -> int:
    """
    Get count of penalties that staff member has with specific reason.

    Args:
        staff_id: staff member's ID.
        reason: reason of penalties.

    Returns:
        Penalties count.
    """
    return Penalty.objects.filter(staff_id=staff_id, reason=reason).count()
