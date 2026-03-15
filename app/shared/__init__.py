"""
app/shared/__init__.py
Re-exports des abstractions partagées les plus utilisées.

    from app.shared import BaseEntity, BaseUseCase, DateRange, Money, GuestCount
"""
from app.shared.domain.base_entity     import BaseEntity, DomainEvent       # noqa: F401
from app.shared.domain.base_repository import BaseRepository                  # noqa: F401
from app.shared.domain.base_use_case   import BaseUseCase, NoInputUseCase    # noqa: F401
from app.shared.domain.value_objects   import DateRange, GuestCount, Money   # noqa: F401
