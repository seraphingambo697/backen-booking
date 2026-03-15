"""app/core/dependencies/payment.py — Factories use cases Payment."""
from app.modules.payment.infrastructure.repositories.payment_repository_impl import DjangoPaymentRepository
from app.modules.payment.infrastructure.external.mock_payment_gateway         import MockPaymentGateway
from app.modules.booking.infrastructure.repositories.booking_repository_impl  import DjangoBookingRepository
from app.modules.payment.domain.use_cases.process_payment import ProcessPaymentUseCase
from app.modules.payment.domain.use_cases.get_payment     import GetPaymentUseCase
from app.modules.payment.domain.use_cases.refund_payment  import RefundPaymentUseCase


def _gateway():       return MockPaymentGateway()
def _payment_repo():  return DjangoPaymentRepository()
def _booking_repo():  return DjangoBookingRepository()


def get_process_payment_uc() -> ProcessPaymentUseCase:
    return ProcessPaymentUseCase(_payment_repo(), _booking_repo(), _gateway())

def get_payment_uc() -> GetPaymentUseCase:
    return GetPaymentUseCase(_payment_repo())

def get_refund_payment_uc() -> RefundPaymentUseCase:
    return RefundPaymentUseCase(_payment_repo(), _booking_repo(), _gateway())
