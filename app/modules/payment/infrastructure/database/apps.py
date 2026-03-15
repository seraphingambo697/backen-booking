from django.apps import AppConfig
class PaymentInfraConfig(AppConfig):
    name  = "app.modules.payment.infrastructure.database"
    label = "payment_infrastructure"
    verbose_name = "Payment Infrastructure"
