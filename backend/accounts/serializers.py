from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT-сериализатор, добавляет role и employee_id в ответ (не в payload токена)."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        profile = getattr(user, 'profile', None)
        token['role'] = profile.role if profile else 'EMPLOYEE'
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        profile = getattr(self.user, 'profile', None)
        data['role'] = profile.role if profile else 'EMPLOYEE'
        data['employee_id'] = profile.employee_id if profile else None
        data['username'] = self.user.username
        data['full_name'] = self.user.get_full_name() or self.user.username
        return data


class UserMeSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'role', 'employee_id']

    def get_role(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.role if profile else 'EMPLOYEE'

    def get_employee_id(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.employee_id if profile else None

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserListSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'role', 'employee_id', 'is_active', 'date_joined']

    def get_role(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.role if profile else None

    def get_employee_id(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.employee_id if profile else None

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserRoleUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES)


class ProfileUpdateSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(min_length=6, required=False, write_only=True)
