"""En-têtes HTTP sensibles appliqués par chemin."""

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse


class CacheNoStoreMiddleware:
    """Empêche la mise en cache des réponses d’authentification et d’utilisateurs."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, requete: HttpRequest) -> HttpResponse:
        reponse = self.get_response(requete)

        if requete.path.startswith(("/api/v1/auth/", "/api/v1/users/")):
            reponse["Cache-Control"] = "no-store"
            reponse["Pragma"] = "no-cache"

        return reponse
