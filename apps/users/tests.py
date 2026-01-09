"""
Unit tests for the users app.
"""

from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from apps.clinic.models import Clinic
from apps.users.models import CustomUser, Policy, Role, RolePolicy, UserRole
from apps.users.serializers import (
    CustomUserSerializer,
    LoginSerializer,
    PolicySerializer,
    RegisterSerializer,
    RoleCreateUpdateSerializer,
    RoleSerializer,
    StaffCreateSerializer,
    StaffListSerializer,
    StaffUpdateSerializer,
    UpdateProfileSerializer,
    UserRoleSerializer,
    UserWithRolesSerializer,
)


class CustomUserModelTestCase(TestCase):
    """Tests for the CustomUser model."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            clinic=self.clinic,
            role=CustomUser.Role.DOCTOR,
            is_owner=True,
        )

    def test_user_creation(self):
        """User should be created with required fields."""
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Doe")
        self.assertEqual(self.user.clinic, self.clinic)
        self.assertEqual(self.user.role, CustomUser.Role.DOCTOR)
        self.assertTrue(self.user.is_owner)

    def test_user_str(self):
        """User __str__ should return full name and email."""
        expected = "John Doe <test@example.com>"
        self.assertEqual(str(self.user), expected)

    def test_user_str_no_name(self):
        """User __str__ should work without name."""
        user = CustomUser.objects.create_user(
            username="noname",
            email="noname@example.com",
            password="testpass123",
        )
        self.assertEqual(str(user), " <noname@example.com>")

    def test_get_display_name_with_name(self):
        """get_display_name should return full name when present."""
        self.assertEqual(self.user.get_display_name(), "John Doe")

    def test_get_display_name_without_name(self):
        """get_display_name should return email when no name."""
        user = CustomUser.objects.create_user(
            username="noname",
            email="noname@example.com",
            password="testpass123",
        )
        self.assertEqual(user.get_display_name(), "noname@example.com")

    def test_avatar_url_without_avatar(self):
        """avatar_url should return gravatar URL when no avatar."""
        self.assertIn("gravatar.com", self.user.avatar_url)
        self.assertIn(self.user.gravatar_id, self.user.avatar_url)

    def test_gravatar_id(self):
        """gravatar_id should be MD5 hash of lowercase email."""
        import hashlib

        expected = hashlib.md5(b"test@example.com").hexdigest()
        self.assertEqual(self.user.gravatar_id, expected)

    def test_role_choices(self):
        """All role choices should be valid."""
        valid_roles = ["Admin", "Doctor", "Nurse", "Secretary", "Cashier"]
        for role in valid_roles:
            user = CustomUser.objects.create_user(
                username=f"user_{role}",
                email=f"{role}@example.com",
                password="testpass123",
                role=role,
            )
            self.assertEqual(user.role, role)

    def test_user_defaults(self):
        """User should have sensible defaults."""
        user = CustomUser.objects.create_user(
            username="minimal",
            email="minimal@example.com",
            password="testpass123",
        )
        self.assertEqual(user.role, CustomUser.Role.ADMIN)
        self.assertFalse(user.is_owner)
        self.assertIsNone(user.clinic)
        self.assertEqual(user.timezone, "")

    def test_get_permissions_without_roles(self):
        """get_permissions should return empty set without roles."""
        permissions = self.user.get_permissions()
        self.assertEqual(permissions, set())

    def test_get_permissions_with_admin_role(self):
        """get_permissions should return wildcard for admin role."""
        role = Role.objects.create(
            name="Administrator",
            slug="administrator",
            clinic=self.clinic,
            is_admin=True,
        )
        UserRole.objects.create(user=self.user, role=role)
        permissions = self.user.get_permissions()
        self.assertEqual(permissions, {"*"})

    def test_get_permissions_with_policies(self):
        """get_permissions should return policy codes."""
        role = Role.objects.create(
            name="Doctor",
            slug="doctor",
            clinic=self.clinic,
            is_admin=False,
        )
        policy1, _ = Policy.objects.get_or_create(
            code="patients.view",
            defaults={"name": "View Patients", "category": "Patients"},
        )
        policy2, _ = Policy.objects.get_or_create(
            code="patients.edit",
            defaults={"name": "Edit Patients", "category": "Patients"},
        )
        RolePolicy.objects.create(role=role, policy=policy1)
        RolePolicy.objects.create(role=role, policy=policy2)
        UserRole.objects.create(user=self.user, role=role)

        permissions = self.user.get_permissions()
        self.assertIn("patients.view", permissions)
        self.assertIn("patients.edit", permissions)

    def test_has_permission_with_admin_role(self):
        """has_permission should return True for admin role."""
        role = Role.objects.create(
            name="Administrator",
            slug="administrator",
            clinic=self.clinic,
            is_admin=True,
        )
        UserRole.objects.create(user=self.user, role=role)
        self.assertTrue(self.user.has_permission("any.permission"))

    def test_has_permission_with_specific_policy(self):
        """has_permission should check specific policy codes."""
        role = Role.objects.create(
            name="Doctor",
            slug="doctor",
            clinic=self.clinic,
        )
        policy, _ = Policy.objects.get_or_create(
            code="patients.view",
            defaults={"name": "View Patients", "category": "Patients"},
        )
        RolePolicy.objects.create(role=role, policy=policy)
        UserRole.objects.create(user=self.user, role=role)

        self.assertTrue(self.user.has_permission("patients.view"))
        self.assertFalse(self.user.has_permission("patients.delete"))


class PolicyModelTestCase(TestCase):
    """Tests for the Policy model."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a unique code for this test class
        self.policy, _ = Policy.objects.get_or_create(
            code="policy_test.view",
            defaults={"name": "View Test", "category": "PolicyTest"},
        )

    def test_policy_creation(self):
        """Policy should be created with required fields."""
        self.assertEqual(self.policy.code, "policy_test.view")
        self.assertEqual(self.policy.name, "View Test")
        self.assertEqual(self.policy.category, "PolicyTest")

    def test_policy_str(self):
        """Policy __str__ should return category and name."""
        self.assertEqual(str(self.policy), "PolicyTest: View Test")

    def test_policy_code_unique(self):
        """Policy code should be unique."""
        # First ensure the policy exists
        Policy.objects.get_or_create(
            code="policy_unique_test",
            defaults={"name": "Unique Test", "category": "Test"},
        )
        with self.assertRaises(IntegrityError):
            Policy.objects.create(
                code="policy_unique_test",  # Duplicate
                name="Another Policy",
                category="Test",
            )

    def test_policy_ordering(self):
        """Policies should be ordered by category, then name."""
        Policy.objects.get_or_create(
            code="ordering_billing.view",
            defaults={"name": "View Bills", "category": "AABilling"},
        )
        Policy.objects.get_or_create(
            code="ordering_patients.edit",
            defaults={"name": "Edit Patients", "category": "ABPatients"},
        )
        Policy.objects.get_or_create(
            code="ordering_patients.view",
            defaults={"name": "View Patients", "category": "ABPatients"},
        )

        policies = list(Policy.objects.filter(code__startswith="ordering_"))
        self.assertEqual(policies[0].category, "AABilling")
        self.assertEqual(policies[1].category, "ABPatients")
        self.assertEqual(policies[1].name, "Edit Patients")
        self.assertEqual(policies[2].name, "View Patients")


class RoleModelTestCase(TestCase):
    """Tests for the Role model."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.role = Role.objects.create(
            name="Doctor",
            slug="doctor",
            description="Medical staff",
            clinic=self.clinic,
            is_system=False,
            is_admin=False,
            color="#3b82f6",
            icon="Stethoscope",
        )

    def test_role_creation(self):
        """Role should be created with required fields."""
        self.assertEqual(self.role.name, "Doctor")
        self.assertEqual(self.role.slug, "doctor")
        self.assertEqual(self.role.clinic, self.clinic)
        self.assertFalse(self.role.is_admin)

    def test_role_str(self):
        """Role __str__ should return name and clinic."""
        self.assertEqual(str(self.role), "Doctor (Test Clinic)")

    def test_role_defaults(self):
        """Role should have sensible defaults."""
        role = Role.objects.create(
            name="Minimal Role",
            slug="minimal",
            clinic=self.clinic,
        )
        self.assertFalse(role.is_system)
        self.assertFalse(role.is_admin)
        self.assertEqual(role.color, "#6b7280")
        self.assertEqual(role.icon, "User")

    def test_role_unique_together(self):
        """Same slug in same clinic should raise IntegrityError."""
        with self.assertRaises(IntegrityError):
            Role.objects.create(
                name="Another Doctor",
                slug="doctor",  # Duplicate slug
                clinic=self.clinic,
            )

    def test_role_same_slug_different_clinic(self):
        """Same slug in different clinic should be allowed."""
        clinic2 = Clinic.objects.create(name="Another Clinic")
        role = Role.objects.create(
            name="Doctor",
            slug="doctor",
            clinic=clinic2,
        )
        self.assertEqual(role.slug, "doctor")
        self.assertNotEqual(role.clinic, self.clinic)

    def test_get_policies(self):
        """get_policies should return attached policies."""
        policy1, _ = Policy.objects.get_or_create(
            code="role_test.view",
            defaults={"name": "View Test", "category": "RoleTest"},
        )
        policy2, _ = Policy.objects.get_or_create(
            code="role_test.edit",
            defaults={"name": "Edit Test", "category": "RoleTest"},
        )
        RolePolicy.objects.create(role=self.role, policy=policy1)
        RolePolicy.objects.create(role=self.role, policy=policy2)

        policies = self.role.get_policies()
        self.assertEqual(policies.count(), 2)
        self.assertIn(policy1, policies)
        self.assertIn(policy2, policies)

    def test_get_policy_codes(self):
        """get_policy_codes should return list of codes."""
        policy, _ = Policy.objects.get_or_create(
            code="role_codes_test.view",
            defaults={"name": "View Test", "category": "RoleCodesTest"},
        )
        RolePolicy.objects.create(role=self.role, policy=policy)

        codes = self.role.get_policy_codes()
        self.assertEqual(codes, ["role_codes_test.view"])

    def test_get_policy_codes_admin_role(self):
        """Admin role should return wildcard."""
        admin_role = Role.objects.create(
            name="Admin",
            slug="admin",
            clinic=self.clinic,
            is_admin=True,
        )
        codes = admin_role.get_policy_codes()
        self.assertEqual(codes, ["*"])


class RolePolicyModelTestCase(TestCase):
    """Tests for the RolePolicy model."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.role = Role.objects.create(
            name="Doctor",
            slug="doctor",
            clinic=self.clinic,
        )
        self.policy, _ = Policy.objects.get_or_create(
            code="rolepolicy_test.view",
            defaults={"name": "View Test", "category": "RolePolicyTest"},
        )
        self.role_policy = RolePolicy.objects.create(
            role=self.role,
            policy=self.policy,
        )

    def test_role_policy_creation(self):
        """RolePolicy should be created correctly."""
        self.assertEqual(self.role_policy.role, self.role)
        self.assertEqual(self.role_policy.policy, self.policy)

    def test_role_policy_str(self):
        """RolePolicy __str__ should return role and policy."""
        self.assertEqual(str(self.role_policy), "Doctor - rolepolicy_test.view")

    def test_role_policy_unique_together(self):
        """Same role-policy combination should raise IntegrityError."""
        with self.assertRaises(IntegrityError):
            RolePolicy.objects.create(
                role=self.role,
                policy=self.policy,  # Duplicate
            )


class UserRoleModelTestCase(TestCase):
    """Tests for the UserRole model."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            clinic=self.clinic,
        )
        self.role = Role.objects.create(
            name="Doctor",
            slug="doctor",
            clinic=self.clinic,
        )
        self.assigner = CustomUser.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass123",
            clinic=self.clinic,
        )
        self.user_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            assigned_by=self.assigner,
        )

    def test_user_role_creation(self):
        """UserRole should be created correctly."""
        self.assertEqual(self.user_role.user, self.user)
        self.assertEqual(self.user_role.role, self.role)
        self.assertEqual(self.user_role.assigned_by, self.assigner)

    def test_user_role_str(self):
        """UserRole __str__ should return user email and role."""
        self.assertEqual(str(self.user_role), "test@example.com - Doctor")

    def test_user_role_unique_together(self):
        """Same user-role combination should raise IntegrityError."""
        with self.assertRaises(IntegrityError):
            UserRole.objects.create(
                user=self.user,
                role=self.role,  # Duplicate
            )

    def test_user_role_assigned_by_null(self):
        """assigned_by can be null."""
        role2 = Role.objects.create(
            name="Nurse",
            slug="nurse",
            clinic=self.clinic,
        )
        user_role = UserRole.objects.create(
            user=self.user,
            role=role2,
            assigned_by=None,
        )
        self.assertIsNone(user_role.assigned_by)

    def test_user_multiple_roles(self):
        """User can have multiple roles."""
        role2 = Role.objects.create(
            name="Administrator",
            slug="admin",
            clinic=self.clinic,
        )
        UserRole.objects.create(user=self.user, role=role2)

        roles = self.user.get_roles()
        self.assertEqual(roles.count(), 2)


class CustomUserSerializerTestCase(TestCase):
    """Tests for the CustomUserSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            clinic=self.clinic,
            role=CustomUser.Role.DOCTOR,
            is_owner=True,
        )

    def test_serializer_contains_expected_fields(self):
        """Serializer should contain all expected fields."""
        serializer = CustomUserSerializer(self.user)
        data = serializer.data

        expected_fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar_url",
            "get_display_name",
            "clinic",
            "role",
            "is_owner",
            "roles",
            "permissions",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_data_values(self):
        """Serializer should return correct values."""
        serializer = CustomUserSerializer(self.user)
        data = serializer.data

        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["first_name"], "John")
        self.assertEqual(data["last_name"], "Doe")
        self.assertEqual(data["role"], "Doctor")
        self.assertTrue(data["is_owner"])
        self.assertEqual(data["get_display_name"], "John Doe")

    def test_serializer_roles_field(self):
        """roles field should return assigned roles."""
        role = Role.objects.create(
            name="Doctor",
            slug="doctor",
            clinic=self.clinic,
        )
        UserRole.objects.create(user=self.user, role=role)

        serializer = CustomUserSerializer(self.user)
        roles = serializer.data["roles"]

        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0]["name"], "Doctor")
        self.assertEqual(roles[0]["slug"], "doctor")

    def test_serializer_permissions_field(self):
        """permissions field should return permission codes."""
        role = Role.objects.create(
            name="Admin",
            slug="admin",
            clinic=self.clinic,
            is_admin=True,
        )
        UserRole.objects.create(user=self.user, role=role)

        serializer = CustomUserSerializer(self.user)
        permissions = serializer.data["permissions"]

        self.assertIn("*", permissions)


class RegisterSerializerTestCase(TestCase):
    """Tests for the RegisterSerializer."""

    def test_valid_registration_data(self):
        """Serializer should validate correct registration data."""
        data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
            "clinic_name": "New Clinic",
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_password_mismatch(self):
        """Serializer should reject mismatched passwords."""
        data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "password_confirm": "DifferentPass!",
            "clinic_name": "New Clinic",
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password_confirm", serializer.errors)

    def test_duplicate_email(self):
        """Serializer should reject duplicate email."""
        CustomUser.objects.create_user(
            username="existing",
            email="existing@example.com",
            password="testpass123",
        )
        data = {
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
            "clinic_name": "New Clinic",
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_email_normalized_to_lowercase(self):
        """Email should be normalized to lowercase."""
        data = {
            "email": "NewUser@Example.COM",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
            "clinic_name": "New Clinic",
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["email"], "newuser@example.com")

    def test_create_user_and_clinic(self):
        """create should create user and clinic."""
        data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
            "clinic_name": "New Clinic",
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(user.is_owner)
        self.assertEqual(user.role, CustomUser.Role.DOCTOR)
        self.assertIsNotNone(user.clinic)
        self.assertEqual(user.clinic.name, "New Clinic")

    def test_weak_password_rejected(self):
        """Serializer should reject weak passwords."""
        data = {
            "email": "newuser@example.com",
            "password": "123",  # Too short/weak
            "password_confirm": "123",
            "clinic_name": "New Clinic",
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)


class LoginSerializerTestCase(TestCase):
    """Tests for the LoginSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = CustomUser.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
            is_active=True,
        )

    def test_valid_login(self):
        """Serializer should validate correct credentials."""
        data = {
            "email": "testuser@example.com",
            "password": "testpass123",
        }
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["user"], self.user)

    def test_invalid_password(self):
        """Serializer should reject invalid password."""
        data = {
            "email": "testuser@example.com",
            "password": "wrongpassword",
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_nonexistent_email(self):
        """Serializer should reject non-existent email."""
        data = {
            "email": "nonexistent@example.com",
            "password": "testpass123",
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_inactive_user(self):
        """Serializer should reject inactive user."""
        self.user.is_active = False
        self.user.save()

        data = {
            "email": "testuser@example.com",
            "password": "testpass123",
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_email_case_insensitive(self):
        """Login should be case-insensitive for email."""
        data = {
            "email": "TestUser@Example.COM",
            "password": "testpass123",
        }
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class StaffSerializerTestCase(TestCase):
    """Tests for staff-related serializers."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.owner = CustomUser.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="testpass123",
            clinic=self.clinic,
            is_owner=True,
        )
        self.staff = CustomUser.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="testpass123",
            first_name="Jane",
            last_name="Smith",
            clinic=self.clinic,
            role=CustomUser.Role.NURSE,
        )

    def get_mock_request(self, user=None):
        """Create a mock request with user context."""
        request = self.factory.get("/")
        request.user = user or self.owner
        drf_request = Request(request)
        drf_request.user = user or self.owner
        return drf_request

    def test_staff_list_serializer_fields(self):
        """StaffListSerializer should contain expected fields."""
        serializer = StaffListSerializer(self.staff)
        data = serializer.data

        expected_fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_owner",
            "is_active",
            "date_joined",
            "roles",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_staff_create_serializer_valid(self):
        """StaffCreateSerializer should validate correct data."""
        data = {
            "email": "newstaff@example.com",
            "password": "newpass123",
            "first_name": "New",
            "last_name": "Staff",
        }
        serializer = StaffCreateSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_staff_create_serializer_creates_user(self):
        """StaffCreateSerializer should create staff user."""
        data = {
            "email": "newstaff@example.com",
            "password": "newpass123",
            "first_name": "New",
            "last_name": "Staff",
        }
        serializer = StaffCreateSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, "newstaff@example.com")
        self.assertEqual(user.clinic, self.clinic)
        self.assertEqual(user.role, CustomUser.Role.SECRETARY)
        self.assertFalse(user.is_owner)

    def test_staff_create_duplicate_email(self):
        """StaffCreateSerializer should reject duplicate email in clinic."""
        data = {
            "email": "staff@example.com",  # Already exists
            "password": "newpass123",
        }
        serializer = StaffCreateSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_staff_update_serializer(self):
        """StaffUpdateSerializer should update staff fields."""
        data = {
            "email": "updated@example.com",
            "first_name": "Updated",
            "last_name": "Name",
            "is_active": False,
        }
        serializer = StaffUpdateSerializer(self.staff, data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.email, "updated@example.com")
        self.assertEqual(updated.first_name, "Updated")
        self.assertFalse(updated.is_active)

    def test_staff_update_with_password(self):
        """StaffUpdateSerializer should reset password when provided."""
        data = {
            "email": "staff@example.com",
            "password": "newpassword123",
        }
        serializer = StaffUpdateSerializer(
            self.staff,
            data=data,
            partial=True,
            context={"request": self.get_mock_request()},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        # Verify password was changed
        self.assertTrue(updated.check_password("newpassword123"))


class PolicySerializerTestCase(TestCase):
    """Tests for the PolicySerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.policy, _ = Policy.objects.get_or_create(
            code="policy_serializer_test.view",
            defaults={"name": "View Test", "category": "PolicySerializerTest"},
        )

    def test_serializer_fields(self):
        """PolicySerializer should contain expected fields."""
        serializer = PolicySerializer(self.policy)
        data = serializer.data

        self.assertEqual(data["id"], self.policy.id)
        self.assertEqual(data["code"], "policy_serializer_test.view")
        self.assertEqual(data["name"], "View Test")
        self.assertEqual(data["category"], "PolicySerializerTest")


class RoleSerializerTestCase(TestCase):
    """Tests for role serializers."""

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
        self.role = Role.objects.create(
            name="Doctor",
            slug="doctor",
            description="Medical staff",
            clinic=self.clinic,
            color="#3b82f6",
            icon="Stethoscope",
        )
        self.policy, _ = Policy.objects.get_or_create(
            code="role_serializer_test.view",
            defaults={"name": "View Test", "category": "RoleSerializerTest"},
        )
        RolePolicy.objects.create(role=self.role, policy=self.policy)

    def get_mock_request(self):
        """Create a mock request with user context."""
        request = self.factory.get("/")
        request.user = self.user
        drf_request = Request(request)
        drf_request.user = self.user
        return drf_request

    def test_role_serializer_fields(self):
        """RoleSerializer should contain expected fields."""
        serializer = RoleSerializer(self.role)
        data = serializer.data

        expected_fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_system",
            "is_admin",
            "policies",
            "color",
            "icon",
            "user_count",
            "created_at",
            "updated_at",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_role_serializer_user_count(self):
        """RoleSerializer should include user count."""
        UserRole.objects.create(user=self.user, role=self.role)

        serializer = RoleSerializer(self.role)
        self.assertEqual(serializer.data["user_count"], 1)

    def test_role_serializer_policies(self):
        """RoleSerializer should include policies."""
        serializer = RoleSerializer(self.role)
        policies = serializer.data["policies"]

        self.assertEqual(len(policies), 1)
        self.assertEqual(policies[0]["code"], "role_serializer_test.view")

    def test_role_create_serializer_valid(self):
        """RoleCreateUpdateSerializer should validate correct data."""
        data = {
            "name": "New Role",
            "slug": "new-role",
            "description": "A new role",
            "color": "#ff0000",
            "icon": "Star",
        }
        serializer = RoleCreateUpdateSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_role_create_serializer_creates_role(self):
        """RoleCreateUpdateSerializer should create role with clinic."""
        data = {
            "name": "New Role",
            "slug": "new-role",
        }
        serializer = RoleCreateUpdateSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        role = serializer.save()

        self.assertEqual(role.name, "New Role")
        self.assertEqual(role.clinic, self.clinic)

    def test_role_create_with_policies(self):
        """RoleCreateUpdateSerializer should create role with policies."""
        data = {
            "name": "New Role",
            "slug": "new-role",
            "policy_ids": [self.policy.id],
        }
        serializer = RoleCreateUpdateSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        role = serializer.save()

        self.assertEqual(role.get_policies().count(), 1)
        self.assertIn(self.policy, role.get_policies())

    def test_role_create_duplicate_slug(self):
        """RoleCreateUpdateSerializer should reject duplicate slug."""
        data = {
            "name": "Another Doctor",
            "slug": "doctor",  # Already exists
        }
        serializer = RoleCreateUpdateSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("slug", serializer.errors)

    def test_role_update_serializer(self):
        """RoleCreateUpdateSerializer should update role."""
        data = {
            "name": "Updated Doctor",
            "slug": "doctor",
            "description": "Updated description",
        }
        serializer = RoleCreateUpdateSerializer(self.role, data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.name, "Updated Doctor")
        self.assertEqual(updated.description, "Updated description")


class UserRoleSerializerTestCase(TestCase):
    """Tests for the UserRoleSerializer."""

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
        self.role = Role.objects.create(
            name="Doctor",
            slug="doctor",
            clinic=self.clinic,
        )

    def get_mock_request(self):
        """Create a mock request with user context."""
        request = self.factory.get("/")
        request.user = self.user
        drf_request = Request(request)
        drf_request.user = self.user
        return drf_request

    def test_user_role_serializer_create(self):
        """UserRoleSerializer should create user role assignment."""
        data = {"role_id": self.role.id}
        serializer = UserRoleSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user_role = serializer.save(user=self.user)

        self.assertEqual(user_role.user, self.user)
        self.assertEqual(user_role.role, self.role)
        self.assertEqual(user_role.assigned_by, self.user)

    def test_user_role_serializer_validates_clinic(self):
        """UserRoleSerializer should reject role from different clinic."""
        other_clinic = Clinic.objects.create(name="Other Clinic")
        other_role = Role.objects.create(
            name="Doctor",
            slug="doctor",
            clinic=other_clinic,
        )

        data = {"role_id": other_role.id}
        serializer = UserRoleSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("role_id", serializer.errors)


class UserWithRolesSerializerTestCase(TestCase):
    """Tests for the UserWithRolesSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            clinic=self.clinic,
            is_owner=True,
        )
        self.role = Role.objects.create(
            name="Doctor",
            slug="doctor",
            clinic=self.clinic,
            is_admin=True,
        )
        UserRole.objects.create(user=self.user, role=self.role)

    def test_serializer_fields(self):
        """UserWithRolesSerializer should contain expected fields."""
        serializer = UserWithRolesSerializer(self.user)
        data = serializer.data

        expected_fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_owner",
            "is_active",
            "roles",
            "permissions",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_roles_expanded(self):
        """roles field should contain full role objects."""
        serializer = UserWithRolesSerializer(self.user)
        roles = serializer.data["roles"]

        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0]["name"], "Doctor")
        self.assertEqual(roles[0]["slug"], "doctor")
        self.assertTrue(roles[0]["is_admin"])

    def test_serializer_permissions(self):
        """permissions field should contain permission codes."""
        serializer = UserWithRolesSerializer(self.user)
        permissions = serializer.data["permissions"]

        self.assertIn("*", permissions)


class UpdateProfileSerializerTestCase(TestCase):
    """Tests for the UpdateProfileSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
        )

    def test_serializer_fields(self):
        """UpdateProfileSerializer should have correct fields."""
        serializer = UpdateProfileSerializer()
        fields = serializer.fields.keys()

        self.assertIn("first_name", fields)
        self.assertIn("last_name", fields)
        self.assertIn("avatar", fields)
        self.assertIn("language", fields)
        self.assertIn("timezone", fields)

    def test_update_profile(self):
        """UpdateProfileSerializer should update profile fields."""
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "timezone": "Asia/Manila",
        }
        serializer = UpdateProfileSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.first_name, "Jane")
        self.assertEqual(updated.last_name, "Smith")
        self.assertEqual(updated.timezone, "Asia/Manila")
