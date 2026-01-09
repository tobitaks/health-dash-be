"""
Management command to populate common lab tests for a clinic.
"""

from django.core.management.base import BaseCommand

from apps.lab_orders.models import LabTest
from apps.users.models import CustomUser

# Common lab tests
COMMON_LAB_TESTS = [
    # Hematology
    {
        "name": "Complete Blood Count (CBC)",
        "code": "CBC",
        "category": "hematology",
        "sample_type": "blood",
        "description": "Measures various components of blood including RBC, WBC, hemoglobin, hematocrit, and platelets",
        "turnaround_time": "1-2 hours",
        "special_instructions": "",
    },
    {
        "name": "Hemoglobin",
        "code": "HGB",
        "category": "hematology",
        "sample_type": "blood",
        "description": "Measures the oxygen-carrying protein in red blood cells",
        "turnaround_time": "1 hour",
        "special_instructions": "",
    },
    {
        "name": "Hematocrit",
        "code": "HCT",
        "category": "hematology",
        "sample_type": "blood",
        "description": "Measures the percentage of blood volume occupied by red blood cells",
        "turnaround_time": "1 hour",
        "special_instructions": "",
    },
    {
        "name": "Platelet Count",
        "code": "PLT",
        "category": "hematology",
        "sample_type": "blood",
        "description": "Measures the number of platelets in blood",
        "turnaround_time": "1-2 hours",
        "special_instructions": "",
    },
    {
        "name": "Erythrocyte Sedimentation Rate (ESR)",
        "code": "ESR",
        "category": "hematology",
        "sample_type": "blood",
        "description": "Non-specific test for inflammation",
        "turnaround_time": "1 hour",
        "special_instructions": "",
    },
    {
        "name": "Prothrombin Time (PT)",
        "code": "PT",
        "category": "hematology",
        "sample_type": "blood",
        "description": "Measures how long it takes blood to clot",
        "turnaround_time": "2-4 hours",
        "special_instructions": "Patient should inform if on blood thinners",
    },
    {
        "name": "Partial Thromboplastin Time (PTT)",
        "code": "PTT",
        "category": "hematology",
        "sample_type": "blood",
        "description": "Measures clotting function",
        "turnaround_time": "2-4 hours",
        "special_instructions": "",
    },
    {
        "name": "Blood Type & Rh Factor",
        "code": "BT-RH",
        "category": "hematology",
        "sample_type": "blood",
        "description": "Determines blood group (A, B, AB, O) and Rh factor",
        "turnaround_time": "1-2 hours",
        "special_instructions": "",
    },
    {
        "name": "Peripheral Blood Smear",
        "code": "PBS",
        "category": "hematology",
        "sample_type": "blood",
        "description": "Microscopic examination of blood cells",
        "turnaround_time": "2-4 hours",
        "special_instructions": "",
    },
    # Chemistry
    {
        "name": "Fasting Blood Sugar (FBS)",
        "code": "FBS",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures blood glucose after fasting",
        "turnaround_time": "1-2 hours",
        "special_instructions": "Patient must fast for 8-12 hours before test",
    },
    {
        "name": "Random Blood Sugar (RBS)",
        "code": "RBS",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures blood glucose at any time",
        "turnaround_time": "1-2 hours",
        "special_instructions": "",
    },
    {
        "name": "HbA1c (Glycated Hemoglobin)",
        "code": "HBA1C",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures average blood sugar over past 2-3 months",
        "turnaround_time": "24 hours",
        "special_instructions": "No fasting required",
    },
    {
        "name": "Lipid Profile",
        "code": "LIPID",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures total cholesterol, HDL, LDL, and triglycerides",
        "turnaround_time": "2-4 hours",
        "special_instructions": "Patient must fast for 9-12 hours before test",
    },
    {
        "name": "Total Cholesterol",
        "code": "CHOL",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures total cholesterol in blood",
        "turnaround_time": "2-4 hours",
        "special_instructions": "Fasting recommended",
    },
    {
        "name": "Triglycerides",
        "code": "TG",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures fat in blood",
        "turnaround_time": "2-4 hours",
        "special_instructions": "Patient must fast for 9-12 hours before test",
    },
    {
        "name": "Blood Urea Nitrogen (BUN)",
        "code": "BUN",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures kidney function",
        "turnaround_time": "2-4 hours",
        "special_instructions": "",
    },
    {
        "name": "Creatinine",
        "code": "CREAT",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures kidney function",
        "turnaround_time": "2-4 hours",
        "special_instructions": "",
    },
    {
        "name": "Uric Acid",
        "code": "UA",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures uric acid levels",
        "turnaround_time": "2-4 hours",
        "special_instructions": "",
    },
    {
        "name": "SGPT/ALT",
        "code": "ALT",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Liver enzyme - measures liver function",
        "turnaround_time": "2-4 hours",
        "special_instructions": "",
    },
    {
        "name": "SGOT/AST",
        "code": "AST",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Liver enzyme - measures liver function",
        "turnaround_time": "2-4 hours",
        "special_instructions": "",
    },
    {
        "name": "Liver Function Test (LFT)",
        "code": "LFT",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Complete liver panel including ALT, AST, ALP, bilirubin, albumin",
        "turnaround_time": "4-6 hours",
        "special_instructions": "Fasting may be required",
    },
    {
        "name": "Renal Function Test (RFT)",
        "code": "RFT",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Complete kidney panel including BUN, creatinine, electrolytes",
        "turnaround_time": "4-6 hours",
        "special_instructions": "",
    },
    {
        "name": "Serum Electrolytes (Na, K, Cl)",
        "code": "LYTES",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures sodium, potassium, and chloride levels",
        "turnaround_time": "2-4 hours",
        "special_instructions": "",
    },
    {
        "name": "Calcium",
        "code": "CA",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures calcium levels in blood",
        "turnaround_time": "2-4 hours",
        "special_instructions": "",
    },
    {
        "name": "Thyroid Stimulating Hormone (TSH)",
        "code": "TSH",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures thyroid function",
        "turnaround_time": "24 hours",
        "special_instructions": "",
    },
    {
        "name": "Free T4 (FT4)",
        "code": "FT4",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures thyroid hormone",
        "turnaround_time": "24 hours",
        "special_instructions": "",
    },
    {
        "name": "Free T3 (FT3)",
        "code": "FT3",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures thyroid hormone",
        "turnaround_time": "24 hours",
        "special_instructions": "",
    },
    {
        "name": "Thyroid Profile",
        "code": "THYROID",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Complete thyroid panel (TSH, FT3, FT4)",
        "turnaround_time": "24 hours",
        "special_instructions": "",
    },
    # Urinalysis
    {
        "name": "Urinalysis",
        "code": "UA",
        "category": "urinalysis",
        "sample_type": "urine",
        "description": "Complete urine examination",
        "turnaround_time": "1-2 hours",
        "special_instructions": "Clean catch midstream sample required",
    },
    {
        "name": "Urine Pregnancy Test",
        "code": "UPT",
        "category": "urinalysis",
        "sample_type": "urine",
        "description": "Detects pregnancy hormone (hCG)",
        "turnaround_time": "30 minutes",
        "special_instructions": "First morning urine preferred",
    },
    {
        "name": "Urine Drug Screen",
        "code": "UDS",
        "category": "urinalysis",
        "sample_type": "urine",
        "description": "Screens for common drugs of abuse",
        "turnaround_time": "1-2 hours",
        "special_instructions": "",
    },
    # Microbiology
    {
        "name": "Urine Culture & Sensitivity",
        "code": "UC&S",
        "category": "microbiology",
        "sample_type": "urine",
        "description": "Identifies bacteria and antibiotic sensitivity",
        "turnaround_time": "48-72 hours",
        "special_instructions": "Clean catch midstream sample required",
    },
    {
        "name": "Stool Culture & Sensitivity",
        "code": "SC&S",
        "category": "microbiology",
        "sample_type": "stool",
        "description": "Identifies bacteria in stool",
        "turnaround_time": "48-72 hours",
        "special_instructions": "Fresh stool sample required",
    },
    {
        "name": "Stool Exam (Fecalysis)",
        "code": "STOOL",
        "category": "microbiology",
        "sample_type": "stool",
        "description": "Examines stool for parasites, blood, and other abnormalities",
        "turnaround_time": "1-2 hours",
        "special_instructions": "Fresh stool sample required",
    },
    {
        "name": "Throat Swab Culture",
        "code": "THROAT",
        "category": "microbiology",
        "sample_type": "swab",
        "description": "Tests for streptococcal infection",
        "turnaround_time": "24-48 hours",
        "special_instructions": "",
    },
    {
        "name": "Wound Culture & Sensitivity",
        "code": "WC&S",
        "category": "microbiology",
        "sample_type": "swab",
        "description": "Identifies bacteria in wound",
        "turnaround_time": "48-72 hours",
        "special_instructions": "",
    },
    {
        "name": "Blood Culture & Sensitivity",
        "code": "BC&S",
        "category": "microbiology",
        "sample_type": "blood",
        "description": "Identifies bacteria in blood (for sepsis)",
        "turnaround_time": "48-72 hours",
        "special_instructions": "Should be collected before antibiotics",
    },
    # Imaging
    {
        "name": "Chest X-Ray (PA View)",
        "code": "CXR-PA",
        "category": "imaging",
        "sample_type": "none",
        "description": "Posteroanterior chest radiograph",
        "turnaround_time": "1-2 hours",
        "special_instructions": "Remove metal objects and jewelry",
    },
    {
        "name": "Chest X-Ray (PA & Lateral)",
        "code": "CXR-PAL",
        "category": "imaging",
        "sample_type": "none",
        "description": "PA and lateral chest radiographs",
        "turnaround_time": "1-2 hours",
        "special_instructions": "Remove metal objects and jewelry",
    },
    {
        "name": "Abdominal X-Ray",
        "code": "AXR",
        "category": "imaging",
        "sample_type": "none",
        "description": "Plain abdominal radiograph",
        "turnaround_time": "1-2 hours",
        "special_instructions": "Remove metal objects",
    },
    {
        "name": "Abdominal Ultrasound",
        "code": "ULTRASOUND-ABD",
        "category": "imaging",
        "sample_type": "none",
        "description": "Ultrasound of abdominal organs",
        "turnaround_time": "24 hours",
        "special_instructions": "Patient must fast for 6-8 hours before test",
    },
    {
        "name": "Pelvic Ultrasound",
        "code": "ULTRASOUND-PEL",
        "category": "imaging",
        "sample_type": "none",
        "description": "Ultrasound of pelvic organs",
        "turnaround_time": "24 hours",
        "special_instructions": "Full bladder required",
    },
    {
        "name": "Thyroid Ultrasound",
        "code": "ULTRASOUND-THY",
        "category": "imaging",
        "sample_type": "none",
        "description": "Ultrasound of thyroid gland",
        "turnaround_time": "24 hours",
        "special_instructions": "",
    },
    {
        "name": "Breast Ultrasound",
        "code": "ULTRASOUND-BRE",
        "category": "imaging",
        "sample_type": "none",
        "description": "Ultrasound of breast tissue",
        "turnaround_time": "24 hours",
        "special_instructions": "",
    },
    # Cardiology
    {
        "name": "12-Lead ECG",
        "code": "ECG",
        "category": "cardiology",
        "sample_type": "none",
        "description": "Electrocardiogram - measures heart electrical activity",
        "turnaround_time": "30 minutes",
        "special_instructions": "Patient should lie still during test",
    },
    {
        "name": "2D Echocardiogram",
        "code": "2D-ECHO",
        "category": "cardiology",
        "sample_type": "none",
        "description": "Ultrasound of the heart",
        "turnaround_time": "24-48 hours",
        "special_instructions": "",
    },
    {
        "name": "Treadmill Stress Test",
        "code": "TMT",
        "category": "cardiology",
        "sample_type": "none",
        "description": "Exercise stress test to evaluate heart function",
        "turnaround_time": "2-4 hours",
        "special_instructions": "Wear comfortable clothes and shoes. No caffeine 24 hours before.",
    },
    # Other Common Tests
    {
        "name": "Dengue NS1 Antigen",
        "code": "DENGUE-NS1",
        "category": "other",
        "sample_type": "blood",
        "description": "Early detection of dengue infection",
        "turnaround_time": "2-4 hours",
        "special_instructions": "Best performed in first 5 days of fever",
    },
    {
        "name": "Dengue IgM/IgG",
        "code": "DENGUE-IGM",
        "category": "other",
        "sample_type": "blood",
        "description": "Antibody test for dengue infection",
        "turnaround_time": "2-4 hours",
        "special_instructions": "",
    },
    {
        "name": "Rapid Antigen Test (COVID-19)",
        "code": "RAT-COVID",
        "category": "other",
        "sample_type": "swab",
        "description": "Rapid test for SARS-CoV-2",
        "turnaround_time": "30 minutes",
        "special_instructions": "Nasopharyngeal swab required",
    },
    {
        "name": "Hepatitis B Surface Antigen (HBsAg)",
        "code": "HBSAG",
        "category": "other",
        "sample_type": "blood",
        "description": "Screens for hepatitis B infection",
        "turnaround_time": "24 hours",
        "special_instructions": "",
    },
    {
        "name": "Anti-HCV",
        "code": "ANTI-HCV",
        "category": "other",
        "sample_type": "blood",
        "description": "Screens for hepatitis C infection",
        "turnaround_time": "24 hours",
        "special_instructions": "",
    },
    {
        "name": "HIV 1/2 Antibody",
        "code": "HIV",
        "category": "other",
        "sample_type": "blood",
        "description": "Screens for HIV infection",
        "turnaround_time": "24 hours",
        "special_instructions": "Counseling recommended",
    },
    {
        "name": "RPR/VDRL",
        "code": "RPR",
        "category": "other",
        "sample_type": "blood",
        "description": "Screens for syphilis",
        "turnaround_time": "24 hours",
        "special_instructions": "",
    },
    {
        "name": "Prostate Specific Antigen (PSA)",
        "code": "PSA",
        "category": "other",
        "sample_type": "blood",
        "description": "Screens for prostate conditions",
        "turnaround_time": "24 hours",
        "special_instructions": "Avoid ejaculation 48 hours before test",
    },
    {
        "name": "CA-125",
        "code": "CA125",
        "category": "other",
        "sample_type": "blood",
        "description": "Tumor marker for ovarian cancer",
        "turnaround_time": "24-48 hours",
        "special_instructions": "",
    },
    {
        "name": "Vitamin D (25-OH)",
        "code": "VITD",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures vitamin D levels",
        "turnaround_time": "24-48 hours",
        "special_instructions": "",
    },
    {
        "name": "Vitamin B12",
        "code": "B12",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures vitamin B12 levels",
        "turnaround_time": "24-48 hours",
        "special_instructions": "",
    },
    {
        "name": "Serum Iron",
        "code": "FE",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures iron levels in blood",
        "turnaround_time": "24 hours",
        "special_instructions": "Fasting recommended",
    },
    {
        "name": "Ferritin",
        "code": "FERR",
        "category": "chemistry",
        "sample_type": "blood",
        "description": "Measures iron stores",
        "turnaround_time": "24 hours",
        "special_instructions": "",
    },
]


class Command(BaseCommand):
    help = "Populate common lab tests for a clinic"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Email of the clinic owner",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing lab tests before populating",
        )

    def handle(self, *args, **options):
        email = options["email"]
        clear = options["clear"]

        # Get the user and their clinic
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with email '{email}' not found"))
            return

        clinic = user.clinic
        if not clinic:
            self.stdout.write(self.style.ERROR(f"User '{email}' has no associated clinic"))
            return

        self.stdout.write(f"Populating lab tests for clinic: {clinic.name}")

        # Clear existing lab tests if requested
        if clear:
            deleted_count = LabTest.objects.filter(clinic=clinic).delete()[0]
            self.stdout.write(self.style.WARNING(f"Cleared {deleted_count} existing lab tests"))

        # Create lab tests
        created_count = 0
        skipped_count = 0

        for test_data in COMMON_LAB_TESTS:
            # Check if test already exists
            exists = LabTest.objects.filter(
                clinic=clinic,
                name=test_data["name"],
            ).exists()

            if exists:
                skipped_count += 1
                continue

            LabTest.objects.create(
                clinic=clinic,
                is_active=True,
                **test_data,
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_count} lab tests, skipped {skipped_count} (already exist)")
        )
        self.stdout.write(
            self.style.SUCCESS(f"Total lab tests in database: {LabTest.objects.filter(clinic=clinic).count()}")
        )
