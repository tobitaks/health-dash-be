"""
Unit tests for the medicines app.
"""

from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from apps.clinic.models import Clinic
from apps.medicines.models import Medicine
from apps.medicines.serializers import MedicineSerializer
from apps.users.models import CustomUser


class MedicineModelTestCase(TestCase):
    """Tests for the Medicine model."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.medicine = Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Paracetamol",
            brand_name="Biogesic",
            strength="500mg",
            form="tablet",
            category="analgesic",
        )

    def test_medicine_creation(self):
        """Medicine should be created with required fields."""
        self.assertEqual(self.medicine.generic_name, "Paracetamol")
        self.assertEqual(self.medicine.brand_name, "Biogesic")
        self.assertEqual(self.medicine.strength, "500mg")
        self.assertEqual(self.medicine.form, "tablet")
        self.assertEqual(self.medicine.category, "analgesic")

    def test_medicine_str_with_brand(self):
        """Medicine __str__ should include brand name if present."""
        expected = "Paracetamol (Biogesic) 500mg Tablet"
        self.assertEqual(str(self.medicine), expected)

    def test_medicine_str_without_brand(self):
        """Medicine __str__ should work without brand name."""
        medicine = Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Amoxicillin",
            strength="500mg",
            form="capsule",
        )
        expected = "Amoxicillin 500mg Capsule"
        self.assertEqual(str(medicine), expected)

    def test_medicine_defaults(self):
        """Medicine should have sensible defaults."""
        medicine = Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Test Medicine",
            strength="100mg",
            form="tablet",
        )
        self.assertEqual(medicine.brand_name, "")
        self.assertEqual(medicine.category, "other")
        self.assertEqual(medicine.default_sig, "")
        self.assertIsNone(medicine.default_quantity)
        self.assertEqual(medicine.notes, "")
        self.assertTrue(medicine.is_active)

    def test_display_name_property(self):
        """display_name should return formatted name without brand."""
        self.assertEqual(self.medicine.display_name, "Paracetamol 500mg Tablet")

    def test_full_name_property_with_brand(self):
        """full_name should include brand name."""
        self.assertEqual(self.medicine.full_name, "Paracetamol (Biogesic) 500mg Tablet")

    def test_full_name_property_without_brand(self):
        """full_name should work without brand name."""
        medicine = Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Ibuprofen",
            strength="400mg",
            form="tablet",
        )
        self.assertEqual(medicine.full_name, "Ibuprofen 400mg Tablet")

    def test_medicine_unique_together_constraint(self):
        """Same generic_name + strength + form in same clinic should raise IntegrityError."""
        with self.assertRaises(IntegrityError):
            Medicine.objects.create(
                clinic=self.clinic,
                generic_name="Paracetamol",
                brand_name="Different Brand",
                strength="500mg",
                form="tablet",
            )

    def test_medicine_same_generic_different_strength(self):
        """Same generic with different strength should be allowed."""
        medicine = Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Paracetamol",
            strength="250mg",  # Different strength
            form="tablet",
        )
        self.assertEqual(medicine.generic_name, "Paracetamol")
        self.assertEqual(medicine.strength, "250mg")

    def test_medicine_same_generic_different_form(self):
        """Same generic with different form should be allowed."""
        medicine = Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Paracetamol",
            strength="500mg",
            form="syrup",  # Different form
        )
        self.assertEqual(medicine.form, "syrup")

    def test_medicine_same_in_different_clinic(self):
        """Same medicine in different clinic should be allowed."""
        clinic2 = Clinic.objects.create(name="Another Clinic")
        medicine = Medicine.objects.create(
            clinic=clinic2,
            generic_name="Paracetamol",
            brand_name="Biogesic",
            strength="500mg",
            form="tablet",
        )
        self.assertEqual(medicine.generic_name, "Paracetamol")
        self.assertNotEqual(medicine.clinic, self.clinic)

    def test_form_choices(self):
        """All valid form choices should be accepted."""
        valid_forms = [
            "tablet",
            "capsule",
            "syrup",
            "suspension",
            "injection",
            "cream",
            "ointment",
            "gel",
            "drops",
            "inhaler",
            "nasal_spray",
            "powder",
            "softgel",
            "suppository",
            "patch",
            "solution",
            "lotion",
            "nebule",
        ]
        for i, form in enumerate(valid_forms):
            medicine = Medicine.objects.create(
                clinic=self.clinic,
                generic_name=f"Test Drug {i}",
                strength="100mg",
                form=form,
            )
            self.assertEqual(medicine.form, form)

    def test_category_choices(self):
        """All valid category choices should be accepted."""
        valid_categories = [
            "antibiotic",
            "analgesic",
            "antipyretic",
            "antihistamine",
            "antihypertensive",
            "antidiabetic",
            "antacid",
            "bronchodilator",
            "corticosteroid",
            "vitamin",
            "nsaid",
            "antiemetic",
            "antidiarrheal",
            "laxative",
            "antifungal",
            "antiviral",
            "cardiovascular",
            "cns",
            "dermatological",
            "ophthalmic",
            "otic",
            "other",
        ]
        for i, category in enumerate(valid_categories):
            medicine = Medicine.objects.create(
                clinic=self.clinic,
                generic_name=f"Category Drug {i}",
                strength="50mg",
                form="tablet",
                category=category,
            )
            self.assertEqual(medicine.category, category)

    def test_default_sig_field(self):
        """default_sig should store prescription instructions."""
        medicine = Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Metformin",
            strength="500mg",
            form="tablet",
            default_sig="Take 1 tablet twice daily after meals",
        )
        self.assertEqual(medicine.default_sig, "Take 1 tablet twice daily after meals")

    def test_default_quantity_field(self):
        """default_quantity should store default quantity."""
        medicine = Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Losartan",
            strength="50mg",
            form="tablet",
            default_quantity=30,
        )
        self.assertEqual(medicine.default_quantity, 30)

    def test_ordering(self):
        """Medicines should be ordered by generic_name, then strength."""
        Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Amoxicillin",
            strength="500mg",
            form="capsule",
        )
        Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Amoxicillin",
            strength="250mg",
            form="capsule",
        )
        medicines = list(Medicine.objects.filter(clinic=self.clinic))
        # Should be: Amoxicillin 250mg, Amoxicillin 500mg, Paracetamol 500mg
        self.assertEqual(medicines[0].generic_name, "Amoxicillin")
        self.assertEqual(medicines[0].strength, "250mg")
        self.assertEqual(medicines[1].generic_name, "Amoxicillin")
        self.assertEqual(medicines[1].strength, "500mg")
        self.assertEqual(medicines[2].generic_name, "Paracetamol")


class MedicineSerializerTestCase(TestCase):
    """Tests for the MedicineSerializer."""

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
        self.medicine = Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Paracetamol",
            brand_name="Biogesic",
            strength="500mg",
            form="tablet",
            category="analgesic",
            default_sig="Take 1 tablet every 4-6 hours as needed",
            default_quantity=20,
            notes="For fever and mild pain",
            is_active=True,
        )

    def get_mock_request(self):
        """Create a mock request with user context."""
        request = self.factory.get("/")
        request.user = self.user
        drf_request = Request(request)
        drf_request.user = self.user
        return drf_request

    def test_serializer_contains_expected_fields(self):
        """Serializer should contain all expected fields."""
        serializer = MedicineSerializer(self.medicine)
        data = serializer.data

        expected_fields = [
            "id",
            "generic_name",
            "brand_name",
            "strength",
            "form",
            "form_display",
            "category",
            "category_display",
            "default_sig",
            "default_quantity",
            "notes",
            "is_active",
            "display_name",
            "full_name",
            "created_at",
            "updated_at",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_data_values(self):
        """Serializer should return correct values."""
        serializer = MedicineSerializer(self.medicine)
        data = serializer.data

        self.assertEqual(data["generic_name"], "Paracetamol")
        self.assertEqual(data["brand_name"], "Biogesic")
        self.assertEqual(data["strength"], "500mg")
        self.assertEqual(data["form"], "tablet")
        self.assertEqual(data["category"], "analgesic")
        self.assertEqual(data["default_quantity"], 20)
        self.assertTrue(data["is_active"])

    def test_form_display_field(self):
        """form_display should return human-readable form."""
        serializer = MedicineSerializer(self.medicine)
        self.assertEqual(serializer.data["form_display"], "Tablet")

    def test_category_display_field(self):
        """category_display should return human-readable category."""
        serializer = MedicineSerializer(self.medicine)
        self.assertEqual(serializer.data["category_display"], "Analgesic/Pain Reliever")

    def test_display_name_field(self):
        """display_name should be included."""
        serializer = MedicineSerializer(self.medicine)
        self.assertEqual(serializer.data["display_name"], "Paracetamol 500mg Tablet")

    def test_full_name_field(self):
        """full_name should be included."""
        serializer = MedicineSerializer(self.medicine)
        self.assertEqual(serializer.data["full_name"], "Paracetamol (Biogesic) 500mg Tablet")

    def test_create_sets_clinic_from_request(self):
        """create should set clinic from request context."""
        data = {
            "generic_name": "Amoxicillin",
            "strength": "500mg",
            "form": "capsule",
            "category": "antibiotic",
        }
        serializer = MedicineSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        medicine = serializer.save()
        self.assertEqual(medicine.clinic, self.clinic)

    def test_serializer_valid_data(self):
        """Serializer should validate correct data."""
        data = {
            "generic_name": "Ibuprofen",
            "strength": "400mg",
            "form": "tablet",
            "category": "nsaid",
        }
        serializer = MedicineSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_missing_required_fields(self):
        """Serializer should fail without required fields."""
        data = {"brand_name": "Some Brand"}
        serializer = MedicineSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("generic_name", serializer.errors)
        self.assertIn("strength", serializer.errors)
        self.assertIn("form", serializer.errors)

    def test_serializer_invalid_form_choice(self):
        """Serializer should reject invalid form choice."""
        data = {
            "generic_name": "Test Drug",
            "strength": "100mg",
            "form": "invalid_form",
        }
        serializer = MedicineSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("form", serializer.errors)

    def test_serializer_invalid_category_choice(self):
        """Serializer should reject invalid category choice."""
        data = {
            "generic_name": "Test Drug",
            "strength": "100mg",
            "form": "tablet",
            "category": "invalid_category",
        }
        serializer = MedicineSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("category", serializer.errors)

    def test_serializer_update(self):
        """Serializer should update existing medicine."""
        data = {
            "generic_name": "Paracetamol",
            "brand_name": "Updated Brand",
            "strength": "500mg",
            "form": "tablet",
            "is_active": False,
        }
        serializer = MedicineSerializer(self.medicine, data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.brand_name, "Updated Brand")
        self.assertFalse(updated.is_active)

    def test_serializer_partial_update(self):
        """Serializer should support partial updates."""
        data = {"is_active": False}
        serializer = MedicineSerializer(
            self.medicine,
            data=data,
            partial=True,
            context={"request": self.get_mock_request()},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertFalse(updated.is_active)
        self.assertEqual(updated.generic_name, "Paracetamol")  # Unchanged
