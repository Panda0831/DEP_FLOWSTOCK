from django.conf import settings
from django.http import JsonResponse


def login_lockout_response(request, credentials=None):
    del request, credentials
    minutes = settings.AXES_COOLOFF_MINUTES
    return JsonResponse(
        {
            "detail": (
                f"La connexion est temporairement bloquée après plusieurs échecs. "
                f"Réessayez dans {minutes} minutes ou réinitialisez votre mot de passe."
            ),
            "code": "login_temporarily_locked",
            "retry_after_minutes": minutes,
        },
        status=429,
    )
