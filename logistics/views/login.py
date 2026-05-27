from logistics.middleware.request_logging import logger
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from logistics.serializers.auth import LoginSerializer
from logistics.views.tokens import tokens_for_user


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        logger.info('User logged in successfully. user_id=%s', user.id)
        return Response(
            {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                },
                'tokens': tokens_for_user(user),
            }
        )
