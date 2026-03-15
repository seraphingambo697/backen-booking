"""
app/shared/presentation/pagination.py
Classes de pagination DRF pour LuxStay.

StandardPagination : pagination par offset/page (défaut, simple)
BookingPagination  : pagination par cursor (réservations — liste longue, temps réel)
"""
from __future__ import annotations

from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    Pagination numérotée — utilisée par hotels, rooms, reviews.

    Query params : ?page=2&page_size=24
    Réponse :
        {
            "success": true,
            "count":   42,
            "pages":   4,
            "next":    "http://…?page=3",
            "previous":"http://…?page=1",
            "data":    [...]
        }
    """
    page_size             = 12
    page_size_query_param = "page_size"
    max_page_size         = 100
    page_query_param      = "page"

    def get_paginated_response(self, data: list) -> Response:
        return Response({
            "success":  True,
            "count":    self.page.paginator.count,
            "pages":    self.page.paginator.num_pages,
            "next":     self.get_next_link(),
            "previous": self.get_previous_link(),
            "data":     data,
        })

    def get_paginated_response_schema(self, schema: dict) -> dict:
        return {
            "type": "object",
            "properties": {
                "success":  {"type": "boolean"},
                "count":    {"type": "integer"},
                "pages":    {"type": "integer"},
                "next":     {"type": "string", "nullable": True},
                "previous": {"type": "string", "nullable": True},
                "data":     schema,
            },
        }


class BookingPagination(CursorPagination):
    """
    Pagination par cursor — utilisée pour les listes de réservations.

    Avantages vs offset :
      - Stable même si des réservations sont ajoutées/supprimées entre pages
      - Performant sur grandes tables (pas de COUNT(*))
      - Idéal pour les listes temps-réel

    Query params : ?cursor=cD0yMDI...
    Réponse :
        {
            "success": true,
            "next":    "http://…?cursor=...",
            "previous":"http://…?cursor=...",
            "data":    [...]
        }
    """
    page_size             = 20
    page_size_query_param = "page_size"
    max_page_size         = 50
    ordering              = "-created_at"   # Plus récentes en premier
    cursor_query_param    = "cursor"

    def get_paginated_response(self, data: list) -> Response:
        return Response({
            "success":  True,
            "next":     self.get_next_link(),
            "previous": self.get_previous_link(),
            "data":     data,
        })
