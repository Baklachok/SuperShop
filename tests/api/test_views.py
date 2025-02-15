import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from api.models import Item, Category, Photo, ItemStock, Color, Size
from api.serializers import ItemSerializer, CategorySerializer, PhotoSerializer, StockItemSerializer

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def category():
    return Category.objects.create(name="Test Category", slug="test-category")

@pytest.fixture
def item(category):
    return Item.objects.create(name="Test Item", price=100, discount=0.1, order_count=5)

@pytest.fixture
def photo():
    return Photo.objects.create(photo="test.jpg")

@pytest.fixture
def color():
    return Color.objects.create(name="Red")

@pytest.fixture
def size():
    return Size.objects.create(name="M")

@pytest.fixture
def stock(item, color, size):
    return ItemStock.objects.create(item=item, color=color, size=size, quantity=10)

# ===============================
# 🔹 ТЕСТЫ ДЛЯ ItemViewSet
# ===============================
@pytest.mark.django_db
def test_get_items(api_client, item):
    url = reverse("item-list")
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1

@pytest.mark.django_db
def test_get_filtered_items(api_client, item):
    url = reverse("item-list") + "?min_price=50"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1

@pytest.mark.django_db
def test_get_max_price(api_client, item):
    url = reverse("item-max-price")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["max_price"] == 90  # 100 - 10 (discount)

# ===============================
# 🔹 ТЕСТЫ ДЛЯ CategoryViewSet
# ===============================
@pytest.mark.django_db
def test_get_categories(api_client, category):
    url = reverse("category-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["slug"] == "test-category"

# ===============================
# 🔹 ТЕСТЫ ДЛЯ PhotoViewSet
# ===============================
@pytest.mark.django_db
def test_get_photos(api_client, photo):
    url = reverse("photo-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1

# ===============================
# 🔹 ТЕСТЫ ДЛЯ ItemDetail
# ===============================
@pytest.mark.django_db
def test_get_item_detail(api_client, item, category):
    item.categories.add(category)
    url = reverse("item-detail", kwargs={"category_slug": "test-category", "item_id": item.id})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "Test Item"

# ===============================
# 🔹 ТЕСТЫ ДЛЯ StockItemView
# ===============================
@pytest.mark.django_db
def test_get_stock_items(api_client, stock):
    url = reverse("stock-item-detail", kwargs={"item_id": stock.item.id})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["stock_items"]) == 1
    assert response.data["stock_items"][0]["quantity"] == 10
