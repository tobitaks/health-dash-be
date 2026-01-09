import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError

from apps.patients.models import Patient
from apps.users.models import CustomUser


class Command(BaseCommand):
    help = "Populates the database with sample patients for a specific clinic."

    # Sample data for generating patients
    FIRST_NAMES_MALE = [
        "Juan",
        "Jose",
        "Miguel",
        "Carlos",
        "Antonio",
        "Rafael",
        "Marco",
        "Gabriel",
        "Daniel",
        "David",
        "Luis",
        "Fernando",
        "Ricardo",
        "Eduardo",
        "Roberto",
        "Alejandro",
        "Francisco",
        "Manuel",
        "Pedro",
        "Ramon",
    ]

    FIRST_NAMES_FEMALE = [
        "Maria",
        "Ana",
        "Sofia",
        "Isabella",
        "Camila",
        "Valentina",
        "Lucia",
        "Elena",
        "Carmen",
        "Rosa",
        "Patricia",
        "Gloria",
        "Teresa",
        "Cristina",
        "Angela",
        "Beatriz",
        "Laura",
        "Diana",
        "Sandra",
        "Monica",
    ]

    MIDDLE_NAMES = [
        "Santos",
        "Cruz",
        "Reyes",
        "Garcia",
        "Martinez",
        "Lopez",
        "Dela Cruz",
        "Ramos",
        "Bautista",
        "Villanueva",
        "Gonzales",
        "Mendoza",
        "Aquino",
        "",
    ]

    LAST_NAMES = [
        "Santos",
        "Reyes",
        "Cruz",
        "Garcia",
        "Mendoza",
        "Lopez",
        "Gonzales",
        "Villanueva",
        "Ramos",
        "Bautista",
        "Aquino",
        "Fernandez",
        "Torres",
        "Rivera",
        "Flores",
        "Castillo",
        "Morales",
        "Navarro",
        "Pascual",
        "Mercado",
    ]

    CITIES = [
        "Manila",
        "Quezon City",
        "Makati",
        "Pasig",
        "Taguig",
        "Cebu City",
        "Davao City",
        "Caloocan",
        "Las Pinas",
        "Paranaque",
        "Muntinlupa",
    ]

    PROVINCES = [
        "Metro Manila",
        "Cebu",
        "Davao del Sur",
        "Laguna",
        "Cavite",
        "Bulacan",
        "Rizal",
        "Pampanga",
        "Batangas",
        "Pangasinan",
    ]

    STREETS = [
        "123 Rizal St.",
        "456 Mabini Ave.",
        "789 Bonifacio Blvd.",
        "321 Luna St.",
        "654 Del Pilar Rd.",
        "987 Aguinaldo Highway",
        "147 Quezon Ave.",
        "258 Osmeña St.",
        "369 Roxas Blvd.",
        "741 EDSA",
    ]

    ALLERGIES = [
        ["Penicillin"],
        ["Sulfa drugs"],
        ["Aspirin"],
        ["Ibuprofen"],
        ["Shellfish"],
        ["Peanuts"],
        ["Latex"],
        ["Bee stings"],
        ["Penicillin", "Sulfa drugs"],
        ["Aspirin", "Ibuprofen"],
        [],
        [],
        [],
        [],  # Empty for variety
    ]

    MEDICAL_CONDITIONS = [
        ["Hypertension"],
        ["Diabetes Type 2"],
        ["Asthma"],
        ["Arthritis"],
        ["Hypertension", "Diabetes Type 2"],
        ["Asthma", "Allergic Rhinitis"],
        ["Hypothyroidism"],
        ["GERD"],
        ["Migraine"],
        ["Anxiety"],
        [],
        [],
        [],
        [],  # Empty for variety
    ]

    MEDICATIONS = [
        "Metformin 500mg daily",
        "Amlodipine 5mg daily",
        "Losartan 50mg daily",
        "Omeprazole 20mg daily",
        "Salbutamol inhaler as needed",
        "Levothyroxine 50mcg daily",
        "Metformin 500mg, Amlodipine 5mg daily",
        "",  # No medications
    ]

    RELATIONSHIP_CHOICES = ["Spouse", "Parent", "Sibling", "Child", "Friend"]

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Email of the clinic owner",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=20,
            help="Number of patients to create (default: 20)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing patients before populating",
        )

    def handle(self, *args, **options):
        email = options["email"]
        count = options["count"]
        clear = options["clear"]

        # Find the user by email
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise CommandError(f"No user found with email: {email}") from None

        # Get the clinic
        clinic = user.clinic
        if not clinic:
            raise CommandError(f"User {email} is not associated with any clinic.") from None

        self.stdout.write(f"Found clinic: {clinic.name}")

        # Clear existing patients if requested
        if clear:
            deleted_count = Patient.objects.filter(clinic=clinic).delete()[0]
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing patients."))

        # Get the next patient number
        existing_patients = Patient.objects.filter(clinic=clinic).count()
        current_year = date.today().year

        created_count = 0
        for i in range(count):
            patient_number = existing_patients + i + 1
            patient_id = f"PT-{current_year}-{patient_number:04d}"

            # Check if patient_id already exists
            if Patient.objects.filter(clinic=clinic, patient_id=patient_id).exists():
                self.stdout.write(self.style.WARNING(f"Patient {patient_id} already exists, skipping."))
                continue

            patient = self._create_patient(clinic, patient_id)
            created_count += 1

            if created_count % 5 == 0:
                self.stdout.write(f"Created {created_count} patients...")

        self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} patients for {clinic.name}"))

    def _create_patient(self, clinic, patient_id):
        """Create a single patient with random data."""
        gender = random.choice(["Male", "Female"])

        if gender == "Male":
            first_name = random.choice(self.FIRST_NAMES_MALE)
        else:
            first_name = random.choice(self.FIRST_NAMES_FEMALE)

        middle_name = random.choice(self.MIDDLE_NAMES)
        last_name = random.choice(self.LAST_NAMES)

        # Generate random date of birth (ages 1-90)
        days_ago = random.randint(365, 365 * 90)
        date_of_birth = date.today() - timedelta(days=days_ago)

        # Generate phone number
        phone = f"09{random.randint(10, 99)}{random.randint(1000000, 9999999)}"

        # Generate email (some patients might not have email)
        email = ""
        if random.random() > 0.3:  # 70% chance of having email
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@email.com"

        # Generate address
        city = random.choice(self.CITIES)
        province = random.choice(self.PROVINCES)
        street = random.choice(self.STREETS)
        zip_code = f"{random.randint(1000, 9999)}"

        # Emergency contact (80% chance)
        emergency_name = ""
        emergency_phone = ""
        emergency_relationship = ""
        if random.random() > 0.2:
            emergency_gender = random.choice(["Male", "Female"])
            if emergency_gender == "Male":
                emergency_first = random.choice(self.FIRST_NAMES_MALE)
            else:
                emergency_first = random.choice(self.FIRST_NAMES_FEMALE)
            emergency_name = f"{emergency_first} {last_name}"
            emergency_phone = f"09{random.randint(10, 99)}{random.randint(1000000, 9999999)}"
            emergency_relationship = random.choice(self.RELATIONSHIP_CHOICES)

        # Medical info
        blood_type = random.choice(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown", ""])
        allergies = random.choice(self.ALLERGIES)
        medical_conditions = random.choice(self.MEDICAL_CONDITIONS)
        medications = random.choice(self.MEDICATIONS)

        # Civil status based on age
        age = (date.today() - date_of_birth).days // 365
        if age < 18:
            civil_status = "Single"
        else:
            civil_status = random.choice(["Single", "Married", "Married", "Widowed", "Separated"])

        return Patient.objects.create(
            clinic=clinic,
            patient_id=patient_id,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender,
            civil_status=civil_status,
            phone=phone,
            email=email,
            address_street=street,
            address_city=city,
            address_province=province,
            address_zip=zip_code,
            emergency_contact_name=emergency_name,
            emergency_contact_phone=emergency_phone,
            emergency_contact_relationship=emergency_relationship,
            blood_type=blood_type,
            allergies=allergies,
            medical_conditions=medical_conditions,
            current_medications=medications,
            status="active",
        )
