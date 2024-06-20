from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.authentication import BaseAuthentication, BasicAuthentication
from rest_framework.exceptions import AuthenticationFailed
from organization.models import Terminal  # Import your Terminal model
import jwt

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import HTTP_HEADER_ENCODING, authentication

from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework import status
from rest_framework.exceptions import APIException

from organization.models import DeviceTracker


AUTH_HEADER_TYPES = api_settings.AUTH_HEADER_TYPES

if not isinstance(api_settings.AUTH_HEADER_TYPES, (list, tuple)):
    AUTH_HEADER_TYPES = (AUTH_HEADER_TYPES,)

AUTH_HEADER_TYPE_BYTES = {h.encode(HTTP_HEADER_ENCODING) for h in AUTH_HEADER_TYPES}

class Custom306Exception(APIException):
    status_code = status.HTTP_306_RESERVED
    default_detail = 'Custom error message for status code 306'

class Custom400Exception(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Custom error message for status code 400'

class CustomTerminalAuthentication(authentication.BaseAuthentication):
    """
    An authentication plugin that authenticates requests through a JSON web
    token provided in a request header.
    """

    www_authenticate_realm = "api"
    media_type = "application/json"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_model = get_user_model()

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        role = validated_token.get('role')
        deviceId = validated_token.get('deviceId')


        
        branch = validated_token.get("branch")
        if not branch:
            raise Custom306Exception('Branch not found in token')
        
        


            
        if "agent" in role:
        
            terminal_number = validated_token.get('terminal')
            if not terminal_number:
                raise Custom400Exception('Terminal not found in token')
        
            try:
                terminal = Terminal.objects.get(terminal_no=terminal_number, branch__id=branch, is_deleted=False, status=True)

            except Terminal.DoesNotExist:
                raise Custom400Exception('Terminal not found')    

            try:
                devicetracker_obj = DeviceTracker.objects.filter(terminal=terminal, status=True)

                if devicetracker_obj.count() > 1:
                    raise Custom400Exception('Terminal is active in more than one  device', code= status.HTTP_306_RESERVED)

            except DeviceTracker.DoesNotExist:
                raise Custom400Exception('Devicetracker has no associated terminal objects')
            try:
                devicetracker_obj = DeviceTracker.objects.get(deviceId=deviceId, terminal=terminal)

                if not devicetracker_obj.status:
                    raise Custom306Exception('Terminal status is not active for this device', code= status.HTTP_306_RESERVED)

            except DeviceTracker.DoesNotExist:
                raise Custom306Exception('DeviceTracker Status not active')
            



        return self.get_user(validated_token), validated_token

    def authenticate_header(self, request):
        return '{} realm="{}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

    def get_header(self, request):
        """
        Extracts the header containing the JSON web token from the given
        request.
        """
        header = request.META.get(api_settings.AUTH_HEADER_NAME)

        if isinstance(header, str):
            # Work around django test client oddness
            header = header.encode(HTTP_HEADER_ENCODING)

        return header

    def get_raw_token(self, header):
        """
        Extracts an unvalidated JSON web token from the given "Authorization"
        header value.
        """
        parts = header.split()

        if len(parts) == 0:
            # Empty AUTHORIZATION header sent
            return None

        if parts[0] not in AUTH_HEADER_TYPE_BYTES:
            # Assume the header does not contain a JSON web token
            return None

        if len(parts) != 2:
            raise AuthenticationFailed(
                _("Authorization header must contain two space-delimited values"),
                code="bad_authorization_header",
            )

        return parts[1]

    def get_validated_token(self, raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        messages = []
        for AuthToken in api_settings.AUTH_TOKEN_CLASSES:
            try:
                return AuthToken(raw_token)
            except TokenError as e:
                messages.append(
                    {
                        "token_class": AuthToken.__name__,
                        "token_type": AuthToken.token_type,
                        "message": e.args[0],
                    }
                )

        raise InvalidToken(
            {
                "detail": _("Given token not valid for any token type"),
                "messages": messages,
            }
        )

    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_("Token contained no recognizable user identification"))

        try:
            user = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(_("User not found"), code="user_not_found")

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")

        return user