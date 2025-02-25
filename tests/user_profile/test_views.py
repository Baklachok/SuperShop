import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from user_profile.models import Address, Review, ReviewPhoto
from django.core.files.uploadedfile import SimpleUploadedFile
from authentication.models import FrontendUser
from api.models import Item
from django.urls import reverse
from PIL import Image
import io

User = get_user_model()


@pytest.fixture
def item(db):
    """Создаёт тестовый товар перед созданием отзыва"""
    return Item.objects.create(name="Test Item", description="Sample item for testing")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return FrontendUser.objects.create_user(telNo="+79894567890", password="testpassword")


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def address(user):
    return Address.objects.create(user=user, address="Test Street 1", lat=55.75, lon=37.61)


@pytest.fixture
def review(user, item):
    return Review.objects.create(user=user, item=item, grade=5, comments="Great product!")


@pytest.fixture
def review_photo(review):
    return ReviewPhoto.objects.create(
        review=review, 
        photo=SimpleUploadedFile("photo.jpg", b"file_content", content_type="image/jpeg")
    )


# =========================== Тесты для адресов ===========================

@pytest.mark.django_db
def test_create_address(auth_client):
    url = reverse("user_profile:address-list")
    data = {"address": "New Address", "lat": 40.71, "lon": -74.00}
    response = auth_client.post(url, data)
    assert response.status_code == 201
    assert response.data["address"] == "New Address"


@pytest.mark.django_db
def test_get_addresses(auth_client, address):
    url = reverse("user_profile:address-list")
    response = auth_client.get(url)
    print(response.data)
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['address'] == "Test Street 1"


@pytest.mark.django_db
def test_update_address(auth_client, address):
    url = reverse("user_profile:address-detail", args=[address.id])
    data = {"address": "Updated Address"}
    response = auth_client.patch(url, data)
    assert response.status_code == 200
    assert response.data["address"] == "Updated Address"


@pytest.mark.django_db
def test_delete_address(auth_client, address):
    url = reverse("user_profile:address-detail", args=[address.id])
    response = auth_client.delete(url)
    assert response.status_code == 204
    assert Address.objects.count() == 0


# =========================== Тесты для отзывов ===========================

@pytest.mark.django_db
def test_create_review(auth_client, item):
    url = reverse("user_profile:review-list")
    data = {"item": item.id, "grade": 4, "comments": "Nice quality"}
    response = auth_client.post(url, data)
    assert response.status_code == 201
    assert response.data["comments"] == "Nice quality"


@pytest.mark.django_db
def test_get_reviews(auth_client, review):
    url = reverse("user_profile:review-list") + f"?item={review.item.id}"
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data["results"][0]["comments"] == "Great product!"


@pytest.mark.django_db
def test_update_review(auth_client, review):
    url = reverse("user_profile:review-detail", args=[review.id])
    data = {"comments": "Updated comment"}
    response = auth_client.patch(url, data)
    assert response.status_code == 200
    assert response.data["comments"] == "Updated comment"


@pytest.mark.django_db
def test_delete_review(auth_client, review):
    url = reverse("user_profile:review-detail", args=[review.id])
    response = auth_client.delete(url)
    assert response.status_code == 204
    assert Review.objects.count() == 0


# =========================== Тесты для фото к отзывам ===========================

@pytest.mark.django_db
def test_create_review_photo(auth_client, review):
    url = reverse("user_profile:reviewphoto-list")

    # Создаём валидное изображение с помощью Pillow
    image = Image.new("RGB", (100, 100), "white")
    image_io = io.BytesIO()
    image.save(image_io, format="JPEG")
    image_io.seek(0)  # Вернуть указатель в начало файла

    file = SimpleUploadedFile("photo.jpg", image_io.getvalue(), content_type="image/jpeg")
    data = {"review": review.id, "photo": file}

    response = auth_client.post(url, data, format="multipart")

    assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_get_review_photos(auth_client, review_photo):
    url = reverse("user_profile:reviewphoto-list")
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_delete_review_photo(auth_client, review_photo):
    url = reverse("user_profile:reviewphoto-detail", args=[review_photo.id])
    response = auth_client.delete(url)
    assert response.status_code == 204
    assert ReviewPhoto.objects.count() == 0
