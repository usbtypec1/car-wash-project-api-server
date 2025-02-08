from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from economics.models import Penalty
from economics.selectors import get_penalties_page
from economics.serializers import (
    PenaltyCreateInputSerializer,
    PenaltyCreateOutputSerializer,
    PenaltyListInputSerializer,
    PenaltyListOutputSerializer,
)
from economics.services.penalties import create_penalty
from shifts.services.shifts import ensure_shift_exists
from staff.selectors import ensure_staff_exists

__all__ = ('PenaltyListCreateApi',)


class PenaltyListCreateApi(APIView):
    def get(self, request: Request) -> Response:
        serializer = PenaltyListInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        serialized_data: dict = serializer.validated_data

        staff_ids: list[int] | None = serialized_data['staff_ids']
        limit: int = serialized_data['limit']
        offset: int = serialized_data['offset']

        penalties_page = get_penalties_page(
            staff_ids=staff_ids,
            limit=limit,
            offset=offset,
        )

        serializer = PenaltyListOutputSerializer(penalties_page)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = PenaltyCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serialized_data = serializer.validated_data

        shift_id: int = serialized_data['shift_id']
        reason: str = serialized_data['reason']
        amount: int | None = serialized_data['amount']

        ensure_shift_exists(shift_id)
        penalty = create_penalty(
            shift_id=shift_id,
            reason=reason,
            amount=amount,
        )

        serializer = PenaltyCreateOutputSerializer(penalty)
        return Response(serializer.data, status.HTTP_201_CREATED)
