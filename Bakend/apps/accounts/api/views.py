from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole
from apps.accounts.services import change_password, security_event

from .serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    SignupSerializer,
    UserAdminSerializer,
    UserSerializer,
)


class SignupAPIView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(request=SignupSerializer, responses={201: UserSerializer})
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        security_event("signup", user=user, ip_address=request.META.get("REMOTE_ADDR"))
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(request=LoginSerializer, responses=UserSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": "La connexion a échoué.", "code": "authentication_failed"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        login(request, user)
        request.session.cycle_key()
        return Response(UserSerializer(user).data)


class LogoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        security_event("logout", user=request.user, ip_address=request.META.get("REMOTE_ADDR"))
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(request=UserSerializer, responses=UserSerializer)
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PasswordChangeAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=PasswordChangeSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"detail": "Le changement a échoué.", "code": "password_change_failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        change_password(
            user=request.user,
            new_password=serializer.validated_data["new_password"],
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        update_session_auth_hash(request, request.user)
        return Response({"detail": "Mot de passe modifié."})


class PasswordResetRequestAPIView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=PasswordResetRequestSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        user = get_user_model().objects.filter(email__iexact=email, is_active=True).first()
        if user:
            reset_form = PasswordResetForm({"email": user.email})
            if reset_form.is_valid():
                reset_form.save(
                    request=request,
                    use_https=request.is_secure(),
                    email_template_name="accounts/password_reset_email.txt",
                    subject_template_name="accounts/password_reset_subject.txt",
                )
        return Response({"detail": "Si le compte existe, un e-mail a été envoyé."})


class PasswordResetConfirmAPIView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user_id = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = get_user_model().objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            return Response(
                {"detail": "Lien invalide ou expiré.", "code": "invalid_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response(
                {"detail": "Lien invalide ou expiré.", "code": "invalid_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        password = serializer.validated_data["new_password"]
        try:
            validate_password(password, user)
        except ValidationError as exc:
            return Response(
                {"detail": exc.messages, "code": "weak_password"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        change_password(
            user=user, new_password=password, ip_address=request.META.get("REMOTE_ADDR")
        )
        return Response({"detail": "Mot de passe modifié."})


class UserAdminViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserAdminSerializer
    permission_classes = (IsAdminRole,)
    lookup_field = "public_id"
    http_method_names = ("get", "post", "patch", "head", "options")

    def perform_update(self, serializer):
        if (
            serializer.instance == self.request.user
            and "role" in serializer.validated_data
            and serializer.validated_data["role"] != self.request.user.role
        ):
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"role": "Vous ne pouvez pas modifier votre propre rôle."})
        serializer.save()

    @action(detail=True, methods=("post",))
    def deactivate(self, request, public_id=None):
        user = self.get_object()
        if user == request.user:
            return Response(
                {"detail": "Vous ne pouvez pas désactiver votre propre compte."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = False
        user.save(update_fields=("is_active", "updated_at"))
        security_event(
            "account_deactivated",
            user=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
            target=str(user.public_id),
        )
        return Response({"detail": "Compte désactivé."})
