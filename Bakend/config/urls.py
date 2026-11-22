"""Routes globales de l’application."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.accounts.urls")),
]

if settings.ACTIVER_DOCUMENTATION_API:
    urlpatterns += [
        path(
            "api/v1/schema/",
            SpectacularAPIView.as_view(permission_classes=[AllowAny]),
            name="schema",
        ),
        path(
            "api/v1/docs/",
            SpectacularSwaggerView.as_view(
                url_name="schema",
                permission_classes=[AllowAny],
            ),
            name="swagger-ui",
        ),
    ]
