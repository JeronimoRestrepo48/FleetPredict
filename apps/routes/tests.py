from django.test import TestCase, Client
from django.urls import reverse

from apps.users.models import User
from apps.vehicles.models import Vehicle
from .models import Route, RouteSuggestion


class RoutesAuthorizationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.driver_a = User.objects.create_user(
            email="drivera@test.local",
            password="TestPass123!",
            first_name="Driver",
            last_name="A",
            role=User.Role.DRIVER,
        )
        self.driver_b = User.objects.create_user(
            email="driverb@test.local",
            password="TestPass123!",
            first_name="Driver",
            last_name="B",
            role=User.Role.DRIVER,
        )
        self.vehicle_a = Vehicle.objects.create(
            license_plate="RA-100",
            vin="1HGBH41JXMN109100",
            make="Ford",
            model="Transit",
            year=2021,
            assigned_driver=self.driver_a,
        )
        self.vehicle_b = Vehicle.objects.create(
            license_plate="RB-200",
            vin="1HGBH41JXMN109200",
            make="Chevrolet",
            model="N400",
            year=2022,
            assigned_driver=self.driver_b,
        )
        self.route_a = Route.objects.create(
            vehicle=self.vehicle_a,
            origin="A",
            destination="B",
            created_by=self.driver_a,
        )
        self.suggestion_a = RouteSuggestion.objects.create(
            route=self.route_a,
            alternative_number=1,
            distance_km=10.5,
            estimated_time_min=20,
            fuel_cost=6.2,
            recommended=True,
        )

    def test_driver_cannot_open_other_driver_route_suggestions(self):
        self.client.force_login(self.driver_b)
        resp = self.client.get(reverse("routes:suggestions", kwargs={"pk": self.route_a.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_driver_cannot_select_other_driver_suggestion(self):
        self.client.force_login(self.driver_b)
        resp = self.client.post(reverse("routes:select", kwargs={"pk": self.suggestion_a.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_owner_driver_can_select_own_suggestion(self):
        self.client.force_login(self.driver_a)
        resp = self.client.post(reverse("routes:select", kwargs={"pk": self.suggestion_a.pk}))
        self.assertEqual(resp.status_code, 302)
        self.route_a.refresh_from_db()
        self.suggestion_a.refresh_from_db()
        self.assertEqual(self.route_a.status, Route.Status.SELECTED)
        self.assertTrue(self.suggestion_a.selected)
