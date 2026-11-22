from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny

urlpatterns = [
    path("healthz/", lambda request: HttpResponse("ok", content_type="text/plain"), name="healthz"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.accounts.api.urls")),
    path("api/v1/", include("apps.catalog.api.urls")),
    path("api/v1/", include("apps.inventory.api.urls")),
    path("api/v1/", include("apps.sales.api.urls")),
    path("api/v1/", include("apps.finance.api.urls")),
    path("api/v1/", include("apps.purchasing.api.urls")),
]

if settings.ACTIVER_DOCUMENTATION_API:
    urlpatterns += [
        path(
            "api/schema/",
            SpectacularAPIView.as_view(permission_classes=[AllowAny]),
            name="schema",
        ),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(
                url_name="schema",
                permission_classes=[AllowAny],
            ),
            name="swagger-ui",
        ),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
