"""Payment endpoints"""
from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from app.core.dependencies import get_process_payment_uc, get_payment_uc, get_refund_payment_uc
from app.modules.payment.domain.use_cases.process_payment import (
    ProcessPaymentInput, GetPaymentInput, RefundPaymentInput,
)
from app.modules.payment.presentation.schemas.payment_schemas import (
    PaymentResponseSerializer, ProcessPaymentRequestSerializer,
)
from app.modules.user.presentation.api.dependencies import get_current_user
from app.shared.presentation.responses import created, success


def _p(payment):
    return PaymentResponseSerializer(payment).data


class PayBookingView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ProcessPaymentRequestSerializer,
        responses={201: PaymentResponseSerializer},
        summary="Payer une réservation (mock)",
        tags=["Payments"],
    )
    def post(self, request):
        user = get_current_user(request)
        s    = ProcessPaymentRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d    = s.validated_data
        payment = get_process_payment_uc().execute(ProcessPaymentInput(
            booking_id=str(d["booking_id"]),
            user_id=user.id,
            method=d["method"],
        ))
        return created(_p(payment))


class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: PaymentResponseSerializer},
        summary="Détail d'un paiement",
        tags=["Payments"],
    )
    def get(self, request, payment_id: str):
        user    = get_current_user(request)
        payment = get_payment_uc().execute(
            GetPaymentInput(payment_id=payment_id, requester_id=user.id)
        )
        return success(_p(payment))


class RefundView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: PaymentResponseSerializer},
        summary="Rembourser une réservation",
        tags=["Payments"],
    )
    def post(self, request, booking_id: str):
        user    = get_current_user(request)
        payment = get_refund_payment_uc().execute(RefundPaymentInput(
            booking_id=booking_id,
            requester_id=user.id,
            is_admin=user.is_admin,
        ))
        return success(_p(payment))


urlpatterns = [
    path("pay/",                     PayBookingView.as_view(),    name="payment-pay"),
    path("<str:payment_id>/",        PaymentDetailView.as_view(), name="payment-detail"),
    path("refund/<str:booking_id>/", RefundView.as_view(),        name="payment-refund"),
]
