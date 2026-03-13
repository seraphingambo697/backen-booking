
"""
app/shared/presentation/responses.py
Enveloppes de réponse HTTP standards pour toutes les vues LuxStay.

Toutes les réponses API suivent le même format :

  Succès :
    { "success": true, "data": {...} }
    { "success": true, "data": [...], "count": 3 }

  Erreur :
    { "success": false, "error": { "code": "not_found", "message": "...", "field": "..." } }

Usage dans une vue :
    from app.shared.presentation.responses import success, created, no_content, error

    def get(self, request, booking_id):
        booking = get_booking_uc().execute(...)
        return success(BookingResponseSerializer(booking).data)

    def post(self, request):
        booking = create_booking_uc().execute(...)
        return created(BookingResponseSerializer(booking).data)
"""
from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.response import Response


# ── Réponses succès ───────────────────────────────────────────────────────────

def success(data: Any = None, *, http_status: int = status.HTTP_200_OK) -> Response:
    """
    200 OK — retourne une ressource unique ou une liste.

    Pour les listes, préférer `success_list()` qui ajoute `count`.
    """
    payload: dict = {"success": True}
    if data is not None:
        payload["data"] = data
    return Response(payload, status=http_status)


def success_list(data: list, *, count: int | None = None) -> Response:
    """
    200 OK — liste de ressources avec count.

    Args:
        data:  liste sérialisée
        count: total (si différent de len(data), ex: pagination externe)
    """
    return Response({
        "success": True,
        "count":   count if count is not None else len(data),
        "data":    data,
    })


def created(data: Any = None) -> Response:
    """201 Created — ressource créée avec succès."""
    payload: dict = {"success": True}
    if data is not None:
        payload["data"] = data
    return Response(payload, status=status.HTTP_201_CREATED)


def no_content() -> Response:
    """204 No Content — opération réussie sans corps de réponse."""
    return Response(status=status.HTTP_204_NO_CONTENT)


def accepted(data: Any = None, message: str = "En cours de traitement.") -> Response:
    """202 Accepted — opération async démarrée."""
    return Response(
        {"success": True, "message": message, "data": data},
        status=status.HTTP_202_ACCEPTED,
    )


# ── Réponses erreur ───────────────────────────────────────────────────────────

def error(
    code:        str,
    message:     str,
    field:       str | None = None,
    http_status: int        = status.HTTP_400_BAD_REQUEST,
) -> Response:
    """
    Réponse d'erreur structurée.

    Args:
        code:    Code machine (ex: "not_found", "booking_conflict")
        message: Message lisible par l'humain
        field:   Champ en erreur (validation)
    """
    err: dict = {"code": code, "message": message}
    if field:
        err["field"] = field
    return Response({"success": False, "error": err}, status=http_status)


def validation_error(field: str, message: str) -> Response:
    """422 Unprocessable Entity — erreur de validation métier."""
    return error(
        code="validation_error",
        message=message,
        field=field,
        http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


def not_found(entity: str, identifier: str) -> Response:
    """404 Not Found."""
    return error(
        code="not_found",
        message=f"{entity} '{identifier}' introuvable.",
        http_status=status.HTTP_404_NOT_FOUND,
    )


def conflict(message: str, field: str | None = None) -> Response:
    """409 Conflict."""
    return error(
        code="conflict",
        message=message,
        field=field,
        http_status=status.HTTP_409_CONFLICT,
    )
