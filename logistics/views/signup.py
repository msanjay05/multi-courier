from logistics.middleware.request_logging import logger
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from logistics.serializers.auth import SignupSerializer
from logistics.views.tokens import tokens_for_user


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info('User signed up successfully. user_id=%s', user.id)
        return Response(
            {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                },
                'tokens': tokens_for_user(user),
            },
            status=status.HTTP_201_CREATED,
        )
