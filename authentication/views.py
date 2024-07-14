from datetime import datetime, timezone

from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from supershop.settings import SIMPLE_JWT
from .models import FrontendUser, UserRefreshToken
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
            response = Response({"success": True}, status=status.HTTP_201_CREATED)
            # Set tokens in cookies
            access_token_expiry = datetime.now() + SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
            refresh_token_expiry = datetime.now() + SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']

            response.set_cookie('refresh_token', response_data['refresh'], httponly=True,
                                expires=refresh_token_expiry)
            response.set_cookie('access_token', response_data['access'], httponly=True,
                                expires=access_token_expiry)
        else:
            response = Response({"error": "True", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return response


class TokenRefreshView(generics.GenericAPIView):
    def get(self, request):
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')

        if access_token:
            try:
                AccessToken(access_token)
                return Response({'success': True}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if refresh_token:
            try:
                stored_token = UserRefreshToken.objects.get(token=refresh_token)
                if stored_token.expires_at < datetime.now():
                    return Response({'error': True, 'message': 'Refresh token expired'},
                                    status=status.HTTP_401_UNAUTHORIZED)

                new_access_token = RefreshToken(refresh_token).access_token
                response = Response({'access': 'created'}, status=status.HTTP_200_OK)
                response.set_cookie(
                    key='access_token',
                    value=str(new_access_token),
                    httponly=True,
                    secure=True,
                    samesite='Lax',
                )
                return response
            except UserRefreshToken.DoesNotExist:
                return Response({'error': True, 'message': 'Invalid refresh token'},
                                status=status.HTTP_401_UNAUTHORIZED)

        return Response({'error': True, 'message': 'No valid tokens provided'},
                        status=status.HTTP_400_BAD_REQUEST)


class LogoutView(generics.GenericAPIView):
    def get(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                token = UserRefreshToken.objects.get(token=refresh_token)
                token.delete()
            except UserRefreshToken.DoesNotExist:
                pass  # Token already deleted or invalid

        response = Response({'success': True, 'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
