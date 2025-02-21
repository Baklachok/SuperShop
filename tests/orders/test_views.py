import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from orders.models import Order, OrderItem, ItemStock
from authentication.models import FrontendUser  # Импортируй модель пользователя, если она используется
from api.models import Item

@pytest.mark.django_db
class TestOrdersViewSet:
    def setup_method(self):
        self.client = APIClient()
        self.user = FrontendUser.objects.create_user(
            telNo="+79894567890", password="testpassword123"
        )
        self.client.force_authenticate(user=self.user)  # Аутентифицируем пользователя

    def test_create_order(self):
        """Тест создания нового заказа."""
        url = reverse("orders:orders-list")  # URL для создания заказа
        print(f"User ID in test: {self.user.id}")
        data = {
            "user": self.user.id,  # Связываем заказ с пользователем
            "total_price": 5000,
            "status": "created"  # Используем допустимое значение
        }
        response = self.client.post(url, data, format="json")
        print(response.data)  # Отладочный вывод

        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1
        assert response.data["status"] == "created"  # Проверяем сохранённый статус


    def test_get_orders_list(self):
        """Тест получения списка заказов."""
        Order.objects.create(user=self.user, status="created")
        Order.objects.create(user=self.user, status="completed")

        url = reverse("orders:orders-list")  # URL для списка заказов
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2  # Проверяем, что вернулись два заказа

    def test_get_order_items(self):
        """Тест получения списка товаров в заказе."""
        order = Order.objects.create(user=self.user, status="created")

        item_stock1 = ItemStock.objects.create(
            item=Item.objects.create(name="Товар 1", price=1000),  # Создаём товар
            quantity=10  # Задаём количество на складе
        )

        item_stock2 = ItemStock.objects.create(
            item=Item.objects.create(name="Товар 2", price=2000),  # Создаём товар
            quantity=10  # Задаём количество на складе
        )

        item1 = OrderItem.objects.create(order=order, product=item_stock1, quantity=2)

        item2 = OrderItem.objects.create(order=order, product=item_stock2, quantity=1)

        url  = reverse("orders:orders-items", kwargs={"pk": order.pk})

        response = self.client.get(url)
        print(response.data)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]["product"] == item1.product.id
        assert response.data[1]["product"] == item2.product.id
