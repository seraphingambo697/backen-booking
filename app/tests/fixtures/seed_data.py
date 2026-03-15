"""
app/tests/fixtures/seed_data.py
Données de test pour le développement.

Usage : python manage.py shell < app/tests/fixtures/seed_data.py
"""
from django.contrib.auth.hashers import make_password

from app.modules.user.infrastructure.database.user_models import UserModel
from app.modules.hotel.infrastructure.database.hotel_models import HotelModel, RoomModel


# ── Utilisateurs ────────
admin = UserModel.objects.get_or_create(
    email="admin@luxstay.fr",
    defaults={
        "first_name": "Admin",
        "last_name": "LuxStay",
        "password": make_password("admin123!"),
        "is_admin": True,
        "is_staff": True,
        "is_superuser": True,
    }
)[0]

demo = UserModel.objects.get_or_create(
    email="demo@luxstay.fr",
    defaults={
        "first_name": "Marie",
        "last_name": "Dupont",
        "password": make_password("demo123!"),
    }
)[0]

# ── Hôtels ──────────────
grand_palais = HotelModel.objects.get_or_create(
    name="Le Grand Palais",
    defaults={
        "owner": admin,
        "description": "Hôtel de luxe au cœur de Paris, à deux pas des Champs-Élysées.",
        "address": "10 Avenue des Champs-Élysées",
        "city": "Paris",
        "country": "France",
        "latitude": 48.8698,
        "longitude": 2.3079,
        "stars": 5,
        "amenities": ["WiFi", "Piscine", "Spa", "Restaurant", "Bar", "Parking", "Climatisation"],
        "images": ["https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800"],
    }
)[0]

riviera = HotelModel.objects.get_or_create(
    name="Hôtel Riviera Nice",
    defaults={
        "owner": admin,
        "description": "Face à la Méditerranée, vue imprenable sur la Promenade des Anglais.",
        "address": "45 Promenade des Anglais",
        "city": "Nice",
        "country": "France",
        "latitude": 43.6957,
        "longitude": 7.2659,
        "stars": 4,
        "amenities": ["WiFi", "Piscine", "Vue mer", "Restaurant", "Plage privée"],
        "images": ["https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800"],
    }
)[0]

# ── Chambres Grand Palais ─────────────────────────────────────────────────────
for room_data in [
    {"name": "Chambre Classique", "type": "DOUBLE", "price_per_night": 350,
     "capacity": 2, "size_sqm": 30, "bed_count": 1, "bed_type": "Grand lit double",
     "amenities": ["WiFi", "Climatisation", "Mini-bar", "Coffre-fort"]},
    {"name": "Suite Présidentielle", "type": "SUITE", "price_per_night": 850,
     "capacity": 4, "size_sqm": 80, "bed_count": 2, "bed_type": "King size",
     "amenities": ["WiFi", "Climatisation", "Jacuzzi", "Salon privé", "Vue Tour Eiffel"]},
    {"name": "Chambre Deluxe", "type": "DELUXE", "price_per_night": 520,
     "capacity": 2, "size_sqm": 45, "bed_count": 1, "bed_type": "King size",
     "amenities": ["WiFi", "Climatisation", "Baignoire", "Vue Champs-Élysées"]},
]:
    RoomModel.objects.get_or_create(hotel=grand_palais, name=room_data["name"], defaults=room_data)

print("✅ Données de seed créées avec succès !")
print(f"   Admin: admin@luxstay.fr / admin123!")
print(f"   Demo:  demo@luxstay.fr / demo123!")
