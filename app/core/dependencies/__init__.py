"""
app/core/dependencies/__init__.py
Re-export de toutes les factories pour rétro-compatibilité.

Les vues importent depuis ce package :
    from app.core.dependencies import get_create_hotel_uc
"""
from app.core.dependencies.user    import *  # noqa: F401, F403
from app.core.dependencies.hotel   import *  # noqa: F401, F403
from app.core.dependencies.booking import *  # noqa: F401, F403
from app.core.dependencies.payment import *  # noqa: F401, F403
from app.core.dependencies.review  import *  # noqa: F401, F403
from app.core.dependencies.search  import *  # noqa: F401, F403
