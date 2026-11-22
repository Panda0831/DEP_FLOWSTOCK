from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    nom_complet = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, value):
        email = value.strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Impossible de créer ce compte.")
        return email

    def validate_password(self, value):
        candidate = get_user_model()(
            email=self.initial_data.get("email", ""),
            nom_complet=self.initial_data.get("nom_complet", ""),
        )
        validate_password(value, candidate)
        return value

    def create(self, validated_data):
        return get_user_model().objects.create_user(
            email=validated_data["email"],
            nom_complet=validated_data["nom_complet"].strip(),
            password=validated_data["password"],
            role="VENDEUR",
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)


class UserSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            "public_id",
            "email",
            "nom_complet",
            "role",
            "is_active",
            "is_staff",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "public_id",
            "email",
            "role",
            "is_active",
            "is_staff",
            "created_at",
            "updated_at",
        )


class UserAdminSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)

    class Meta:
        model = get_user_model()
        fields = (
            "public_id",
            "email",
            "nom_complet",
            "password",
            "role",
            "is_active",
            "is_staff",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("public_id", "created_at", "updated_at")

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if not self.instance and not attrs.get("password"):
            raise serializers.ValidationError(
                {"password": "Ce champ est obligatoire lors de la création."}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        return get_user_model().objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    def validate_role(self, value):
        if value not in ("ADMIN", "VENDEUR"):
            raise serializers.ValidationError("Rôle invalide")
        return value
