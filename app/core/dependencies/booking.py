"""app/core/dependencies/booking.py — Factories use cases Booking."""
from app.modules.booking.infrastructure.repositories.booking_repository_impl import DjangoBookingRepository
from app.modules.hotel.infrastructure.repositories.room_repository_impl       import DjangoRoomRepository
from app.modules.booking.domain.use_cases.create_booking    import CreateBookingUseCase
from app.modules.booking.domain.use_cases.get_booking       import GetBookingUseCase, ListBookingsUseCase
from app.modules.booking.domain.use_cases.cancel_booking    import CancelBookingUseCase
from app.modules.booking.domain.use_cases.confirm_booking   import ConfirmBookingUseCase
from app.modules.booking.domain.use_cases.complete_booking  import CompleteBookingUseCase
from app.modules.booking.domain.use_cases.check_availability import CheckAvailabilityUseCase


def get_create_booking_uc() -> CreateBookingUseCase:
    return CreateBookingUseCase(DjangoBookingRepository(), DjangoRoomRepository())

def get_booking_uc()            -> GetBookingUseCase:        return GetBookingUseCase(DjangoBookingRepository())
def get_list_bookings_uc()      -> ListBookingsUseCase:      return ListBookingsUseCase(DjangoBookingRepository())
def get_cancel_booking_uc()     -> CancelBookingUseCase:     return CancelBookingUseCase(DjangoBookingRepository())
def get_confirm_booking_uc()    -> ConfirmBookingUseCase:    return ConfirmBookingUseCase(DjangoBookingRepository())
def get_complete_booking_uc()   -> CompleteBookingUseCase:   return CompleteBookingUseCase(DjangoBookingRepository())

def get_check_availability_uc() -> CheckAvailabilityUseCase:
    return CheckAvailabilityUseCase(DjangoBookingRepository(), DjangoRoomRepository())
