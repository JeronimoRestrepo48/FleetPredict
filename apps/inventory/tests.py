from django.test import TestCase, Client
from django.urls import reverse

from apps.users.models import User
from .models import SparePart


class InventoryStockAdjustTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(
            email="manager@test.local",
            password="TestPass123!",
            first_name="Fleet",
            last_name="Manager",
            role=User.Role.FLEET_MANAGER,
        )
        self.driver = User.objects.create_user(
            email="driver@test.local",
            password="TestPass123!",
            first_name="Driver",
            last_name="User",
            role=User.Role.DRIVER,
        )
        self.part = SparePart.objects.create(
            name="Brake Pad",
            part_number="BP-100",
            unit_cost=10,
            reorder_point=3,
            current_stock=10,
            created_by=self.manager,
        )

    def test_fleet_manager_can_adjust_stock_out(self):
        self.client.force_login(self.manager)
        resp = self.client.post(
            reverse("inventory:stock_adjust"),
            data={
                "spare_part": self.part.pk,
                "movement_type": "out",
                "quantity": 4,
                "notes": "Usage in maintenance",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.part.refresh_from_db()
        self.assertEqual(self.part.current_stock, 6)

    def test_stock_never_goes_negative(self):
        self.client.force_login(self.manager)
        resp = self.client.post(
            reverse("inventory:stock_adjust"),
            data={
                "spare_part": self.part.pk,
                "movement_type": "out",
                "quantity": 1000,
                "notes": "Large consumption",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.part.refresh_from_db()
        self.assertEqual(self.part.current_stock, 0)

    def test_driver_cannot_adjust_stock(self):
        self.client.force_login(self.driver)
        resp = self.client.get(reverse("inventory:stock_adjust"))
        self.assertEqual(resp.status_code, 403)
