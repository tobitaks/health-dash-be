"""
Unit tests for the clinic app.
"""

from decimal import Decimal

from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from apps.clinic.models import Clinic, Service
from apps.clinic.serializers import (
    ClinicCreateSerializer,
    ClinicSerializer,
    ServiceCreateUpdateSerializer,
    ServiceSerializer,
)
from apps.users.models import CustomUser


class ClinicModelTestCase(TestCase):
    """Tests for the Clinic model."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(
            name="Test Medical Center",
            email="info@testclinic.com",
            phone="+63 2 1234 5678",
            address_street="123 Main Street",
            address_city="Manila",
            address_region="Metro Manila",
            address_postal_code="1000",
        )

    def test_clinic_creation(self):
        """Clinic should be created with required fields."""
        self.assertEqual(self.clinic.name, "Test Medical Center")
        self.assertEqual(self.clinic.email, "info@testclinic.com")
        self.assertTrue(self.clinic.is_active)

    def test_clinic_str(self):
        """Clinic __str__ should return name."""
        self.assertEqual(str(self.clinic), "Test Medical Center")

    def test_clinic_defaults(self):
        """Clinic should have sensible defaults."""
        clinic = Clinic.objects.create(name="Simple Clinic")
        self.assertEqual(clinic.address_country, "Philippines")
        self.assertEqual(clinic.timezone, "Asia/Manila")
        self.assertEqual(clinic.currency, "PHP")
        self.assertTrue(clinic.is_active)
        self.assertEqual(clinic.business_hours, {})

    def test_full_address_property(self):
        """full_address should return formatted address."""
        expected = "123 Main Street, Manila, Metro Manila, 1000, Philippines"
        self.assertEqual(self.clinic.full_address, expected)

    def test_full_address_with_missing_parts(self):
        """full_address should handle missing address parts."""
        clinic = Clinic.objects.create(
            name="Minimal Clinic",
            address_city="Cebu",
            address_country="Philippines",
        )
        self.assertEqual(clinic.full_address, "Cebu, Philippines")

    def test_owner_property_with_owner(self):
        """owner property should return clinic owner."""
        owner = CustomUser.objects.create_user(
            username="owner",
            email="owner@clinic.com",
            password="testpass123",
            clinic=self.clinic,
            is_owner=True,
        )
        self.assertEqual(self.clinic.owner, owner)

    def test_owner_property_without_owner(self):
        """owner property should return None if no owner."""
        self.assertIsNone(self.clinic.owner)

    def test_staff_count_property(self):
        """staff_count should return active staff count."""
        # Create active staff
        for i in range(3):
            CustomUser.objects.create_user(
                username=f"staff{i}",
                email=f"staff{i}@clinic.com",
                password="testpass123",
                clinic=self.clinic,
                is_active=True,
            )
        # Create inactive staff
        CustomUser.objects.create_user(
            username="inactive",
            email="inactive@clinic.com",
            password="testpass123",
            clinic=self.clinic,
            is_active=False,
        )
        self.assertEqual(self.clinic.staff_count, 3)

    def test_staff_count_empty(self):
        """staff_count should return 0 for clinic with no staff."""
        self.assertEqual(self.clinic.staff_count, 0)

    def test_business_hours_json_field(self):
        """business_hours should store JSON data correctly."""
        hours = {
            "monday": {"open": "09:00", "close": "17:00"},
            "tuesday": {"open": "09:00", "close": "17:00"},
            "saturday": {"open": "09:00", "close": "12:00"},
            "sunday": None,
        }
        self.clinic.business_hours = hours
        self.clinic.save()
        self.clinic.refresh_from_db()
        self.assertEqual(self.clinic.business_hours, hours)


class ServiceModelTestCase(TestCase):
    """Tests for the Service model."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.service = Service.objects.create(
            clinic=self.clinic,
            name="General Consultation",
            code="GC001",
            price=Decimal("500.00"),
            duration_minutes=30,
        )

    def test_service_creation(self):
        """Service should be created with required fields."""
        self.assertEqual(self.service.name, "General Consultation")
        self.assertEqual(self.service.code, "GC001")
        self.assertEqual(self.service.price, Decimal("500.00"))
        self.assertEqual(self.service.duration_minutes, 30)

    def test_service_str(self):
        """Service __str__ should return code and name."""
        self.assertEqual(str(self.service), "GC001 - General Consultation")

    def test_service_defaults(self):
        """Service should have sensible defaults."""
        service = Service.objects.create(
            clinic=self.clinic,
            name="Quick Check",
            code="QC001",
            price=Decimal("300.00"),
        )
        self.assertEqual(service.duration_minutes, 30)
        self.assertTrue(service.is_active)

    def test_service_unique_together_constraint(self):
        """Same code in same clinic should raise IntegrityError."""
        with self.assertRaises(IntegrityError):
            Service.objects.create(
                clinic=self.clinic,
                name="Another Service",
                code="GC001",  # Duplicate
                price=Decimal("400.00"),
            )

    def test_service_same_code_different_clinic(self):
        """Same code in different clinic should be allowed."""
        clinic2 = Clinic.objects.create(name="Another Clinic")
        service2 = Service.objects.create(
            clinic=clinic2,
            name="Consultation",
            code="GC001",  # Same code, different clinic
            price=Decimal("600.00"),
        )
        self.assertEqual(service2.code, "GC001")
        self.assertNotEqual(service2.clinic, self.service.clinic)

    def test_service_price_decimal(self):
        """Service price should handle decimal values correctly."""
        service = Service.objects.create(
            clinic=self.clinic,
            name="Special Service",
            code="SS001",
            price=Decimal("1234.56"),
        )
        self.assertEqual(service.price, Decimal("1234.56"))

    def test_service_ordering(self):
        """Services should be ordered by name."""
        Service.objects.create(
            clinic=self.clinic, name="Zebra Service", code="ZS001", price=Decimal("100.00")
        )
        Service.objects.create(
            clinic=self.clinic, name="Alpha Service", code="AS001", price=Decimal("100.00")
        )
        services = list(Service.objects.filter(clinic=self.clinic))
        self.assertEqual(services[0].name, "Alpha Service")
        self.assertEqual(services[1].name, "General Consultation")
        self.assertEqual(services[2].name, "Zebra Service")


class ClinicSerializerTestCase(TestCase):
    """Tests for the ClinicSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(
            name="Test Clinic",
            email="info@test.com",
            phone="+63 2 1234 5678",
            address_street="123 Main St",
            address_city="Manila",
        )
        self.owner = CustomUser.objects.create_user(
            username="owner",
            email="owner@test.com",
            password="testpass123",
            first_name="John",
            last_name="Owner",
            clinic=self.clinic,
            is_owner=True,
        )

    def test_serializer_contains_expected_fields(self):
        """Serializer should contain all expected fields."""
        serializer = ClinicSerializer(self.clinic)
        data = serializer.data

        expected_fields = [
            "id",
            "name",
            "email",
            "phone",
            "website",
            "address_street",
            "address_city",
            "address_region",
            "address_postal_code",
            "address_country",
            "full_address",
            "business_hours",
            "logo",
            "timezone",
            "currency",
            "is_active",
            "owner",
            "staff_count",
            "created_at",
            "updated_at",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_owner_field(self):
        """owner field should contain owner info."""
        serializer = ClinicSerializer(self.clinic)
        owner_data = serializer.data["owner"]

        self.assertEqual(owner_data["id"], self.owner.id)
        self.assertEqual(owner_data["email"], "owner@test.com")
        self.assertEqual(owner_data["first_name"], "John")
        self.assertEqual(owner_data["last_name"], "Owner")

    def test_serializer_owner_none(self):
        """owner field should be None if no owner."""
        clinic = Clinic.objects.create(name="No Owner Clinic")
        serializer = ClinicSerializer(clinic)
        self.assertIsNone(serializer.data["owner"])

    def test_serializer_staff_count(self):
        """staff_count should be included."""
        serializer = ClinicSerializer(self.clinic)
        self.assertEqual(serializer.data["staff_count"], 1)  # Just the owner

    def test_serializer_full_address(self):
        """full_address should be included."""
        serializer = ClinicSerializer(self.clinic)
        self.assertIn("123 Main St", serializer.data["full_address"])
        self.assertIn("Manila", serializer.data["full_address"])


class ClinicCreateSerializerTestCase(TestCase):
    """Tests for the ClinicCreateSerializer."""

    def test_valid_data(self):
        """Serializer should validate with just name."""
        data = {"name": "New Clinic"}
        serializer = ClinicCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_name_required(self):
        """name field should be required."""
        serializer = ClinicCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_create_clinic(self):
        """Serializer should create clinic with name only."""
        data = {"name": "Created Clinic"}
        serializer = ClinicCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        clinic = serializer.save()
        self.assertEqual(clinic.name, "Created Clinic")


class ServiceSerializerTestCase(TestCase):
    """Tests for the ServiceSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.service = Service.objects.create(
            clinic=self.clinic,
            name="Consultation",
            code="CON001",
            price=Decimal("500.00"),
            duration_minutes=45,
            is_active=True,
        )

    def test_serializer_contains_expected_fields(self):
        """Serializer should contain all expected fields."""
        serializer = ServiceSerializer(self.service)
        data = serializer.data

        expected_fields = [
            "id",
            "name",
            "code",
            "price",
            "duration_minutes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_data_values(self):
        """Serializer should return correct values."""
        serializer = ServiceSerializer(self.service)
        data = serializer.data

        self.assertEqual(data["name"], "Consultation")
        self.assertEqual(data["code"], "CON001")
        self.assertEqual(Decimal(data["price"]), Decimal("500.00"))
        self.assertEqual(data["duration_minutes"], 45)
        self.assertTrue(data["is_active"])


class ServiceCreateUpdateSerializerTestCase(TestCase):
    """Tests for the ServiceCreateUpdateSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            clinic=self.clinic,
        )
        self.valid_data = {
            "name": "New Service",
            "code": "NS001",
            "price": "350.00",
            "duration_minutes": 30,
        }

    def get_mock_request(self):
        """Create a mock request with user context."""
        request = self.factory.get("/")
        request.user = self.user
        drf_request = Request(request)
        drf_request.user = self.user
        return drf_request

    def test_valid_data_is_valid(self):
        """Serializer should validate with valid data."""
        serializer = ServiceCreateUpdateSerializer(
            data=self.valid_data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_required_fields(self):
        """Serializer should fail without required fields."""
        serializer = ServiceCreateUpdateSerializer(
            data={}, context={"request": self.get_mock_request()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)
        self.assertIn("code", serializer.errors)
        self.assertIn("price", serializer.errors)

    def test_code_normalized_to_uppercase(self):
        """Code should be normalized to uppercase."""
        data = self.valid_data.copy()
        data["code"] = "lowercase"
        serializer = ServiceCreateUpdateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["code"], "LOWERCASE")

    def test_duplicate_code_in_same_clinic_invalid(self):
        """Duplicate code in same clinic should fail."""
        Service.objects.create(
            clinic=self.clinic,
            name="Existing Service",
            code="NS001",
            price=Decimal("200.00"),
        )
        serializer = ServiceCreateUpdateSerializer(
            data=self.valid_data, context={"request": self.get_mock_request()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("code", serializer.errors)

    def test_duplicate_code_case_insensitive(self):
        """Code uniqueness check should be case-insensitive."""
        Service.objects.create(
            clinic=self.clinic,
            name="Existing Service",
            code="NS001",
            price=Decimal("200.00"),
        )
        data = self.valid_data.copy()
        data["code"] = "ns001"  # lowercase version
        serializer = ServiceCreateUpdateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("code", serializer.errors)

    def test_update_allows_same_code(self):
        """Update should allow keeping the same code."""
        service = Service.objects.create(
            clinic=self.clinic,
            name="Original Service",
            code="ORIG001",
            price=Decimal("200.00"),
        )
        data = {"name": "Updated Name", "code": "ORIG001", "price": "250.00"}
        serializer = ServiceCreateUpdateSerializer(
            service, data=data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_partial_update(self):
        """Serializer should support partial updates."""
        service = Service.objects.create(
            clinic=self.clinic,
            name="Original Service",
            code="ORIG001",
            price=Decimal("200.00"),
        )
        data = {"price": "300.00"}
        serializer = ServiceCreateUpdateSerializer(
            service,
            data=data,
            partial=True,
            context={"request": self.get_mock_request()},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.price, Decimal("300.00"))
        self.assertEqual(updated.name, "Original Service")  # Unchanged

    def test_is_active_default(self):
        """is_active should default to True if not provided."""
        serializer = ServiceCreateUpdateSerializer(
            data=self.valid_data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        service = serializer.save(clinic=self.clinic)
        self.assertTrue(service.is_active)


class ClinicAdminTestCase(TestCase):
    """Tests for the Clinic admin configuration."""

    def setUp(self):
        """Set up test fixtures."""
        from django.contrib.admin.sites import AdminSite

        from apps.clinic.admin import ClinicAdmin

        self.site = AdminSite()
        self.admin = ClinicAdmin(Clinic, self.site)
        self.clinic = Clinic.objects.create(
            name="Test Clinic",
            email="test@clinic.com",
            phone="+63 2 1234 5678",
            address_street="123 Main St",
            address_city="Manila",
            address_region="Metro Manila",
        )

    def test_list_display_fields_exist(self):
        """All fields in list_display should exist on the model."""
        for field in self.admin.list_display:
            if field == "__str__":
                continue
            self.assertTrue(
                hasattr(Clinic, field) or hasattr(self.admin, field),
                f"Field '{field}' in list_display does not exist on Clinic model",
            )

    def test_list_filter_fields_exist(self):
        """All fields in list_filter should exist on the model."""
        for field in self.admin.list_filter:
            self.assertTrue(
                hasattr(Clinic, field),
                f"Field '{field}' in list_filter does not exist on Clinic model",
            )

    def test_search_fields_valid(self):
        """All fields in search_fields should be valid."""
        for field in self.admin.search_fields:
            # Remove lookup suffixes like __icontains
            base_field = field.split("__")[0]
            self.assertTrue(
                hasattr(Clinic, base_field),
                f"Field '{base_field}' in search_fields does not exist on Clinic model",
            )

    def test_fieldsets_fields_exist(self):
        """All fields in fieldsets should exist on the model."""
        for fieldset_name, fieldset_options in self.admin.fieldsets:
            for field in fieldset_options.get("fields", []):
                self.assertTrue(
                    hasattr(Clinic, field),
                    f"Field '{field}' in fieldset '{fieldset_name}' does not exist on Clinic model",
                )

    def test_readonly_fields_exist(self):
        """All readonly_fields should exist on the model."""
        for field in self.admin.readonly_fields:
            self.assertTrue(
                hasattr(Clinic, field),
                f"Field '{field}' in readonly_fields does not exist on Clinic model",
            )
