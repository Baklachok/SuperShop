from datetime import datetime

from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from supershop.settings import SIMPLE_JWT
from .models import FrontendUser
from .serializers import RegistrationSerializer, MyTokenObtainSerializer


class RegistrationAPIView(generics.CreateAPIView):
    queryset = FrontendUser.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response = Response({"success": True}, status=status.HTTP_201_CREATED)
        else:
            response = Response({"error": ["True"], "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # Set tokens in cookies
        # response.set_cookie('refresh_token', response_data['refresh'], httponly=True)
        # response.set_cookie('access_token', response_data['access'], httponly=True)

        return response


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            response_data = serializer.validated_data
            response = Response({"succes": True}, status=status.HTTP_201_CREATED)
            # Set tokens in cookies
            access_token_expiry = datetime.now() + SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
            refresh_token_expiry = datetime.now() + SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']

            response.set_cookie('refresh_token', response_data['refresh'], httponly=True,
                                expires=refresh_token_expiry, secure=True)
            response.set_cookie('access_token', response_data['access'], httponly=True,
                                expires=access_token_expiry, secure=True)
        else:
            response = Response({"error": "True", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return response
