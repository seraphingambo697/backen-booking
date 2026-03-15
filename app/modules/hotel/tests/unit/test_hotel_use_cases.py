"""
Tests unitaires des use cases Hotel — repositories mockés.
"""
from unittest.mock import MagicMock, patch
import pytest

from app.core.exceptions import AuthorizationError, EntityNotFoundError
from app.modules.hotel.domain.entities.hotel import Hotel, HotelStatus, Room, RoomType
from app.modules.hotel.domain.use_cases.create_hotel import CreateHotelInput, CreateHotelUseCase
from app.modules.hotel.domain.use_cases.get_hotel    import GetHotelInput, GetHotelUseCase
from app.modules.hotel.domain.use_cases.update_hotel import UpdateHotelInput, UpdateHotelUseCase
from app.modules.hotel.domain.use_cases.delete_hotel import DeleteHotelInput, DeleteHotelUseCase
from app.modules.hotel.domain.use_cases.manage_rooms import (
    CreateRoomInput, CreateRoomUseCase,
    GetRoomInput, GetRoomUseCase,
    ListRoomsInput, ListRoomsUseCase,
)


def _mock_hotel(owner_id="owner-1", **kwargs) -> Hotel:
    h = Hotel.__new__(Hotel)
    from datetime import datetime
    attrs = dict(id="hotel-1", owner_id=owner_id, name="Test Hotel",
                 description="", address="1 rue Test", city="Paris",
                 country="France", latitude=0.0, longitude=0.0, stars=4,
                 status=HotelStatus.ACTIVE, phone="", email="", website="",
                 amenities=[], images=[],
                 created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    attrs.update(kwargs)
    for k, v in attrs.items():
        object.__setattr__(h, k, v)
    return h


def _mock_room(**kwargs) -> Room:
    r = Room.__new__(Room)
    from datetime import datetime
    attrs = dict(id="room-1", hotel_id="hotel-1", name="Chambre Test",
                 type=RoomType.DOUBLE, description="", price_per_night=100.0,
                 currency="EUR", capacity=2, size_sqm=25, bed_count=1,
                 bed_type="Double", floor=1, amenities=[], images=[],
                 is_available=True,
                 created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    attrs.update(kwargs)
    for k, v in attrs.items():
        object.__setattr__(r, k, v)
    return r


class TestCreateHotelUseCase:

    def test_creates_and_saves_hotel(self):
        repo = MagicMock()
        hotel = _mock_hotel()
        repo.save.return_value = hotel
        uc = CreateHotelUseCase(repo)
        result = uc.execute(CreateHotelInput(
            owner_id="owner-1", name="Test Hotel", description="",
            address="1 rue Test", city="Paris", country="France", stars=4,
        ))
        repo.save.assert_called_once()
        assert result.name == "Test Hotel"


class TestGetHotelUseCase:

    def test_returns_hotel_when_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _mock_hotel()
        uc = GetHotelUseCase(repo)
        result = uc.execute(GetHotelInput(hotel_id="hotel-1"))
        assert result.id == "hotel-1"

    def test_raises_when_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        uc = GetHotelUseCase(repo)
        with pytest.raises(EntityNotFoundError) as exc:
            uc.execute(GetHotelInput(hotel_id="ghost"))
        assert exc.value.entity == "Hotel"


class TestUpdateHotelUseCase:

    def test_owner_can_update(self):
        repo = MagicMock()
        hotel = _mock_hotel(owner_id="owner-1")
        repo.find_by_id.return_value = hotel
        repo.save.return_value = hotel
        uc = UpdateHotelUseCase(repo)
        uc.execute(UpdateHotelInput(hotel_id="hotel-1", requester_id="owner-1", name="Nouveau Nom"))
        repo.save.assert_called_once()

    def test_non_owner_cannot_update(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _mock_hotel(owner_id="owner-1")
        uc = UpdateHotelUseCase(repo)
        with pytest.raises(AuthorizationError):
            uc.execute(UpdateHotelInput(hotel_id="hotel-1", requester_id="other-user"))

    def test_admin_can_update_any_hotel(self):
        repo = MagicMock()
        hotel = _mock_hotel(owner_id="owner-1")
        repo.find_by_id.return_value = hotel
        repo.save.return_value = hotel
        uc = UpdateHotelUseCase(repo)
        uc.execute(UpdateHotelInput(
            hotel_id="hotel-1", requester_id="admin-id", is_admin=True, name="Modifié"
        ))
        repo.save.assert_called_once()


class TestDeleteHotelUseCase:

    def test_owner_can_delete(self):
        repo = MagicMock()
        hotel = _mock_hotel(owner_id="owner-1")
        repo.find_by_id.return_value = hotel
        repo.save.return_value = hotel
        uc = DeleteHotelUseCase(repo)
        uc.execute(DeleteHotelInput(hotel_id="hotel-1", requester_id="owner-1"))
        assert hotel.status == HotelStatus.INACTIVE

    def test_stranger_cannot_delete(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _mock_hotel(owner_id="owner-1")
        uc = DeleteHotelUseCase(repo)
        with pytest.raises(AuthorizationError):
            uc.execute(DeleteHotelInput(hotel_id="hotel-1", requester_id="stranger"))


class TestCreateRoomUseCase:

    def test_creates_room_for_existing_hotel(self):
        room_repo  = MagicMock()
        hotel_repo = MagicMock()
        hotel_repo.find_by_id.return_value = _mock_hotel(owner_id="owner-1")
        room_repo.save.return_value = _mock_room()
        uc = CreateRoomUseCase(room_repo, hotel_repo)
        result = uc.execute(CreateRoomInput(
            hotel_id="hotel-1", requester_id="owner-1",
            name="Double Std", type="DOUBLE", description="",
            price_per_night=120.0, capacity=2,
        ))
        room_repo.save.assert_called_once()

    def test_raises_if_hotel_not_found(self):
        room_repo  = MagicMock()
        hotel_repo = MagicMock()
        hotel_repo.find_by_id.return_value = None
        uc = CreateRoomUseCase(room_repo, hotel_repo)
        with pytest.raises(EntityNotFoundError):
            uc.execute(CreateRoomInput(
                hotel_id="ghost", requester_id="owner-1",
                name="Test", type="DOUBLE", description="",
                price_per_night=100.0, capacity=2,
            ))

    def test_non_owner_cannot_create_room(self):
        room_repo  = MagicMock()
        hotel_repo = MagicMock()
        hotel_repo.find_by_id.return_value = _mock_hotel(owner_id="owner-1")
        uc = CreateRoomUseCase(room_repo, hotel_repo)
        with pytest.raises(AuthorizationError):
            uc.execute(CreateRoomInput(
                hotel_id="hotel-1", requester_id="stranger",
                name="Test", type="DOUBLE", description="",
                price_per_night=100.0, capacity=2,
            ))
