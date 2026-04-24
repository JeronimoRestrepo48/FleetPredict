from django.test import TestCase, Client
from django.urls import reverse

from apps.users.models import User
from .models import SparePart, Supplier, SupplierReview


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
        self.supplier = Supplier.objects.create(name="Proveedor Uno")

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

    def test_stock_in_can_capture_supplier_review(self):
        self.client.force_login(self.manager)
        resp = self.client.post(
            reverse("inventory:stock_adjust"),
            data={
                "spare_part": self.part.pk,
                "movement_type": "in",
                "quantity": 2,
                "notes": "Delivery received",
                "supplier_id": self.supplier.pk,
                "supplier_rating": 5,
                "supplier_comment": "Fast and complete delivery",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(SupplierReview.objects.filter(supplier=self.supplier, rating=5).exists())


class SupplierReviewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(
            email="manager2@test.local",
            password="TestPass123!",
            first_name="Fleet",
            last_name="Manager",
            role=User.Role.FLEET_MANAGER,
        )
        self.supplier = Supplier.objects.create(name="Proveedor Dos")

    def test_can_create_review_from_supplier_detail(self):
        self.client.force_login(self.manager)
        resp = self.client.post(
            reverse("inventory:supplier_review_create", kwargs={"pk": self.supplier.pk}),
            data={"rating": 4, "comment": "Reliable in last delivery"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.supplier.reviews.count(), 1)
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.rating_count, 1)
