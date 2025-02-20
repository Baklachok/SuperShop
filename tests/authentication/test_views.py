import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from authentication.models import FrontendUser, TelNoCode

User = get_user_model()

@pytest.mark.django_db
def test_registration():
    client = APIClient()
    url = reverse("authentication:registration")

    data = {
        "username": "testuser",  # <- Это поле не используется в сериализаторе, можно убрать
        "email": "test@example.com",  # <- Это тоже не используется
        "password": "testpassword123",
        "passwordConfirmation": "testpassword123",  # <- Обязательно добавить
        "telNo": "+79894567890",
        "name": "Test User"  # <- Обязательно добавить
    }

    response = client.post(url, data, format="json")
    print(response.data)  # Посмотреть ответ API

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_login():
    client = APIClient()
    url = reverse("token_obtain_pair")  # Имя в `urls.py`
    
    user = FrontendUser.objects.create_user(telNo="+79894567890", password="testpassword123")

    data = {
        "telNo":"+79894567890",
        "password": "testpassword123",
    }

    response = client.post(url, data, format="json")
    print(response.data)
    
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data

@pytest.mark.django_db
def test_refresh_token():
    client = APIClient()
    
    # Создаём пользователя с телефоном
    user = FrontendUser.objects.create_user(telNo="+79894567890", password="testpassword123")

    # Получаем access и refresh токены
    url = reverse("token_obtain_pair")
    response = client.post(url, {"telNo": "+79894567890", "password": "testpassword123"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "refresh" in response.data, f"Response: {response.data}"
    
    refresh_token = response.data["refresh"]

    # Тестируем обновление токена
    refresh_url = reverse("token_refresh")
    refresh_response = client.post(refresh_url, {"refresh": refresh_token}, format="json")

    assert refresh_response.status_code == status.HTTP_200_OK
    assert "access" in refresh_response.data, f"Response: {refresh_response.data}"


@pytest.mark.django_db
def test_logout():
    client = APIClient()
    
    # Создаём пользователя
    user = FrontendUser.objects.create_user(telNo="+79894567890", password="testpassword123")

    # Логинимся и получаем токены
    login_url = reverse("token_obtain_pair")
    response = client.post(login_url, {"telNo": "+79894567890", "password": "testpassword123"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "refresh" in response.data, f"Response: {response.data}"
    
    refresh_token = response.data["refresh"]
    
    # Добавляем токен в куки для проверки логаута
    client.cookies["refresh_token"] = refresh_token

    # Логаут
    logout_url = reverse("authentication:logout")  # Убедитесь, что имя URL правильное
    logout_response = client.get(logout_url)

    assert logout_response.status_code == status.HTTP_200_OK
    assert logout_response.data["success"] is True

@pytest.mark.django_db
def test_reset_password():
    client = APIClient()

    # Создаём тестового пользователя
    user = FrontendUser.objects.create_user(telNo="+79894567890", password="testpassword123")

    url = reverse("authentication:password_reset")  # Проверь имя в urls.py

    data = {"telNo": "+79894567890"}

    # Шаг 1: Отправляем запрос на сброс пароля
    response = client.post(url, data, format="json")
    print("Step 1 Response:", response.data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST, f"Step 1 failed: {response.data}"
    assert response.data["message"]["code"][0] == "Haven't code", f"Unexpected error: {response.data}"

    # Шаг 2: Проверяем, что код подтверждения создан
    db_code = TelNoCode.objects.filter(telNo="+79894567890").first()
    assert db_code is not None, "Код не был создан в базе данных"
    print("Generated code:", db_code.code)

    # Шаг 3: Отправляем код подтверждения для завершения процесса сброса
    confirm_data = {
        "telNo": "+79894567890",
        "code": db_code.code
    }

    confirm_response = client.post(url, confirm_data, format="json")
    print("Step 2 Response:", confirm_response.data)

    assert confirm_response.status_code == status.HTTP_200_OK, f"Step 2 failed: {confirm_response.data}"

@pytest.mark.django_db
def test_new_password():
    client = APIClient()
    user = FrontendUser.objects.create_user(telNo="+79894567890", password="testpassword123")

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    url = reverse("authentication:new_password")  # Проверь имя в `urls.py`

    data = {
        "token": access_token,
        "password": "newpassword123",
        "password_confirm": "newpassword123"
    }

    response = client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.check_password("newpassword123")
