from rest_framework import serializers


class RegisterRequestSerializer(serializers.Serializer):
    email      = serializers.EmailField()
    first_name = serializers.CharField(max_length=100)
    last_name  = serializers.CharField(max_length=100)
    password   = serializers.CharField(min_length=8, write_only=True)
    phone      = serializers.CharField(max_length=20, required=False, default="")

class LoginRequestSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class UpdateUserRequestSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False)
    last_name  = serializers.CharField(required=False)
    phone      = serializers.CharField(required=False)
    email      = serializers.EmailField(required=False)
    password   = serializers.CharField(min_length=8, write_only=True, required=False)

class UserResponseSerializer(serializers.Serializer):
    id         = serializers.UUIDField()
    email      = serializers.EmailField()
    first_name = serializers.CharField()
    last_name  = serializers.CharField()
    phone      = serializers.CharField()
    is_active  = serializers.BooleanField()
    is_admin   = serializers.BooleanField()
    created_at = serializers.DateTimeField()

class TokenResponseSerializer(serializers.Serializer):
    access  = serializers.CharField()
    refresh = serializers.CharField()
    user    = UserResponseSerializer()