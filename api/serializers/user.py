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
from rest_framework.exceptions import APIException
from rest_framework import status
from organization.models import DeviceTracker


User = get_user_model()

import json

class Custom306Exception(APIException):
    status_code = status.HTTP_306_RESERVED
    default_detail = 'Custom error message for status code 306'
    
class Custom400Exception(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Custom error message for status code 400'

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
        self.fields["terminal"] = serializers.CharField()
        self.fields["deviceId"] = serializers.CharField()


    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            "password": attrs["password"],
            "branch": attrs.get("branch", None),
            "terminal": attrs.get("terminal", None),
            "deviceId": attrs.get("deviceId", None),
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
        terminal = attrs.get("terminal", None)
        deviceId = attrs.get("deviceId", None)
        print(branch)
        print(f'terminal {terminal}')
        self.branch = branch
        self.terminal = terminal
        self.deviceId = deviceId


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

        # Include the "branch" from the data passed during token validation
        branch = attrs.get("branch")
        terminal = attrs.get("terminal")

        if branch:
            data["branch"] = branch
            data["terminal"] = terminal
            # data["token"]["branch"] = branch

        return data
    

    def get_token(self, user):
        token = super().get_token(user)
        token["name"] = user.full_name
        groups = []
        for group in user.groups.values_list("name"):
            groups.append(group[0])
        group_str = json.dumps(groups)
        token["role"] = group_str
        # token["branch"] = attrs.get("branch")

        # branch = attrs.get("branch")
        # if branch:
        #     token["branch"] = branch
        branch = self.branch
        terminal = self.terminal
        deviceId = self.deviceId

        try:
            branch_obj = Branch.objects.get(id=branch)
            token["branch"] = branch
        except(ObjectDoesNotExist, ValueError):
            raise serializers.ValidationError({"detail":"No branch found"})
        try:
            terminal_obj = Terminal.objects.get(terminal_no=terminal, branch=branch_obj, is_deleted=False, status=True)
            token["terminal"] = terminal
        except(ObjectDoesNotExist, ValueError):
            raise serializers.ValidationError({"detail":"No terminal found"})
        

        # # if Terminal.objects.get(terminal_no=terminal, branch=branch_obj, is_deleted=False, status=True).is_active == True:
        # #     raise Custom306Exception({"detail":"Terminal is already active"})
        # if terminal_obj.is_active == True:
        #     raise Custom306Exception({"detail":"Terminal is already active"})
        # # elif terminal_obj.active_count >= 1:
        # #     raise Custom306Exception({'detail': "Terminal is already active in another device"})

        # else:
        #     terminal_obj.is_active = True
        #     terminal_obj.active_count += 1
        #     terminal_obj.save()
        #     return token

        if DeviceTracker.objects.filter(terminal=terminal_obj, status=True).exists():
            raise Custom400Exception({"detail":"Terminal is already associated with another device"})
        else:
            DeviceTracker.objects.filter(terminal=terminal_obj).delete()
            DeviceTracker.objects.create(deviceId=deviceId, terminal=terminal_obj)
            token["deviceId"] = deviceId
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



# from django.contrib.auth import get_user_model
# from rest_framework.serializers import ModelSerializer
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# from user.models import Customer


# User = get_user_model()

# import json


# class CustomTokenPairSerializer(TokenObtainPairSerializer):
#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)
#         token["name"] = user.full_name
#         groups = []
#         for group in user.groups.values_list("name"):
#             groups.append(group[0])
#         group_str = json.dumps(groups)
#         token["role"] = group_str

#         return token


# class CustomerSerializer(ModelSerializer):
#     class Meta:
#         model = Customer
#         exclude = [
#             "created_at",
#             "updated_at",
#             "status",
#             "is_deleted",
#             "sorting_order",
#             "is_featured",
#             "created_by",
#         ]


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields = ['full_name', 'username']