"""app/core/dependencies/search.py — Factory use case Search."""
from app.modules.hotel.infrastructure.repositories.hotel_repository_impl      import DjangoHotelRepository
from app.modules.hotel.infrastructure.repositories.room_repository_impl       import DjangoRoomRepository
from app.modules.booking.infrastructure.repositories.booking_repository_impl  import DjangoBookingRepository
from app.modules.search.domain.use_cases.search_hotels import SearchHotelsUseCase


def get_search_hotels_uc() -> SearchHotelsUseCase:
    return SearchHotelsUseCase(DjangoHotelRepository(), DjangoRoomRepository(), DjangoBookingRepository())
