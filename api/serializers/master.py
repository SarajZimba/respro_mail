from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from user.models import Customer
from rest_framework import serializers, exceptions
from rest_framework_simplejwt.tokens import RefreshToken, SlidingToken, UntypedToken
from rest_framework_simplejwt.settings import api_settings
from organization.models import Branch, Terminal

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()

import json

class PasswordField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("style", {})

        kwargs["style"]["input_type"] = "password"
        kwargs["write_only"] = True

        super().__init__(*args, **kwargs)

class TokenObtainSerializer1(serializers.Serializer):
    username_field = get_user_model().USERNAME_FIELD
    token_class = None

    default_error_messages = {
        "no_active_account": _("No active account found with the given credentials")
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()
        self.fields["password"] = PasswordField()
        self.fields["branch"] = serializers.CharField()

    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            "password": attrs["password"],
            "branch": attrs.get("branch", None)
        }
        try:
            authenticate_kwargs["request"] = self.context["request"]
        except KeyError:
            pass

        self.user = authenticate(**authenticate_kwargs)

        if not api_settings.USER_AUTHENTICATION_RULE(self.user):
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )
        
        branch = attrs.get("branch", None)
        print(branch)
        self.branch = branch

        return {}

    @classmethod
    def get_token(cls, user):
        return cls.token_class.for_user(user)
    

class   TokenObtainPairSerializer1(TokenObtainSerializer1):
    token_class = RefreshToken

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)



        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data

class CustomTokenPairSerializer(TokenObtainPairSerializer1):
    def validate(self, attrs):
        data = super().validate(attrs)

        branch = attrs.get("branch")

        if branch:
            data["branch"] = branch

        return data
    

    def get_token(self, user):
        token = super().get_token(user)
        token["name"] = user.full_name
        groups = []
        for group in user.groups.values_list("name"):
            groups.append(group[0])
        group_str = json.dumps(groups)
        token["role"] = group_str
        branch = self.branch
        try:
            branch_obj = Branch.objects.get(id=branch)
            token["branch"] = branch
        except(ObjectDoesNotExist, ValueError):
            raise serializers.ValidationError({"detail":"No branch found"})
        
        # print(user.groups.values_list("name", flat=True))
        if 'admin' not in user.groups.values_list("name", flat=True):
            raise serializers.ValidationError({"detail":"You are not a manager"})

        return token



class CustomerSerializer(ModelSerializer):
    class Meta:
        model = Customer
        exclude = [
            "created_at",
            "updated_at",
            "status",
            "is_deleted",
            "sorting_order",
            "is_featured",
            "created_by",
        ]