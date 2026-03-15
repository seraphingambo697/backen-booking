"""
app/shared/domain/__init__.py
Exports rapides pour le domaine partagé.
"""
from app.shared.domain.base_entity    import BaseEntity, DomainEvent  # noqa: F401
from app.shared.domain.base_repository import BaseRepository           # noqa: F401
from app.shared.domain.base_use_case  import BaseUseCase               # noqa: F401
from app.shared.domain.value_objects  import DateRange, Money, GuestCount  # noqa: F401
