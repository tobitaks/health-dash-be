import random
from datetime import date, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from apps.consultations.models import Consultation
from apps.patients.models import Patient
from apps.users.models import CustomUser


class Command(BaseCommand):
    help = "Populates the database with sample consultations for testing SOAP generation."

    # Realistic chief complaints with associated vital sign profiles
    CHIEF_COMPLAINTS = [
        {
            "complaint": "Patient complains of persistent cough and cold symptoms for 3 days. "
            "Reports runny nose, mild sore throat, and occasional sneezing. "
            "Denies fever but feels generally unwell.",
            "vitals": {"temp_range": (36.5, 37.5), "hr_range": (70, 85), "rr_range": (16, 20)},
        },
        {
            "complaint": "Presenting with high-grade fever for 2 days, body malaise, and headache. "
            "Temperature reached 39°C at home last night. Associated with chills and muscle aches.",
            "vitals": {"temp_range": (38.0, 39.5), "hr_range": (90, 110), "rr_range": (18, 24)},
        },
        {
            "complaint": "Chief complaint of epigastric pain and bloating after meals for 1 week. "
            "Describes burning sensation in upper abdomen. Occasional nausea but no vomiting. "
            "Symptoms worsen after eating spicy or fatty foods.",
            "vitals": {"temp_range": (36.5, 37.2), "hr_range": (72, 88), "rr_range": (16, 20)},
        },
        {
            "complaint": "Patient reports dizziness and lightheadedness for the past 3 days. "
            "Symptoms worse when standing up quickly. Denies chest pain or palpitations. "
            "Has been feeling more tired than usual.",
            "vitals": {"temp_range": (36.4, 37.0), "hr_range": (65, 80), "rr_range": (14, 18)},
        },
        {
            "complaint": "Presenting with difficulty breathing and wheezing since this morning. "
            "Has history of asthma, last attack was 6 months ago. Used rescue inhaler with partial relief. "
            "Denies fever or productive cough.",
            "vitals": {"temp_range": (36.5, 37.3), "hr_range": (95, 115), "rr_range": (22, 28), "spo2_range": (92, 96)},
        },
        {
            "complaint": "Patient complains of severe headache rated 8/10, located at the frontal area. "
            "Started yesterday afternoon. Associated with sensitivity to light. "
            "Reports similar episodes in the past. Denies nausea or visual changes.",
            "vitals": {"temp_range": (36.5, 37.2), "hr_range": (75, 95), "rr_range": (16, 20)},
        },
        {
            "complaint": "Chief complaint of lower back pain for 5 days after lifting heavy objects. "
            "Pain radiates to right buttock. Rates pain as 6/10. Difficulty bending forward. "
            "No numbness or weakness in legs.",
            "vitals": {"temp_range": (36.5, 37.0), "hr_range": (70, 85), "rr_range": (16, 18)},
        },
        {
            "complaint": "Patient presents with skin rashes on both arms for 2 days. "
            "Describes itchy, red, raised lesions. Started after trying new laundry detergent. "
            "No fever or difficulty breathing.",
            "vitals": {"temp_range": (36.5, 37.2), "hr_range": (70, 82), "rr_range": (16, 18)},
        },
        {
            "complaint": "Complaining of frequent urination and burning sensation when urinating for 3 days. "
            "Urine appears cloudy. Mild lower abdominal discomfort. No fever or back pain.",
            "vitals": {"temp_range": (36.8, 37.8), "hr_range": (75, 90), "rr_range": (16, 20)},
        },
        {
            "complaint": "Patient reports loose bowel movements for 2 days, approximately 5-6 episodes daily. "
            "Watery stools without blood or mucus. Mild abdominal cramping. "
            "Able to tolerate oral fluids. No fever.",
            "vitals": {"temp_range": (36.5, 37.5), "hr_range": (80, 95), "rr_range": (16, 20)},
        },
        {
            "complaint": "Presenting for follow-up of hypertension. Currently on Amlodipine 5mg daily. "
            "Reports occasional headaches in the morning. Home BP readings average 140/90. "
            "Compliant with medications.",
            "vitals": {"temp_range": (36.5, 37.0), "hr_range": (70, 85), "rr_range": (16, 18), "bp_high": True},
        },
        {
            "complaint": "Chief complaint of sore throat and difficulty swallowing for 4 days. "
            "Reports low-grade fever at home. Swollen lymph nodes noted in neck. "
            "No cough or runny nose.",
            "vitals": {"temp_range": (37.5, 38.5), "hr_range": (85, 100), "rr_range": (16, 20)},
        },
        {
            "complaint": "Patient complains of chest tightness and occasional palpitations for 1 week. "
            "Symptoms occur during stressful situations at work. Denies chest pain at rest. "
            "No shortness of breath or dizziness. Reports poor sleep lately.",
            "vitals": {"temp_range": (36.5, 37.0), "hr_range": (85, 105), "rr_range": (18, 22)},
        },
        {
            "complaint": "Presenting with joint pain in both knees for 2 weeks. "
            "Pain is worse in the morning and improves with movement. Mild swelling noted. "
            "Has history of osteoarthritis. Currently taking Paracetamol as needed.",
            "vitals": {"temp_range": (36.5, 37.0), "hr_range": (68, 80), "rr_range": (16, 18)},
        },
        {
            "complaint": "Patient reports excessive fatigue and weakness for the past 2 weeks. "
            "Sleeping 10-12 hours but still feels tired. Decreased appetite. "
            "No fever, weight loss, or night sweats.",
            "vitals": {"temp_range": (36.3, 36.8), "hr_range": (60, 75), "rr_range": (14, 18)},
        },
        {
            "complaint": "Chief complaint of ear pain in the right ear for 3 days. "
            "Reports decreased hearing on affected side. Had recent upper respiratory infection. "
            "Mild drainage noted. No fever.",
            "vitals": {"temp_range": (36.8, 37.8), "hr_range": (75, 88), "rr_range": (16, 18)},
        },
        {
            "complaint": "Patient presents with eye redness and discharge in left eye for 2 days. "
            "Reports itching and tearing. Woke up with crusted eyelids this morning. "
            "No vision changes or pain.",
            "vitals": {"temp_range": (36.5, 37.2), "hr_range": (70, 82), "rr_range": (16, 18)},
        },
        {
            "complaint": "Complaining of nausea and vomiting since last night. "
            "Approximately 4 episodes of vomiting. Unable to keep food down. "
            "Ate at a restaurant yesterday. Mild abdominal discomfort. Low-grade fever.",
            "vitals": {"temp_range": (37.2, 38.2), "hr_range": (85, 100), "rr_range": (18, 22)},
        },
        {
            "complaint": "Patient reports numbness and tingling in both hands for 1 month. "
            "Symptoms worse at night and upon waking. Works at computer all day. "
            "Occasional dropping of objects. No neck pain.",
            "vitals": {"temp_range": (36.5, 37.0), "hr_range": (68, 80), "rr_range": (16, 18)},
        },
        {
            "complaint": "Presenting for diabetes follow-up. Currently on Metformin 500mg twice daily. "
            "Home glucose readings range from 120-180 mg/dL fasting. "
            "Reports occasional blurry vision. No numbness in feet.",
            "vitals": {"temp_range": (36.5, 37.0), "hr_range": (72, 85), "rr_range": (16, 18)},
        },
    ]

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
            default=10,
            help="Number of consultations to create (default: 10)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing consultations before populating",
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

        # Get patients for this clinic
        patients = list(Patient.objects.filter(clinic=clinic, status="active"))
        if not patients:
            raise CommandError(
                f"No active patients found for clinic {clinic.name}. Please run populate_patients first."
            ) from None

        self.stdout.write(f"Found {len(patients)} active patients")

        # Clear existing consultations if requested
        if clear:
            deleted_count = Consultation.objects.filter(clinic=clinic).delete()[0]
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing consultations."))

        # Get the next consultation number
        existing_count = Consultation.objects.filter(clinic=clinic).count()
        current_year = date.today().year

        created_count = 0
        for i in range(count):
            consultation_number = existing_count + i + 1
            consultation_id = f"CONS-{current_year}-{consultation_number:04d}"

            # Check if consultation_id already exists
            if Consultation.objects.filter(clinic=clinic, consultation_id=consultation_id).exists():
                self.stdout.write(self.style.WARNING(f"Consultation {consultation_id} already exists, skipping."))
                continue

            self._create_consultation(
                clinic=clinic,
                consultation_id=consultation_id,
                patient=random.choice(patients),
                created_by=user,
            )
            created_count += 1

            if created_count % 5 == 0:
                self.stdout.write(f"Created {created_count} consultations...")

        self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} consultations for {clinic.name}"))

    def _create_consultation(self, clinic, consultation_id, patient, created_by):
        """Create a single consultation with random chief complaint and vital signs."""
        # Pick a random chief complaint profile
        complaint_profile = random.choice(self.CHIEF_COMPLAINTS)

        # Generate consultation date (within last 30 days)
        days_ago = random.randint(0, 30)
        consultation_date = date.today() - timedelta(days=days_ago)

        # Generate consultation time (8 AM to 5 PM)
        hour = random.randint(8, 17)
        minute = random.choice([0, 15, 30, 45])
        consultation_time = time(hour, minute)

        # Generate vital signs based on profile
        vitals = complaint_profile["vitals"]

        # Temperature
        temp_low, temp_high = vitals.get("temp_range", (36.5, 37.0))
        temperature = Decimal(str(round(random.uniform(temp_low, temp_high), 1)))

        # Heart rate
        hr_low, hr_high = vitals.get("hr_range", (70, 85))
        heart_rate = random.randint(hr_low, hr_high)

        # Respiratory rate
        rr_low, rr_high = vitals.get("rr_range", (16, 20))
        respiratory_rate = random.randint(rr_low, rr_high)

        # Blood pressure
        if vitals.get("bp_high"):
            bp_systolic = random.randint(135, 160)
            bp_diastolic = random.randint(85, 100)
        else:
            bp_systolic = random.randint(110, 130)
            bp_diastolic = random.randint(70, 85)

        # Oxygen saturation
        spo2_low, spo2_high = vitals.get("spo2_range", (96, 100))
        oxygen_saturation = random.randint(spo2_low, spo2_high)

        # Weight and height based on patient (randomize a bit for variety)
        weight = Decimal(str(round(random.uniform(50.0, 90.0), 1)))
        height = Decimal(str(round(random.uniform(155.0, 180.0), 1)))

        return Consultation.objects.create(
            clinic=clinic,
            patient=patient,
            created_by=created_by,
            consultation_id=consultation_id,
            consultation_date=consultation_date,
            consultation_time=consultation_time,
            status="draft",
            chief_complaint=complaint_profile["complaint"],
            bp_systolic=bp_systolic,
            bp_diastolic=bp_diastolic,
            temperature=temperature,
            temperature_unit="C",
            heart_rate=heart_rate,
            respiratory_rate=respiratory_rate,
            oxygen_saturation=oxygen_saturation,
            weight=weight,
            weight_unit="kg",
            height=height,
            height_unit="cm",
        )
