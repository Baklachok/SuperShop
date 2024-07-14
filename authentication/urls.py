
from django.urls import path


from .views import RegistrationAPIView, MyTokenObtainPairView, TokenRefreshView, LogoutView

app_name = 'authentication'




urlpatterns = [
    path('register/', RegistrationAPIView.as_view()),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
