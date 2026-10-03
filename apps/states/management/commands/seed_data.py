"""
Civic AI — Seed Initial Data
Usage: python manage.py seed_data
Seeds: Languages, States (AP + TN), Districts, Scheme Categories, Sample Schemes
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seed Civic AI with initial data (states, languages, categories, sample schemes)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('>>> Seeding Civic AI initial data...'))

        self._seed_languages()
        self._seed_states()
        self._seed_districts()
        self._seed_categories()
        self._seed_sample_schemes()

        self.stdout.write(self.style.SUCCESS('[OK] Seed data loaded successfully!'))

    def _seed_languages(self):
        from apps.states.models import Language
        self.stdout.write('  → Languages...')

        languages_data = [
            {'code': 'en', 'name': 'English', 'native_name': 'English', 'display_order': 1, 'flag_emoji': '🇬🇧'},
            {'code': 'ta', 'name': 'Tamil', 'native_name': 'தமிழ்', 'display_order': 2, 'flag_emoji': '🇮🇳'},
            {'code': 'te', 'name': 'Telugu', 'native_name': 'తెలుగు', 'display_order': 3, 'flag_emoji': '🇮🇳'},
        ]

        for data in languages_data:
            lang, created = Language.objects.get_or_create(code=data['code'], defaults=data)
            if created:
                self.stdout.write(f'    Created: {lang.name}')
            else:
                self.stdout.write(f'    Exists: {lang.name}')

    def _seed_states(self):
        from apps.states.models import State, Language
        self.stdout.write('  → States...')

        en = Language.objects.get(code='en')
        ta = Language.objects.get(code='ta')
        te = Language.objects.get(code='te')

        states_data = [
            {
                'code': 'AP',
                'name': 'Andhra Pradesh',
                'native_name': 'ఆంధ్ర ప్రదేశ్',
                'slug': 'andhra-pradesh',
                'display_order': 1,
                'capital': 'Amaravati',
                'region': 'South India',
                'transition_title': 'Welcome to Andhra Pradesh',
                'transition_subtitle': 'Government schemes and citizen services personalized for you.',
                'transition_image_url': 'images/civic_ai/states/ap_transition.png',
                'transition_secondary_image_url': 'images/civic_ai/states/ap_login.png',
                'transition_color_primary': '#003580',
                'transition_color_accent': '#FFD700',
                'transition_landmark': 'Tirumala Venkateswara Temple, Tirupati',
                'languages': [en, te],
            },
            {
                'code': 'TN',
                'name': 'Tamil Nadu',
                'native_name': 'தமிழ் நாடு',
                'slug': 'tamil-nadu',
                'display_order': 2,
                'capital': 'Chennai',
                'region': 'South India',
                'transition_title': 'Welcome to Tamil Nadu',
                'transition_subtitle': 'Government schemes and citizen services personalized for you.',
                'transition_image_url': 'images/civic_ai/states/tn_transition.png',
                'transition_secondary_image_url': 'images/civic_ai/states/tn_login.png',
                'transition_color_primary': '#8B0000',
                'transition_color_accent': '#FFD700',
                'transition_landmark': 'Meenakshi Amman Temple, Madurai',
                'languages': [en, ta],
            },
        ]

        for data in states_data:
            languages = data.pop('languages')
            state, created = State.objects.get_or_create(
                slug=data['slug'],
                defaults={**data, 'is_active': True}
            )
            state.languages.set(languages)
            if created:
                self.stdout.write(f'    Created: {state.name}')
            else:
                # Update transition content if exists
                for key, val in data.items():
                    setattr(state, key, val)
                state.save()
                self.stdout.write(f'    Updated: {state.name}')

    def _seed_districts(self):
        from apps.states.models import State, District
        self.stdout.write('  → Districts...')

        ap_districts = [
            'Visakhapatnam', 'Krishna', 'Guntur', 'West Godavari', 'East Godavari',
            'Kurnool', 'Nellore', 'Kadapa', 'Chittoor', 'Prakasam',
            'Srikakulam', 'Vizianagaram', 'Anantapur',
        ]
        tn_districts = [
            'Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli', 'Salem',
            'Tirunelveli', 'Vellore', 'Erode', 'Thanjavur', 'Dindigul',
            'Kancheepuram', 'Cuddalore', 'Tiruppur', 'Ranipet', 'Chengalpet',
        ]

        try:
            ap = State.objects.get(slug='andhra-pradesh')
            for name in ap_districts:
                District.objects.get_or_create(state=ap, name=name, defaults={'is_active': True})
        except State.DoesNotExist:
            pass

        try:
            tn = State.objects.get(slug='tamil-nadu')
            for name in tn_districts:
                District.objects.get_or_create(state=tn, name=name, defaults={'is_active': True})
        except State.DoesNotExist:
            pass

        self.stdout.write(f'    Districts seeded for AP and TN')

    def _seed_categories(self):
        from apps.schemes.models import SchemeCategory
        self.stdout.write('  → Scheme Categories...')

        categories = [
            ('Education', '🎓', '#4A90E2', 1),
            ('Scholarships', '📚', '#7B68EE', 2),
            ('Agriculture & Farmers', '🌾', '#2E8B57', 3),
            ('Employment & Skills', '💼', '#FF8C00', 4),
            ('Women Welfare', '♀', '#FF69B4', 5),
            ('Health', '🏥', '#DC143C', 6),
            ('Housing', '🏠', '#8B4513', 7),
            ('Senior Citizens', '👴', '#708090', 8),
            ('Disability Support', '♿', '#6495ED', 9),
            ('Business & Startup', '🚀', '#FF6347', 10),
            ('Financial Assistance', '💰', '#32CD32', 11),
            ('Insurance', '🛡', '#4169E1', 12),
            ('Student Welfare', '🎒', '#9370DB', 13),
            ('Rural Development', '🌄', '#228B22', 14),
            ('Social Security', '🤝', '#20B2AA', 15),
        ]

        for name, icon, color, order in categories:
            cat, created = SchemeCategory.objects.get_or_create(
                slug=slugify(name),
                defaults={'name': name, 'icon': icon, 'color': color, 'display_order': order, 'is_active': True}
            )
            if created:
                self.stdout.write(f'    Created category: {name}')

    def _seed_sample_schemes(self):
        from apps.states.models import State
        from apps.schemes.models import (
            Scheme, SchemeVersion, EligibilityRule,
            RequiredDocument, Department, SchemeCategory
        )
        self.stdout.write('  → Sample Schemes...')

        try:
            ap = State.objects.get(slug='andhra-pradesh')
            tn = State.objects.get(slug='tamil-nadu')
        except State.DoesNotExist:
            self.stdout.write(self.style.WARNING('    States not found — skipping schemes'))
            return

        scholarship_cat = SchemeCategory.objects.filter(slug='scholarships').first()
        farmer_cat = SchemeCategory.objects.filter(slug='agriculture-farmers').first()
        employment_cat = SchemeCategory.objects.filter(slug='employment-skills').first()

        schemes_data = [
            {
                'name': 'Dr. YSR Rythu Bharosa PM-KISAN',
                'slug': 'ysr-rythu-bharosa-pm-kisan',
                'level': 'state',
                'state': ap,
                'description': 'Financial support to farmer families in AP combining state and central government assistance. Eligible farmers receive ₹13,500 per year.',
                'benefit': '₹13,500 per year per farmer family (₹4,000 from State + ₹2,000 bonus + ₹6,000 PM-KISAN)',
                'how_to_apply': 'Register at village secretariat or meeseva center. Aadhaar and land records required.',
                'official_url': 'https://apagrisnet.gov.in/',
                'categories': [farmer_cat] if farmer_cat else [],
                'rules': [
                    {'type': EligibilityRule.RULE_STATE, 'value': 'AP', 'label': 'Andhra Pradesh Resident'},
                    {'type': EligibilityRule.RULE_IS_FARMER, 'value': 'true', 'label': 'Must be a farmer'},
                    {'type': EligibilityRule.RULE_MAX_INDIVIDUAL_INCOME, 'value': '500000', 'label': 'Income below ₹5 lakh'},
                ],
                'documents': ['Aadhaar Card', 'Land Records / Pattadar Passbook', 'Bank Account Details', 'Mobile Number linked to Aadhaar'],
            },
            {
                'name': 'Amma Vodi Scheme (AP)',
                'slug': 'amma-vodi-ap',
                'level': 'state',
                'state': ap,
                'description': 'Financial incentive for mothers who send their children to government schools in Andhra Pradesh.',
                'benefit': '₹15,000 per year to mothers of students in Classes 1-12 in government schools',
                'how_to_apply': 'Eligible mothers are auto-identified through school enrollment. Visit school or meeseva.',
                'official_url': 'https://ammavodi.ap.gov.in/',
                'categories': [scholarship_cat] if scholarship_cat else [],
                'rules': [
                    {'type': EligibilityRule.RULE_STATE, 'value': 'AP', 'label': 'Andhra Pradesh Resident'},
                    {'type': EligibilityRule.RULE_GENDER, 'value': 'female', 'label': 'Female (Mother)'},
                    {'type': EligibilityRule.RULE_MAX_FAMILY_INCOME, 'value': '500000', 'label': 'BPL/EWS Family'},
                ],
                'documents': ['Aadhaar Card', 'Student school enrollment proof', 'Bank Account', 'Income Certificate'],
            },
            {
                'name': 'YSR Pension Kanuka',
                'slug': 'ysr-pension-kanuka',
                'level': 'state',
                'state': ap,
                'description': 'Monthly pension for elderly, widows, weavers, toddy workers, fishermen, and disabled persons in Andhra Pradesh.',
                'benefit': '₹2,500 to ₹3,000 per month depending on category',
                'how_to_apply': 'Apply at village secretariat with required documents.',
                'official_url': 'https://pensionkanuka.ap.gov.in/',
                'categories': [],
                'rules': [
                    {'type': EligibilityRule.RULE_STATE, 'value': 'AP', 'label': 'Andhra Pradesh Resident'},
                    {'type': EligibilityRule.RULE_MAX_FAMILY_INCOME, 'value': '250000', 'label': 'Income below ₹2.5 lakh'},
                ],
                'documents': ['Aadhaar Card', 'Income Certificate', 'Age Proof / Disability Certificate'],
            },
            {
                'name': 'Kalaignar Magalir Urimai Scheme (TN)',
                'slug': 'kalaignar-magalir-urimai-tn',
                'level': 'state',
                'state': tn,
                'description': "Monthly financial assistance to women heads of households in Tamil Nadu as part of the Chief Minister's scheme.",
                'benefit': '₹1,000 per month to eligible women',
                'how_to_apply': 'Register at nearest government office or ration shop. Aadhaar and bank account required.',
                'official_url': 'https://www.tn.gov.in/',
                'categories': [],
                'rules': [
                    {'type': EligibilityRule.RULE_STATE, 'value': 'TN', 'label': 'Tamil Nadu Resident'},
                    {'type': EligibilityRule.RULE_GENDER, 'value': 'female', 'label': 'Female'},
                    {'type': EligibilityRule.RULE_MIN_AGE, 'value': '21', 'label': 'Age 21 and above'},
                ],
                'documents': ['Aadhaar Card', 'Ration Card', 'Bank Passbook', 'Residential Proof'],
            },
            {
                'name': 'Tamil Nadu Chief Minister\'s Kisan Scheme',
                'slug': 'tn-chief-minister-kisan',
                'level': 'state',
                'state': tn,
                'description': 'Financial assistance to small and marginal farmers in Tamil Nadu for agricultural support.',
                'benefit': '₹4,000 per year per farmer family',
                'how_to_apply': 'Register at Agriculture Department office or online portal.',
                'official_url': 'https://agri.tn.gov.in/',
                'categories': [farmer_cat] if farmer_cat else [],
                'rules': [
                    {'type': EligibilityRule.RULE_STATE, 'value': 'TN', 'label': 'Tamil Nadu Resident'},
                    {'type': EligibilityRule.RULE_IS_FARMER, 'value': 'true', 'label': 'Must be a farmer'},
                    {'type': EligibilityRule.RULE_LAND_HOLDING, 'value': 'marginal,small', 'label': 'Small or Marginal Farmer'},
                ],
                'documents': ['Aadhaar Card', 'Land Records', 'Bank Passbook', 'Mobile Number'],
            },
            {
                'name': 'PM Scholarship Scheme for Ex-Servicemen',
                'slug': 'pm-scholarship-ex-servicemen',
                'level': 'central',
                'state': None,
                'description': 'Central government scholarship for wards and widows of ex-servicemen and ex-coast guard personnel pursuing technical/professional education.',
                'benefit': '₹2,500/month for boys and ₹3,000/month for girls pursuing recognized technical/professional courses',
                'how_to_apply': 'Apply online at National Scholarship Portal (NSP): scholarships.gov.in',
                'official_url': 'https://scholarships.gov.in/',
                'categories': [scholarship_cat] if scholarship_cat else [],
                'rules': [
                    {'type': EligibilityRule.RULE_IS_STUDENT, 'value': 'true', 'label': 'Must be a student'},
                    {'type': EligibilityRule.RULE_EDUCATION_MIN, 'value': 'higher_secondary', 'label': 'Passed Class 12'},
                    {'type': EligibilityRule.RULE_MIN_AGE, 'value': '16', 'label': 'Age 16 and above'},
                    {'type': EligibilityRule.RULE_MAX_AGE, 'value': '30', 'label': 'Age below 30'},
                ],
                'documents': ['Aadhaar Card', 'Ex-serviceman discharge certificate', 'Marksheets', 'Admission proof', 'Bank Account'],
            },
            {
                'name': 'PM Employment Generation Programme (PMEGP)',
                'slug': 'pmegp',
                'level': 'central',
                'state': None,
                'description': 'Central scheme to generate employment through establishment of micro enterprises in rural and urban areas.',
                'benefit': 'Subsidy of 15-35% on project cost up to ₹25 lakh for manufacturing and ₹10 lakh for service sector',
                'how_to_apply': 'Apply through KVIC/KVIB/DIC or online at PMEGP portal.',
                'official_url': 'https://www.kviconline.gov.in/pmegpeportal/',
                'categories': [employment_cat] if employment_cat else [],
                'rules': [
                    {'type': EligibilityRule.RULE_MIN_AGE, 'value': '18', 'label': 'Age 18 and above'},
                    {'type': EligibilityRule.RULE_EDUCATION_MIN, 'value': 'secondary', 'label': 'Minimum Class 8 pass (for projects > ₹10 lakh)'},
                    {'type': EligibilityRule.RULE_IS_ENTREPRENEUR, 'value': 'true', 'label': 'Planning to start enterprise', 'mandatory': False},
                ],
                'documents': ['Aadhaar Card', 'Project Report', 'Educational Certificate', 'Caste Certificate (if applicable)', 'Bank Account'],
            },
        ]

        for s_data in schemes_data:
            rules_data = s_data.pop('rules')
            documents_data = s_data.pop('documents')
            categories_data = s_data.pop('categories')

            scheme, created = Scheme.objects.get_or_create(
                slug=s_data['slug'],
                defaults={
                    'name': s_data['name'],
                    'level': s_data['level'],
                    'state': s_data.get('state'),
                    'status': Scheme.STATUS_ACTIVE,
                    'official_url': s_data.get('official_url', ''),
                    'is_new': True,
                }
            )

            if categories_data:
                scheme.categories.set([c for c in categories_data if c])

            # Create version
            version, v_created = SchemeVersion.objects.get_or_create(
                scheme=scheme,
                version_number=1,
                defaults={
                    'description': s_data['description'],
                    'benefit_summary': s_data['benefit'],
                    'how_to_apply': s_data['how_to_apply'],
                    'review_status': 'approved',
                    'source_url': s_data.get('official_url', ''),
                }
            )

            if v_created:
                # Add eligibility rules
                for r in rules_data:
                    EligibilityRule.objects.create(
                        scheme_version=version,
                        rule_type=r['type'],
                        operator=EligibilityRule.OPERATOR_EQ if 'eq' not in r else r.get('op', EligibilityRule.OPERATOR_EQ),
                        value=r['value'],
                        display_label=r.get('label', ''),
                        is_mandatory=r.get('mandatory', True),
                    )

                # Add required documents
                for i, doc in enumerate(documents_data):
                    RequiredDocument.objects.create(
                        scheme_version=version,
                        name=doc,
                        is_mandatory=True,
                        display_order=i,
                    )

                # Set as current version
                scheme.current_version = version
                scheme.save(update_fields=['current_version'])

            action = 'Created' if created else 'Exists'
            self.stdout.write(f'    {action}: {scheme.name}')

        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(schemes_data)} schemes seeded'))

