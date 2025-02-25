import pytest
from django.urls import reverse
from rest_framework import status
from purchases.models import Basket, BasketItem, Payment, Favourites, FavouritesItem
from rest_framework.test import APIClient
from authentication.models import FrontendUser
from api.models import Item, ItemStock, Color, Size

@pytest.fixture
def api_client():
    """Возвращает API-клиент для тестирования."""
    return APIClient()

@pytest.fixture
def user(db):
    """Создает и возвращает тестового пользователя."""
    return FrontendUser.objects.create_user(telNo="+79894567890", password="testpassword")

@pytest.fixture
def basket(user):
    """Создает корзину для пользователя."""
    return Basket.objects.create(user=user)


@pytest.fixture
def color(db):
    """Создает цвет."""
    return Color.objects.create(name="Red")


@pytest.fixture
def size(db):
    """Создает размер."""
    return Size.objects.create(name="M")


@pytest.fixture
def item(db):
    """Создает тестовый товар."""
    return Item.objects.create(name="Test Item", price=1000)


@pytest.fixture
def item_stock(db, item, color, size):
    return ItemStock.objects.create(item=item, color=color, size=size, quantity=10)


@pytest.fixture
def basket_item(basket, item_stock):
    """Добавляет товар в корзину пользователя."""
    return BasketItem.objects.create(basket=basket, product=item_stock, quantity=1)


@pytest.fixture
def favourites(user):
    """Создает список избранного для пользователя."""
    return Favourites.objects.create(user=user)

@pytest.mark.django_db
class TestBasketViewSet:

    def test_get_basket(self, api_client, user, basket):
        """Тест получения корзины пользователя."""
        api_client.force_authenticate(user=user)
        url = reverse("purchases:basket-list")
        response = api_client.get(url)
        print(response.data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_add_to_basket(self, api_client, user, basket, item_stock):
        """Тест добавления товара в корзину."""
        api_client.force_authenticate(user=user)
        url = reverse("purchases:add-to-cart")
        data = {
            "item_id": item_stock.item.id,  # Используем item.id вместо item_stock.id
            "color": item_stock.color.name,
            "size": item_stock.size.name,
            "quantity": 2
        }
        print(f"Создан ItemStock: {item_stock.id}, {item_stock.item.name}, {item_stock.color.name}, {item_stock.size.name}, {item_stock.quantity}")
        print(f"Отправляем запрос с item_id={data['item_id']}")
        response = api_client.post(url, data, format="json")
        print(response)

        assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.django_db
class TestUpdateBasketItemView:

    def test_update_basket_item(self, api_client, user, basket_item):
        """Тест обновления количества товара в корзине."""
        api_client.force_authenticate(user=user)
        url = reverse("purchases:update-cart-item", kwargs={"item_id": basket_item.id})
        data = {"quantity": 3}
        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        basket_item.refresh_from_db()
        assert basket_item.quantity == 3


@pytest.mark.django_db
class TestCreatePaymentView:

    def test_create_payment(self, api_client, user, basket, basket_item):
        """Тест создания платежа."""
        api_client.force_authenticate(user=user)
        url = reverse("purchases:create-payment")
        data = {"basket_id": basket.id, "amount": 1}
        response = api_client.post(url, data, format="json")
        print(response)

        assert response.status_code == status.HTTP_201_CREATED
        assert Payment.objects.count() == 1


@pytest.mark.django_db
class TestFavouritesViewSet:

    def test_add_to_favourites(self, api_client, user, item_stock):
        """Тест добавления товара в избранное."""
        api_client.force_authenticate(user=user)
        url = reverse("purchases:favourites-add-item")
        data = {"product_id": item_stock.id}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert FavouritesItem.objects.count() == 1


@pytest.mark.django_db
class TestPaymentsViewSet:

    def test_create_payment(self, api_client, user, basket):
        """Тест создания платежа."""
        api_client.force_authenticate(user=user)

        url = reverse("purchases:payment-list")
        data = {"basket_id": basket.id, "amount": 1000}

        response = api_client.post(url, data, format="json")
        print(response.data)  # Проверить, что вернул сервер

        assert response.status_code == status.HTTP_201_CREATED


