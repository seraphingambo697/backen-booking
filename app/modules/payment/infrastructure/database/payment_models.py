import uuid
from django.conf import settings
from django.db import models
from app.modules.booking.infrastructure.database.booking_models import BookingModel


class PaymentModel(models.Model):
    class Meta:
        app_label = "payment_infrastructure"
        db_table  = "payments"
        ordering  = ["-created_at"]

    class Status(models.TextChoices):
        PENDING   = "PENDING",   "En attente"
        SUCCEEDED = "SUCCEEDED", "Réussi"
        FAILED    = "FAILED",    "Échoué"
        REFUNDED  = "REFUNDED",  "Remboursé"

    class Method(models.TextChoices):
        CARD          = "CARD",          "Carte"
        PAYPAL        = "PAYPAL",        "PayPal"
        BANK_TRANSFER = "BANK_TRANSFER", "Virement"

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking        = models.ForeignKey(BookingModel, on_delete=models.CASCADE, related_name="payments")
    user           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    currency       = models.CharField(max_length=3, default="EUR")
    status         = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    method         = models.CharField(max_length=20, choices=Method.choices, default=Method.CARD)
    gateway_ref    = models.CharField(max_length=100, blank=True, default="")
    failure_reason = models.TextField(blank=True, default="")
    refunded_at    = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def __str__(self): return f"Payment {self.id} — {self.status} — {self.amount} {self.currency}"
