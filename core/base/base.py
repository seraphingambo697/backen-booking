
from core import config

BOOKING_FREE_CANCEL_HOURS     = config("BOOKING_FREE_CANCEL_HOURS",     default=48,  cast=int)
# Nombre maximum de nuits par réservation
BOOKING_MAX_NIGHTS            = config("BOOKING_MAX_NIGHTS",            default=30,  cast=int)
# Délai (minutes) avant expiration d'une réservation PENDING non payée
BOOKING_PENDING_EXPIRY_MINUTES = config("BOOKING_PENDING_EXPIRY_MINUTES", default=30, cast=int)

