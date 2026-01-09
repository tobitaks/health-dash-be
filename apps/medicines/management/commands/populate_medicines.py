"""
Management command to populate common medicines for a clinic.
"""

from django.core.management.base import BaseCommand

from apps.medicines.models import Medicine
from apps.users.models import CustomUser

# Common medicines in the Philippines
COMMON_MEDICINES = [
    # Antibiotics
    {
        "generic_name": "Amoxicillin",
        "brand_name": "Amoxil",
        "strength": "500mg",
        "form": "capsule",
        "category": "antibiotic",
        "default_sig": "1 capsule 3 times a day for 7 days",
        "default_quantity": 21,
    },
    {
        "generic_name": "Amoxicillin",
        "brand_name": "Amoxil",
        "strength": "250mg",
        "form": "capsule",
        "category": "antibiotic",
        "default_sig": "1 capsule 3 times a day for 7 days",
        "default_quantity": 21,
    },
    {
        "generic_name": "Amoxicillin",
        "brand_name": "Amoxil",
        "strength": "250mg/5ml",
        "form": "suspension",
        "category": "antibiotic",
        "default_sig": "5ml 3 times a day for 7 days",
        "default_quantity": 1,
    },
    {
        "generic_name": "Azithromycin",
        "brand_name": "Zithromax",
        "strength": "500mg",
        "form": "tablet",
        "category": "antibiotic",
        "default_sig": "1 tablet once daily for 3 days",
        "default_quantity": 3,
    },
    {
        "generic_name": "Co-Amoxiclav",
        "brand_name": "Augmentin",
        "strength": "625mg",
        "form": "tablet",
        "category": "antibiotic",
        "default_sig": "1 tablet 2 times a day for 7 days",
        "default_quantity": 14,
    },
    {
        "generic_name": "Cefalexin",
        "brand_name": "Keflex",
        "strength": "500mg",
        "form": "capsule",
        "category": "antibiotic",
        "default_sig": "1 capsule 4 times a day for 7 days",
        "default_quantity": 28,
    },
    {
        "generic_name": "Ciprofloxacin",
        "brand_name": "Ciprobay",
        "strength": "500mg",
        "form": "tablet",
        "category": "antibiotic",
        "default_sig": "1 tablet 2 times a day for 7 days",
        "default_quantity": 14,
    },
    {
        "generic_name": "Metronidazole",
        "brand_name": "Flagyl",
        "strength": "500mg",
        "form": "tablet",
        "category": "antibiotic",
        "default_sig": "1 tablet 3 times a day for 7 days",
        "default_quantity": 21,
    },
    # Analgesics / Pain Relievers
    {
        "generic_name": "Paracetamol",
        "brand_name": "Biogesic",
        "strength": "500mg",
        "form": "tablet",
        "category": "analgesic",
        "default_sig": "1-2 tablets every 4-6 hours as needed for pain/fever",
        "default_quantity": 20,
    },
    {
        "generic_name": "Paracetamol",
        "brand_name": "Calpol",
        "strength": "250mg/5ml",
        "form": "syrup",
        "category": "analgesic",
        "default_sig": "5-10ml every 4-6 hours as needed for pain/fever",
        "default_quantity": 1,
    },
    {
        "generic_name": "Ibuprofen",
        "brand_name": "Advil",
        "strength": "200mg",
        "form": "tablet",
        "category": "nsaid",
        "default_sig": "1-2 tablets every 6-8 hours as needed with food",
        "default_quantity": 20,
    },
    {
        "generic_name": "Ibuprofen",
        "brand_name": "Advil",
        "strength": "400mg",
        "form": "tablet",
        "category": "nsaid",
        "default_sig": "1 tablet every 6-8 hours as needed with food",
        "default_quantity": 20,
    },
    {
        "generic_name": "Mefenamic Acid",
        "brand_name": "Ponstan",
        "strength": "500mg",
        "form": "capsule",
        "category": "nsaid",
        "default_sig": "1 capsule 3 times a day after meals",
        "default_quantity": 15,
    },
    {
        "generic_name": "Celecoxib",
        "brand_name": "Celebrex",
        "strength": "200mg",
        "form": "capsule",
        "category": "nsaid",
        "default_sig": "1 capsule once or twice daily",
        "default_quantity": 14,
    },
    # Antihistamines
    {
        "generic_name": "Cetirizine",
        "brand_name": "Zyrtec",
        "strength": "10mg",
        "form": "tablet",
        "category": "antihistamine",
        "default_sig": "1 tablet once daily at bedtime",
        "default_quantity": 14,
    },
    {
        "generic_name": "Loratadine",
        "brand_name": "Claritin",
        "strength": "10mg",
        "form": "tablet",
        "category": "antihistamine",
        "default_sig": "1 tablet once daily",
        "default_quantity": 14,
    },
    {
        "generic_name": "Diphenhydramine",
        "brand_name": "Benadryl",
        "strength": "25mg",
        "form": "capsule",
        "category": "antihistamine",
        "default_sig": "1 capsule every 6-8 hours as needed",
        "default_quantity": 12,
    },
    # Antihypertensives
    {
        "generic_name": "Amlodipine",
        "brand_name": "Norvasc",
        "strength": "5mg",
        "form": "tablet",
        "category": "antihypertensive",
        "default_sig": "1 tablet once daily",
        "default_quantity": 30,
    },
    {
        "generic_name": "Amlodipine",
        "brand_name": "Norvasc",
        "strength": "10mg",
        "form": "tablet",
        "category": "antihypertensive",
        "default_sig": "1 tablet once daily",
        "default_quantity": 30,
    },
    {
        "generic_name": "Losartan",
        "brand_name": "Cozaar",
        "strength": "50mg",
        "form": "tablet",
        "category": "antihypertensive",
        "default_sig": "1 tablet once daily",
        "default_quantity": 30,
    },
    {
        "generic_name": "Losartan",
        "brand_name": "Cozaar",
        "strength": "100mg",
        "form": "tablet",
        "category": "antihypertensive",
        "default_sig": "1 tablet once daily",
        "default_quantity": 30,
    },
    {
        "generic_name": "Metoprolol",
        "brand_name": "Lopressor",
        "strength": "50mg",
        "form": "tablet",
        "category": "cardiovascular",
        "default_sig": "1 tablet twice daily",
        "default_quantity": 60,
    },
    # Antidiabetics
    {
        "generic_name": "Metformin",
        "brand_name": "Glucophage",
        "strength": "500mg",
        "form": "tablet",
        "category": "antidiabetic",
        "default_sig": "1 tablet twice daily with meals",
        "default_quantity": 60,
    },
    {
        "generic_name": "Metformin",
        "brand_name": "Glucophage",
        "strength": "850mg",
        "form": "tablet",
        "category": "antidiabetic",
        "default_sig": "1 tablet twice daily with meals",
        "default_quantity": 60,
    },
    {
        "generic_name": "Glimepiride",
        "brand_name": "Amaryl",
        "strength": "2mg",
        "form": "tablet",
        "category": "antidiabetic",
        "default_sig": "1 tablet once daily before breakfast",
        "default_quantity": 30,
    },
    # GI Medications
    {
        "generic_name": "Omeprazole",
        "brand_name": "Prilosec",
        "strength": "20mg",
        "form": "capsule",
        "category": "antacid",
        "default_sig": "1 capsule once daily before breakfast",
        "default_quantity": 30,
    },
    {
        "generic_name": "Omeprazole",
        "brand_name": "Prilosec",
        "strength": "40mg",
        "form": "capsule",
        "category": "antacid",
        "default_sig": "1 capsule once daily before breakfast",
        "default_quantity": 30,
    },
    {
        "generic_name": "Lansoprazole",
        "brand_name": "Prevacid",
        "strength": "30mg",
        "form": "capsule",
        "category": "antacid",
        "default_sig": "1 capsule once daily before breakfast",
        "default_quantity": 30,
    },
    {
        "generic_name": "Loperamide",
        "brand_name": "Imodium",
        "strength": "2mg",
        "form": "capsule",
        "category": "antidiarrheal",
        "default_sig": "2 capsules initially, then 1 after each loose stool. Max 8/day",
        "default_quantity": 12,
    },
    {
        "generic_name": "Metoclopramide",
        "brand_name": "Plasil",
        "strength": "10mg",
        "form": "tablet",
        "category": "antiemetic",
        "default_sig": "1 tablet 3 times a day before meals",
        "default_quantity": 21,
    },
    {
        "generic_name": "Domperidone",
        "brand_name": "Motilium",
        "strength": "10mg",
        "form": "tablet",
        "category": "antiemetic",
        "default_sig": "1 tablet 3 times a day before meals",
        "default_quantity": 21,
    },
    # Respiratory
    {
        "generic_name": "Salbutamol",
        "brand_name": "Ventolin",
        "strength": "100mcg/dose",
        "form": "inhaler",
        "category": "bronchodilator",
        "default_sig": "2 puffs every 4-6 hours as needed",
        "default_quantity": 1,
    },
    {
        "generic_name": "Salbutamol",
        "brand_name": "Ventolin",
        "strength": "2mg/5ml",
        "form": "syrup",
        "category": "bronchodilator",
        "default_sig": "5-10ml 3 times a day",
        "default_quantity": 1,
    },
    {
        "generic_name": "Montelukast",
        "brand_name": "Singulair",
        "strength": "10mg",
        "form": "tablet",
        "category": "bronchodilator",
        "default_sig": "1 tablet once daily at bedtime",
        "default_quantity": 30,
    },
    {
        "generic_name": "Fluticasone",
        "brand_name": "Flixonase",
        "strength": "50mcg/spray",
        "form": "nasal_spray",
        "category": "corticosteroid",
        "default_sig": "2 sprays per nostril once daily",
        "default_quantity": 1,
    },
    {
        "generic_name": "Carbocisteine",
        "brand_name": "Solmux",
        "strength": "500mg",
        "form": "capsule",
        "category": "other",
        "default_sig": "1 capsule 3 times a day",
        "default_quantity": 21,
        "notes": "Mucolytic - helps loosen phlegm",
    },
    {
        "generic_name": "Dextromethorphan",
        "brand_name": "Robitussin DM",
        "strength": "15mg/5ml",
        "form": "syrup",
        "category": "other",
        "default_sig": "10ml every 6-8 hours as needed for cough",
        "default_quantity": 1,
        "notes": "Cough suppressant",
    },
    # Vitamins/Supplements
    {
        "generic_name": "Vitamin B Complex",
        "brand_name": "Neurobion",
        "strength": "",
        "form": "tablet",
        "category": "vitamin",
        "default_sig": "1 tablet once daily",
        "default_quantity": 30,
    },
    {
        "generic_name": "Vitamin C",
        "brand_name": "Ascorbic Acid",
        "strength": "500mg",
        "form": "tablet",
        "category": "vitamin",
        "default_sig": "1 tablet once or twice daily",
        "default_quantity": 30,
    },
    {
        "generic_name": "Vitamin D3",
        "brand_name": "Cholecalciferol",
        "strength": "1000IU",
        "form": "softgel",
        "category": "vitamin",
        "default_sig": "1 softgel once daily with food",
        "default_quantity": 30,
    },
    {
        "generic_name": "Ferrous Sulfate",
        "brand_name": "Iberet",
        "strength": "325mg",
        "form": "tablet",
        "category": "vitamin",
        "default_sig": "1 tablet once daily",
        "default_quantity": 30,
        "notes": "Iron supplement - for anemia",
    },
    {
        "generic_name": "Calcium Carbonate + Vitamin D",
        "brand_name": "Caltrate",
        "strength": "600mg/400IU",
        "form": "tablet",
        "category": "vitamin",
        "default_sig": "1 tablet once daily with meals",
        "default_quantity": 30,
    },
    # Topical
    {
        "generic_name": "Hydrocortisone",
        "brand_name": "Hydrocortisone",
        "strength": "1%",
        "form": "cream",
        "category": "dermatological",
        "default_sig": "Apply thin layer to affected area 2-3 times daily",
        "default_quantity": 1,
    },
    {
        "generic_name": "Mupirocin",
        "brand_name": "Bactroban",
        "strength": "2%",
        "form": "ointment",
        "category": "dermatological",
        "default_sig": "Apply to affected area 3 times daily for 7 days",
        "default_quantity": 1,
    },
    {
        "generic_name": "Clotrimazole",
        "brand_name": "Canesten",
        "strength": "1%",
        "form": "cream",
        "category": "antifungal",
        "default_sig": "Apply to affected area twice daily for 2-4 weeks",
        "default_quantity": 1,
    },
    {
        "generic_name": "Diclofenac",
        "brand_name": "Voltaren",
        "strength": "1%",
        "form": "gel",
        "category": "nsaid",
        "default_sig": "Apply to affected area 3-4 times daily",
        "default_quantity": 1,
        "notes": "Topical pain relief",
    },
    # Eye Drops
    {
        "generic_name": "Tobramycin",
        "brand_name": "Tobrex",
        "strength": "0.3%",
        "form": "drops",
        "category": "ophthalmic",
        "default_sig": "1-2 drops to affected eye 4 times daily for 7 days",
        "default_quantity": 1,
    },
    {
        "generic_name": "Artificial Tears",
        "brand_name": "Tears Naturale",
        "strength": "",
        "form": "drops",
        "category": "ophthalmic",
        "default_sig": "1-2 drops to affected eye as needed",
        "default_quantity": 1,
    },
    # Cardiovascular
    {
        "generic_name": "Atorvastatin",
        "brand_name": "Lipitor",
        "strength": "20mg",
        "form": "tablet",
        "category": "cardiovascular",
        "default_sig": "1 tablet once daily at bedtime",
        "default_quantity": 30,
    },
    {
        "generic_name": "Aspirin",
        "brand_name": "Aspirin",
        "strength": "80mg",
        "form": "tablet",
        "category": "cardiovascular",
        "default_sig": "1 tablet once daily",
        "default_quantity": 30,
        "notes": "Low-dose aspirin for cardiac protection",
    },
    {
        "generic_name": "Clopidogrel",
        "brand_name": "Plavix",
        "strength": "75mg",
        "form": "tablet",
        "category": "cardiovascular",
        "default_sig": "1 tablet once daily",
        "default_quantity": 30,
    },
]


class Command(BaseCommand):
    help = "Populate common medicines for a clinic"

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
            help="Clear existing medicines before populating",
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

        self.stdout.write(f"Populating medicines for clinic: {clinic.name}")

        # Clear existing medicines if requested
        if clear:
            deleted_count = Medicine.objects.filter(clinic=clinic).delete()[0]
            self.stdout.write(self.style.WARNING(f"Cleared {deleted_count} existing medicines"))

        # Create medicines
        created_count = 0
        skipped_count = 0

        for medicine_data in COMMON_MEDICINES:
            # Check if medicine already exists
            exists = Medicine.objects.filter(
                clinic=clinic,
                generic_name=medicine_data["generic_name"],
                strength=medicine_data["strength"],
                form=medicine_data["form"],
            ).exists()

            if exists:
                skipped_count += 1
                continue

            Medicine.objects.create(
                clinic=clinic,
                **medicine_data,
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_count} medicines, skipped {skipped_count} (already exist)")
        )
        self.stdout.write(
            self.style.SUCCESS(f"Total medicines in database: {Medicine.objects.filter(clinic=clinic).count()}")
        )
