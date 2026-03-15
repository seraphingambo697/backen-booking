from typing import List, Optional
from app.modules.payment.domain.entities.payment import Payment, PaymentStatus, PaymentMethod
from app.modules.payment.infrastructure.database.payment_models import PaymentModel
from app.shared.infrastructure.database.base_repository_impl import BaseDjangoRepository


class DjangoPaymentRepository(BaseDjangoRepository[Payment, PaymentModel]):
    model_class = PaymentModel
    entity_name = "Payment"

    def find_by_booking(self, booking_id: str) -> List[Payment]:
        return [self._to_entity(m) for m in PaymentModel.objects.filter(booking_id=booking_id)]

    def _to_entity(self, m: PaymentModel) -> Payment:
        p = Payment.__new__(Payment)
        object.__setattr__(p, "id",             str(m.id))
        object.__setattr__(p, "booking_id",     str(m.booking_id))
        object.__setattr__(p, "user_id",        str(m.user_id))
        object.__setattr__(p, "amount",         float(m.amount))
        object.__setattr__(p, "currency",       m.currency)
        object.__setattr__(p, "status",         PaymentStatus(m.status))
        object.__setattr__(p, "method",         PaymentMethod(m.method))
        object.__setattr__(p, "gateway_ref",    m.gateway_ref)
        object.__setattr__(p, "failure_reason", m.failure_reason)
        object.__setattr__(p, "refunded_at",    m.refunded_at)
        object.__setattr__(p, "created_at",     m.created_at)
        object.__setattr__(p, "updated_at",     m.updated_at)
        return p

    def _to_model_data(self, e: Payment) -> dict:
        return {
            "booking_id": e.booking_id, "user_id": e.user_id,
            "amount": e.amount, "currency": e.currency,
            "status": e.status.value, "method": e.method.value,
            "gateway_ref": e.gateway_ref, "failure_reason": e.failure_reason,
            "refunded_at": e.refunded_at,
        }
