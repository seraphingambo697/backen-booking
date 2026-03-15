import uuid
from django.conf import settings
from django.db import models
from app.modules.hotel.infrastructure.database.hotel_models import HotelModel
from app.modules.booking.infrastructure.database.booking_models import BookingModel


class ReviewModel(models.Model):
    class Meta:
        app_label = "review_infrastructure"
        db_table  = "reviews"
        unique_together = [["user", "booking"]]
        ordering  = ["-created_at"]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    hotel      = models.ForeignKey(HotelModel,   on_delete=models.CASCADE, related_name="reviews")
    booking    = models.ForeignKey(BookingModel, on_delete=models.CASCADE, related_name="reviews")
    rating     = models.IntegerField()
    title      = models.CharField(max_length=200, blank=True, default="")
    comment    = models.TextField(blank=True, default="")
    is_visible = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return f"Review {self.rating}★ — {self.hotel.name}"
