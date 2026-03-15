"""app/core/dependencies/hotel.py — Factories use cases Hotel & Room."""
from app.modules.hotel.infrastructure.repositories.hotel_repository_impl import DjangoHotelRepository
from app.modules.hotel.infrastructure.repositories.room_repository_impl  import DjangoRoomRepository
from app.modules.hotel.domain.use_cases.create_hotel  import CreateHotelUseCase
from app.modules.hotel.domain.use_cases.get_hotel     import GetHotelUseCase, ListHotelsUseCase
from app.modules.hotel.domain.use_cases.update_hotel  import UpdateHotelUseCase
from app.modules.hotel.domain.use_cases.delete_hotel  import DeleteHotelUseCase
from app.modules.hotel.domain.use_cases.manage_rooms  import (
    CreateRoomUseCase, GetRoomUseCase, ListRoomsUseCase, UpdateRoomUseCase,
)


def get_create_hotel_uc() -> CreateHotelUseCase:  return CreateHotelUseCase(DjangoHotelRepository())
def get_hotel_uc()         -> GetHotelUseCase:     return GetHotelUseCase(DjangoHotelRepository())
def get_list_hotels_uc()   -> ListHotelsUseCase:   return ListHotelsUseCase(DjangoHotelRepository())
def get_update_hotel_uc()  -> UpdateHotelUseCase:  return UpdateHotelUseCase(DjangoHotelRepository())
def get_delete_hotel_uc()  -> DeleteHotelUseCase:  return DeleteHotelUseCase(DjangoHotelRepository())

def get_create_room_uc() -> CreateRoomUseCase:
    return CreateRoomUseCase(DjangoRoomRepository(), DjangoHotelRepository())

def get_room_uc()         -> GetRoomUseCase:   return GetRoomUseCase(DjangoRoomRepository())
def get_list_rooms_uc()   -> ListRoomsUseCase: return ListRoomsUseCase(DjangoRoomRepository())
def get_update_room_uc()  -> UpdateRoomUseCase: return UpdateRoomUseCase(DjangoRoomRepository())
