from django.utils import timezone

from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from supershop.settings import SIMPLE_JWT
from .models import FrontendUser, UserRefreshToken
from .serializers import RegistrationSerializer, MyTokenObtainSerializer, ResetPasswordSerializer, NewPasswordSerializer


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

            response = Response(
                {
                    "success": True,
                    "access": response_data["access"],
                    "refresh": response_data["refresh"],
                },
                status=status.HTTP_200_OK,  # Должен быть 200 OK, а не 201 CREATED
            )

            # Set tokens in cookies
            access_token_expiry = timezone.now() + SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
            refresh_token_expiry = timezone.now() + SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]

            response.set_cookie(
                "refresh_token", response_data["refresh"], httponly=True, expires=refresh_token_expiry
            )
            response.set_cookie(
                "access_token", response_data["access"], httponly=True, expires=access_token_expiry
            )

            return response

        return Response(
            {"error": "True", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )


class TokenRefreshView(generics.GenericAPIView):
    def post(self, request):
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token:
            try:
                stored_token = UserRefreshToken.objects.get(token=refresh_token)
                if stored_token.expires_at < timezone.now():
                    return Response({'error': True, 'message': 'Refresh token expired'},
                                    status=status.HTTP_401_UNAUTHORIZED)
                new_access_token = RefreshToken(refresh_token).access_token
                
                # Возвращаем access token явно
                return Response({
                    'success': True,
                    'access': str(new_access_token),
                }, status=status.HTTP_200_OK)

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


class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            phone = request.data.get('telNo')
            response = Response({"success": True}, status=status.HTTP_200_OK)
            try:
                user = FrontendUser.objects.get(telNo=phone)
            except FrontendUser.DoesNotExist:
                return Response({"error": "True", "message": "User does not exist"},)
            temporary_token = str(RefreshToken.for_user(user).access_token)
            return Response({"success": True, 'token': temporary_token}, status=status.HTTP_200_OK)
        else:
            response = Response({"error": ["True"], "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        return response


class NewPasswordView(generics.GenericAPIView):
    serializer_class = NewPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            response = Response({"success": True}, status=status.HTTP_200_OK)
            response_data = serializer.validated_data
            access_token = request.data.get('token')
            print(response_data)
            print(request.data)
            print(access_token)
            print("access_token")
            if access_token:
                try:
                    token = AccessToken(access_token)
                    user_id = token['user_id']

                    try:
                        user = FrontendUser.objects.get(pk=user_id)
                        print('user est')
                    except FrontendUser.DoesNotExist:
                        return Response({'error': True, 'message': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
                    user.set_password(response_data['password'])
                    print('user set')
                    user.save()
                    return Response({'success': True}, status=status.HTTP_200_OK)
                except Exception as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                response = Response({"error": "True", "message": 'no token'}, status=status.HTTP_400_BAD_REQUEST)
                return response
