from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    LoginAPIView,
    LogoutAPIView,
    MeAPIView,
    PasswordChangeAPIView,
    PasswordResetConfirmAPIView,
    PasswordResetRequestAPIView,
    SignupAPIView,
    UserAdminViewSet,
)

router = DefaultRouter()
router.register("users", UserAdminViewSet, basename="user")

urlpatterns = router.urls + [
    path("auth/signup/", SignupAPIView.as_view(), name="auth-signup"),
    path("auth/login/", LoginAPIView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="auth-logout"),
    path("auth/me/", MeAPIView.as_view(), name="auth-me"),
    path("auth/password/change/", PasswordChangeAPIView.as_view(), name="auth-password-change"),
    path(
        "auth/password/reset/request/",
        PasswordResetRequestAPIView.as_view(),
        name="auth-password-reset-request",
    ),
    path(
        "auth/password/reset/confirm/",
        PasswordResetConfirmAPIView.as_view(),
        name="auth-password-reset-confirm",
    ),
]
