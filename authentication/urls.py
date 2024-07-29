
from django.urls import path


from .views import RegistrationAPIView, MyTokenObtainPairView, TokenRefreshView, LogoutView, ResetPasswordView, \
    NewPasswordView

app_name = 'authentication'




urlpatterns = [
    path('register/', RegistrationAPIView.as_view()),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', ResetPasswordView.as_view(), name='login'),
    path('new-password/', NewPasswordView.as_view(), name='password_reset'),
]
