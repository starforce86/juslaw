from django.core.management import BaseCommand

from apps.business.models.extra import PaymentMethods

from ....users.models import (
    AppointmentType,
    Currencies,
    FeeKind,
    FirmSize,
    Language,
    PaymentType,
    Speciality,
    TimeZone,
)
from ...models import ForumPracticeAreas, Topic

specialities_data = [
    {'title': 'Accounting Law Practice'},
    {'title': 'Advertising Law'},
    {'title': 'Asset Protection'},
    {'title': 'Banking and Finance'},
    {'title': 'Bankruptcy & Corporate Restructuring/Creditor’s Rights'},
    {'title': 'Communications Law'},
    {'title': 'Corporate Trust and Agency'},
    {'title': 'Corporate/M&A'},
    {'title': 'Criminal Law'},
    {'title': 'Defamation'},
    {'title': 'Education'},
    {'title': 'Entertainment and Sports'},
    {'title': 'Equipment Lease Financing'},
    {'title': 'Elder Law'},
    {'title': 'Estate Litigation'},
    {'title': 'Family Matters'},
    {'title': 'Global Outsourcing and Procurement'},
    {'title': 'Healthcare'},
    {'title': 'Hospitality, Food Service, Restaurants'},
    {'title': 'Intellectual Property'},
    {'title': 'Internet & Technology'},
    {'title': 'Labor, Employment & Employee Benefits'},
    {'title': 'Legal Ethics & Law Firm Practice'},
    {'title': 'Libel'},
    {'title': 'Litigation'},
    {'title': 'Maritime and Multimodal Transportation'},
    {'title': 'Marketplace Lending & Fin/Tech'},
    {'title': 'Matrimonial and Family Law'},
    {'title': 'Privacy & Cybersecurity'},
    {'title': 'Private Funds'},
    {'title': 'Promotions Law'},
    {'title': 'Real Estate'},
    {'title': 'Securities and Capital Markets'},
    {'title': 'Securities Litigation'},
    {'title': 'Tax'},
    {'title': 'Trusts and Estates'},
    {'title': 'Web Accessibility'},
    {'title': 'White Collar Criminal Defense and Government Investigations'},
    {'title': 'Personal Injuries'},
    {'title': 'Immigration Law'},
    {'title': 'International Law'},
]

categories_data = [
    {
        'title': 'Accounting Law Practice',
        'description': 'Accounting and Auditing where there are challenges '
                       'accounting firms and individual accountants face from '
                       'sea changes in the global economy and the '
                       'litigation that '
                       'often follows.',
    },
    {
        'title': 'Advertising Law',
        'description': 'Vetting claims about products and managing business '
                       'practices to avoid misleading, deceiving, or'
                       ' defrauding'
                       ' consumers.',
    },
    {
        'title': 'Asset Protection',
        'description': 'A set of legal techniques and a body of statutory and '
                       'common law dealing with protecting assets of '
                       'individuals '
                       'and business entities from civil money judgements.',
    },
    {
        'title': 'Banking and Finance',
        'description': 'Stems from the banking and financial industries are '
                       'heavily regulated by both state and federal law. '
                       ' These '
                       'laws impose reporting requirements for banks and '
                       'other '
                       'financial institutions, govern securities and other '
                       'transactions, and regulate taxes.',
    },
    {
        'title': 'Bankruptcy & Corporate Restructuring/Creditor’s Rights',
        'description': 'Finding creative solutions to complex issues affecting'
                       ' distressed businesses or funds throughout the United '
                       'States and abroad.',
    },
    {
        'title': 'Communications Law',
        'description': 'Exchange of information using technology.  Its any '
                       'law that involves the regulation and use of '
                       'electronic '
                       'telecommunication.  Communication law includes '
                       'technologies '
                       'like radio, television, cable and broadband internet.',
    },
    {
        'title': 'Corporate Trust and Agency',
        'description': 'Trust created by a corporation in the United '
                       'States is '
                       'most often used to describe the business activities '
                       'of many '
                       'financial services companies and bank that act in a '
                       'fiduciary capacity for investors in a particular '
                       'security (i.e., stock investors or bond investors).',
    },
    {
        'title': 'Corporate/M&A',
        'description': 'Mergers and acquisitions (M&A) are transactions in'
                       ' which '
                       'the ownership of companies, other business '
                       'organizations, '
                       'or their operating units are transferred or '
                       'consolidated'
                       ' with other entities.  As an aspect of strategic '
                       'management, '
                       'M&A can allow enterprises to grow or downsize and'
                       ' change '
                       'the nature of their business or competitive position.',
    },
    {
        'title': 'Criminal Law',
        'description': 'Any crime.  Involving civil and or criminal inclusive,'
                       ' assassination, assault, battery, child abuse, '
                       'criminal'
                       ' negligence, defamation, false imprisonment harassment'
                       ' home invasion homicide intimidation, etc...',
    },
    {
        'title': 'Defamation',
        'description': 'This relates to communications about the reputation '
                       'of another person.  Defamatory speech is a '
                       'communication '
                       'that might hurt the reputation of someone else. '
                       'Libel and slander.  Libel is defamation that is '
                       'written down.  Slander is defamation that’s spoken.',
    },
    {
        'title': 'Education',
        'description': 'This area involves the legal discipline covering all '
                       'issues pertaining to schools, from kindergarten'
                       ' through '
                       'higher education.  Attorneys here have worked also'
                       ' toward '
                       'expanding access to a high-quality education for all '
                       'children as well as providing for greater access to '
                       'higher education.',
    },
    {
        'title': 'Entertainment and Sports',
        'description': 'Entertainment or media law involves a myriad of legal '
                       'disciplines applied to the entertainment industry. '
                       ' Entertainment law frequently involves intellectual '
                       'property law and defamation, first amendment and '
                       'right of publicity issues.  Sports law often involves'
                       ' labor, antitrust, contract and tort law.',
    },
    {
        'title': 'Equipment Lease Financing',
        'description': 'In essence an extended rental agreement under which '
                       'the owner of the equipment allows the user to operate '
                       'or otherwise make use of the equipment in exchange '
                       'for periodic lease payments.',
    },
    {
        'title': 'Elder Law',
        'description': 'Specializes on issues that affect the aging'
                       ' population. '
                       ' The purpose here is to prepare the elderly '
                       'person for '
                       'financial freedom and autonomy through financial'
                       ' planning '
                       'and long term care options.',
    },
    {
        'title': 'Estate Litigation',
        'description': 'Matters involving litigation probate matters, '
                       'estates, '
                       'trusts, fiduciaries, and guardianships.',
    },
    {
        'title': 'Family Matters',
        'description': 'Also called Matrimonial law or the law of domestic '
                       'relations in the areas dealing with family and '
                       'domestic '
                       'relations also involves marriage, civil unions and '
                       'domestic '
                       'partnerships adoption / surrogacy/ child protective '
                       'proceedings.',
    },
    {
        'title': 'Global Outsourcing and Procurement',

        'description': 'Negotiation of sourcing arrangements to avoid '
                       'specific '
                       'risks and challenges for many companies, especially'
                       ' those sourcing on a global basis and those in '
                       'regulated '
                       'industries.',
    },
    {
        'title': 'Healthcare',
        'description': 'Law that regulates the provision of healthcare '
                       'services.  '
                       'Health law governs the relationship between those who '
                       'provide healthcare and those who receive it.  '
                       'Here the attorneys/lawyers focus on one area of '
                       'healthcare law or they may provide comprehensive '
                       'legal services to a healthcare provider.',
    },
    {
        'title': 'Hospitality, Food Service, Restaurants',
        'description': 'To seek help in attorney providing cost-effective, '
                       'practical and efficient legal services in matters'
                       ' related to launch, management and growth of their '
                       'businesses as well as the protection of assets and '
                       'alleviating risk and liabilities…',
    },
    {
        'title': 'Intellectual Property',
        'description': 'Securing and enforcing legal rights of inventions, '
                       'designs and artistic work.  Just as the law protects '
                       'ownership of personal property and real estate, so '
                       'too does it protect the exclusive control of '
                       'intangible'
                       ' assets. Also covers trade secrets / trademarks / '
                       'copyrights and patents.',
    },
    {
        'title': 'Internet & Technology',
        'description': 'Computer hardware and software sale, lease and '
                       'license '
                       'agreements involving E-Commerce / Website '
                       'Disclaimer / '
                       'Cybersquatting Law / General Date Protection '
                       'Regulations '
                       '(GDPR) Privacy Policy Protections and '
                       'orresponding U.S. '
                       'State Statutes / Child Protection and Obscenity '
                       'Enforcement '
                       'Act / Federal Trade Commission Guide Concerning '
                       'the Use of '
                       'Endorsements and Testimonials in Advertising.',
    },
    {
        'title': 'Labor, Employment & Employee Benefits',
        'description': 'Representing Employers of all types and sizes – '
                       'ranging '
                       'from the Fortune 100 to privately held startups, '
                       'including '
                       'businesses both foreign and domestic.  Covering a '
                       'broad '
                       'range of hard-hitting labor and employment law '
                       'issues, '
                       'including major class and collective actions, '
                       'wage and '
                       'hour ERISA litigation.',
    },
    {
        'title': 'Legal Ethics & Law Firm Practice',
        'description': 'From representing small to large law firms in '
                       'civil litigation – Malpractice , Disqualification and '
                       'Sanctions Litigation / Disciplinary Matters / '
                       'Counseling / '
                       'Internal Law Firm Management.',
    },
    {
        'title': 'Libel',
        'description': 'Defamation expressed by print, writing, pictures, '
                       'signs, effigies, or any communication embodied in '
                       'physical form that is injurious to a person’s '
                       'reputation, '
                       'exposes a person to public hatred, contempt or '
                       'ridicule, '
                       'or injures a person in his/her business or '
                       'profession.',
    },
    {
        'title': 'Litigation',
        'description': 'Resolving your disputes in the court system can be '
                       'tort cases, all kinds of cases from contested '
                       'divorces '
                       'to eviction proceedings.',
    },
    {
        'title': 'Maritime and Multimodal Transportation',
        'description': 'If you are hurt in a maritime accident or suffered'
                       ' an offshore injury other areas & the Multimodal'
                       ' Transportation of goods.',
    },
    {
        'title': 'Marketplace Lending & Fin/Tech',
        'description': 'Internet-based platforms engaged in consumer, '
                       'student, and small business lending and providing '
                       'other financial products.  Loan purchasers, warehouse '
                       'line providers and securitizes / complying with the '
                       'novel '
                       'legal and regulatory issues presented by these '
                       'programs '
                       'and '
                       'assist in obtaining access to (or providing) a '
                       'variety of '
                       'funding solutions / issuance programs and regulatory '
                       'advice '
                       '/ lending facilities.',
    },
    {

        'title': 'Matrimonial and Family Law',
        'description': 'Marriage / domestic relations / supervised '
                       'visitation / '
                       'child custody / divorce / alimony / child support / '
                       'annulment, property settlements.',
    },
    {
        'title': 'Privacy & Cybersecurity',
        'description': 'Managing risk and adopting sound privacy and security '
                       'standards in adopting sound privacy and security '
                       'practices '
                       'ensuring regulatory and legal compliance and '
                       'protecting '
                       'their competitive advantage.',
    },
    {
        'title': 'Private Funds',
        'description': 'Formation of private investment funds of all sizes '
                       'and '
                       'investment strategies including buyout funds, growth '
                       'equity'
                       ' funds, middle market funds, infrastructure funds, '
                       'real '
                       'estate funds, debt funds, funds of funds, secondary '
                       'fund, '
                       'special situations funds and hedge funds/ '
                       'establishment '
                       'of investment firms.',
    },
    {
        'title': 'Promotions Law',
        'description': 'State and Federal laws contain provisions governing '
                       'the '
                       'method of operation and advertising for a prize '
                       'promotion / here you have attorneys which will be '
                       'able to guide in regard to various laws, regulations '
                       'and issues that may also be implicated for example '
                       'privacy and data security issues, promotion that are '
                       'directed towards children and mobile technology-based '
                       'promotions.',
    },
    {
        'title': 'Real Estate',
        'description': 'Any law pertaining to land  as well as anything '
                       'permanently attached to the land such as buildings '
                       'and '
                       'other structures / Commercial Leasing / '
                       'Condemnation / '
                       'Eminent Domain / Condominiums Conversion / '
                       'Construction Law / Construction Defects / Deeds / '
                       'Appraisals, etc...',
    },
    {
        'title': 'Securities and Capital Markets',
        'description': 'Any questions dealing with issuance of securities all '
                       'types of securities / transactional securities '
                       '/regulatory aspects / litigation securities law / '
                       'administrative securities.',
    },
    {
        'title': 'Securities Litigation',
        'description': 'Generally, advise regarding a lawsuit filed by '
                       'investors who bought or sold a company’s publicly '
                       'traded securities within a specific period of time '
                       'suffering economic injury as a result of violations '
                       'of the securities law…',
    },
    {
        'title': 'Tax',
        'description': 'Covering rules policies and laws that oversee the '
                       'tax process which involves charges on estates, '
                       'transactions, property, income, licenses and more '
                       'by the '
                       'government.  Duties on imports from foreign countries '
                       'and'
                       ' all compulsory levies imposed by the government '
                       'upon individuals / tax disputes / initial audit to '
                       'IRS '
                       'administrative appeals, Tax Court and final review '
                       'by the '
                       'Court of Appeals or even the U.S. Supreme Court.',
    },
    {

        'title': 'Trusts and Estates',
        'description': 'Planning efficient and effective transfer of assets '
                       'to spouses, to younger generation family members to '
                       'other persons clients wish to benefit and to '
                       'charities / trust agreements preparation / wills /'
                       'power of attorneys / medical directives / closely '
                       'held business structures, '
                       'including partnerships, limited liability companies '
                       'and '
                       'corporations / Wealth Planning / Estate '
                       'Administration /'
                       ' Trust Administration.',
    },
    {

        'title': 'Web Accessibility',
        'description': 'Assisting in both the regulatory aspects and including'
                       ' and '
                       'not limited to guiding ensuring there are no barriers'
                       ' that '
                       'prevent interaction with, or access to websites.',
    },
    {
        'title': 'White Collar Criminal Defense and Government Investigations',
        'description': 'Representation of Corporations, executives, '
                       'individuals ''and public officials in a wide range of '
                       'federal and state'
                       ' prosecutions and investigations and have conducted '
                       'internal'
                       ' investigations for corporations / financial and '
                       'securities'
                       ' violations, money laundering and health care fraud'
                       ' / Wall'
                       ' Street traders…',
    },
    {
        'title': 'Personal Injuries',
        'description': 'If you have suffered any type of personal injury '
                       'arising out of Animal Attacks, Asbestos Exposure '
                       'Cases, Automobile Accidents, Aviation Accidents, '
                       'Back Injuries, Bicycle Accidents, Brain Injury Cases '
                       'and TBI, Burn Injuries, Construction Accident Cases, '
                       'Crane Collapse Cases, Death Cases, Defective Product '
                       'Cases, Defective Drug Cases, Dog Bite Cases, '
                       'DWI Accidents, Electrocution Cases Elevator & '
                       'Escalator Accidents, Emotional Distress Claims, '
                       'Explosions Cases, Slip and Fall Accidents, '
                       'Food Poisoning and E-coli, Ladder Injury Cases, '
                       'Lawn Tractor Roll Overs, Long Term Disability, '
                       'Insurance Claims, Mesothelioma, Motorcycle Accidents, '
                       'Nail Gun Injuries, Nursing Home, Abuse and Neglect – '
                       'Elder Abuse Cases, OSHA Workplace Safety Cases, '
                       'Paralysis Injuries.',
    },
    {
        'title': 'Immigration Law',
        'description': 'If you need an attorney in the areas of EB-1 '
                       'Extraordinary Ability / EB-2 National Interest Waiver '
                       '(NIW) / EB-5 Investor Green card / L1-1 Temporary Work'
                       ' Visa / Treaty National (TN) Temporary Work Visa / '
                       'H-1B Temporary Work Visa for Specialty Workers / '
                       'Marriage-Base Green card and Fiancé Visas / '
                       'Naturalization & Citizenship',
    },
    {
        'title': 'International Law',
        'description': 'If you are looking for a law firm to help you resolve '
                       'a problem involving a foreign country for example, '
                       'you were injured while outside the U.S. on a cruise, '
                       'at a hotel, at an overseas worksite, or elsewhere. '
                       'We recently helped one of our clients recover more '
                       'than $5 million for an injury he sustained in Europe. '
                       'You are trying to re-gain possession of, or '
                       'compensation for, land or other property.You want to'
                       ' enforce a judgment involving a foreign country. You'
                       ' are seeking to invest outside the U.S., including'
                       ' investment in Brazil under Brazil’s “My House, '
                       'My Life” program',
    }
]

fee_kinds_data = [
    {'title': 'Free consultation'},
    {'title': 'Flat rates'},
    {'title': 'Contingency rates'},
    {'title': 'Hourly rates'},
    {'title': 'Alternative agreement'},
]

appointment_type_data = [
    {'title': 'In-Person Appointments'},
    {'title': 'Virtual Appointments'}
]

payment_type_data = [
    {'title': 'Direct Debit(ACH/eCheck)'},
    {'title': 'Paypal'},
    {'title': 'Credit Cards'}
]

language_data = [
    {'title': 'Abkhazian'},
    {'title': 'Afar'},
    {'title': 'Afrikaans'},
    {'title': 'Akan'},
    {'title': 'Albanian'},
    {'title': 'Amharic'},
    {'title': 'Arabic'},
    {'title': 'Aragonese'},
    {'title': 'Armenian'},
    {'title': 'Assamese'},
    {'title': 'Avaric'},
    {'title': 'Avestan'},
    {'title': 'Aymara'},
    {'title': 'Azerbaijani'},
    {'title': 'Bambara'},
    {'title': 'Bashkir'},
    {'title': 'Basque'},
    {'title': 'Belarusian'},
    {'title': 'Bengali'},
    {'title': 'Bihari languages'},
    {'title': 'Bislama'},
    {'title': 'Bokmål, Norwegian; Norwegian Bokmål'},
    {'title': 'Bosnian'},
    {'title': 'Breton'},
    {'title': 'Bulgarian'},
    {'title': 'Burmese'},
    {'title': 'Catalan; Valencian'},
    {'title': 'Central Khmer'},
    {'title': 'Chamorro'},
    {'title': 'Chechen'},
    {'title': 'Chichewa; Chewa; Nyanja'},
    {'title': 'Chinese'},
    {'title': 'Chuvash'},
    {'title': 'Cornish'},
    {'title': 'Corsican'},
    {'title': 'Cree'},
    {'title': 'Croatian'},
    {'title': 'Czech'},
    {'title': 'Danish'},
    {'title': 'Divehi; Dhivehi; Maldivian'},
    {'title': 'Dutch; Flemish'},
    {'title': 'Dzongkha'},
    {'title': 'English'},
    {'title': 'Esperanto'},
    {'title': 'Estonian'},
    {'title': 'Ewe'},
    {'title': 'Faroese'},
    {'title': 'Fijian'},
    {'title': 'Finnish'},
    {'title': 'French'},
    {'title': 'Fulah'},
    {'title': 'Gaelic; Scottish Gaelic'},
    {'title': 'Galician'},
    {'title': 'Ganda'},
    {'title': 'Georgian'},
    {'title': 'German'},
    {'title': 'Greek, Modern (1453-)'},
    {'title': 'Guarani'},
    {'title': 'Gujarati'},
    {'title': 'Haitian; Haitian Creole'},
    {'title': 'Hausa'},
    {'title': 'Hebrew'},
    {'title': 'Herero'},
    {'title': 'Hindi'},
    {'title': 'Hiri Motu'},
    {'title': 'Hungarian'},
    {'title': 'Icelandic'},
    {'title': 'Ido'},
    {'title': 'Igbo'},
    {'title': 'Indonesian'},
    {'title': 'Interlingue; Occidental'},
    {'title': 'Inuktitut'},
    {'title': 'Inupiaq'},
    {'title': 'Irish'},
    {'title': 'Italian'},
    {'title': 'Japanese'},
    {'title': 'Javanese'},
    {'title': 'Kalaallisut; Greenlandic'},
    {'title': 'Kannada'},
    {'title': 'Kanuri'},
    {'title': 'Kashmiri'},
    {'title': 'Kazakh'},
    {'title': 'Kikuyu; Gikuyu'},
    {'title': 'Kinyarwanda'},
    {'title': 'Kirghiz; Kyrgyz'},
    {'title': 'Komi'},
    {'title': 'Kongo'},
    {'title': 'Korean'},
    {'title': 'Kuanyama; Kwanyama'},
    {'title': 'Kurdish'},
    {'title': 'Lao'},
    {'title': 'Latin'},
    {'title': 'Latvian'},
    {'title': 'Limburgan; Limburger; Limburgish'},
    {'title': 'Lingala'},
    {'title': 'Lithuanian'},
    {'title': 'Luba-Katanga'},
    {'title': 'Luxembourgish; Letzeburgesch'},
    {'title': 'Macedonian'},
    {'title': 'Malagasy'},
    {'title': 'Malay'},
    {'title': 'Malayalam'},
    {'title': 'Maltese'},
    {'title': 'Manx'},
    {'title': 'Maori'},
    {'title': 'Marathi'},
    {'title': 'Marshallese'},
    {'title': 'Mongolian'},
    {'title': 'Nauru'},
    {'title': 'Navajo; Navaho'},
    {'title': 'Ndebele, North; North Ndebele'},
    {'title': 'Ndebele, South; South Ndebele'},
    {'title': 'Ndonga'},
    {'title': 'Nepali'},
    {'title': 'Northern Sami'},
    {'title': 'Norwegian'},
    {'title': 'Norwegian Nynorsk; Nynorsk, Norwegian'},
    {'title': 'Occitan (post 1500)'},
    {'title': 'Ojibwa'},
    {'title': 'Oriya'},
    {'title': 'Oromo'},
    {'title': 'Ossetian; Ossetic'},
    {'title': 'Pali'},
    {'title': 'Panjabi; Punjabi'},
    {'title': 'Persian'},
    {'title': 'Polish'},
    {'title': 'Portuguese'},
    {'title': 'Pushto; Pashto'},
    {'title': 'Quechua'},
    {'title': 'Romanian; Moldavian; Moldovan'},
    {'title': 'Romansh'},
    {'title': 'Rundi'},
    {'title': 'Russian'},
    {'title': 'Samoan'},
    {'title': 'Sango'},
    {'title': 'Sanskrit'},
    {'title': 'Sardinian'},
    {'title': 'Serbian'},
    {'title': 'Shona'},
    {'title': 'Sichuan Yi; Nuosu'},
    {'title': 'Sindhi'},
    {'title': 'Sinhala; Sinhalese'},
    {'title': 'Slovak'},
    {'title': 'Slovenian'},
    {'title': 'Somali'},
    {'title': 'Sotho, Southern'},
    {'title': 'Spanish; Castilian'},
    {'title': 'Sundanese'},
    {'title': 'Swahili'},
    {'title': 'Swati'},
    {'title': 'Swedish'},
    {'title': 'Tagalog'},
    {'title': 'Tahitian'},
    {'title': 'Tajik'},
    {'title': 'Tamil'},
    {'title': 'Tatar'},
    {'title': 'Telugu'},
    {'title': 'Thai'},
    {'title': 'Tibetan'},
    {'title': 'Tigrinya'},
    {'title': 'Tonga (Tonga Islands)'},
    {'title': 'Tsonga'},
    {'title': 'Tswana'},
    {'title': 'Turkish'},
    {'title': 'Turkmen'},
    {'title': 'Twi'},
    {'title': 'Uighur; Uyghur'},
    {'title': 'Ukrainian'},
    {'title': 'Urdu'},
    {'title': 'Uzbek'},
    {'title': 'Venda'},
    {'title': 'Vietnamese'},
    {'title': 'Volapük'},
    {'title': 'Walloon'},
    {'title': 'Welsh'},
    {'title': 'Western Frisian'},
    {'title': 'Wolof'},
    {'title': 'Xhosa'},
    {'title': 'Yiddish'},
    {'title': 'Yoruba'},
    {'title': 'Zhuang; Chuang'},
    {'title': 'Zulu'}
]

currencies_data = [
    {'title': 'USD'},
    {'title': 'EUR'},
    {'title': 'JPY'},
    {'title': 'GBP'},
    {'title': 'AUD'},
    {'title': 'CAD'},
    {'title': 'CHF'},
    {'title': 'CNY'},
    {'title': 'HKD'},
    {'title': 'NZD'},
    {'title': 'SEK'},
    {'title': 'KRW'},
    {'title': 'SGD'},
    {'title': 'NOK'},
    {'title': 'MXN'},
    {'title': 'INR'},
    {'title': 'RUB'},
    {'title': 'ZAR'},
    {'title': 'TRY'},
    {'title': 'BRL'},
    {'title': 'TWD'},
    {'title': 'DKK'},
    {'title': 'PLN'},
    {'title': 'THB'},
    {'title': 'IDR'},
    {'title': 'HUF'},
    {'title': 'CZK'},
    {'title': 'ILS'},
    {'title': 'CLP'},
    {'title': 'PHP'},
    {'title': 'AED'},
    {'title': 'COP'},
    {'title': 'SAR'},
    {'title': 'MYR'},
    {'title': 'RON'}
]

firm_size_data = [
    {'title': '2-10'},
    {'title': '11-50'},
    {'title': '51-100'},
    {'title': '101-500'},
    {'title': '501+'},
]


timezone_data = [
    {'title': 'Africa/Abidjan'},
    {'title': 'Africa/Accra'},
    {'title': 'Africa/Addis_Ababa'},
    {'title': 'Africa/Algiers'},
    {'title': 'Africa/Asmara'},
    {'title': 'Africa/Asmera'},
    {'title': 'Africa/Bamako'},
    {'title': 'Africa/Bangui'},
    {'title': 'Africa/Banjul'},
    {'title': 'Africa/Bissau'},
    {'title': 'Africa/Blantyre'},
    {'title': 'Africa/Brazzaville'},
    {'title': 'Africa/Bujumbura'},
    {'title': 'Africa/Cairo'},
    {'title': 'Africa/Casablanca'},
    {'title': 'Africa/Ceuta'},
    {'title': 'Africa/Conakry'},
    {'title': 'Africa/Dakar'},
    {'title': 'Africa/Dar_es_Salaam'},
    {'title': 'Africa/Djibouti'},
    {'title': 'Africa/Douala'},
    {'title': 'Africa/El_Aaiun'},
    {'title': 'Africa/Freetown'},
    {'title': 'Africa/Gaborone'},
    {'title': 'Africa/Harare'},
    {'title': 'Africa/Johannesburg'},
    {'title': 'Africa/Juba'},
    {'title': 'Africa/Kampala'},
    {'title': 'Africa/Khartoum'},
    {'title': 'Africa/Kigali'},
    {'title': 'Africa/Kinshasa'},
    {'title': 'Africa/Lagos'},
    {'title': 'Africa/Libreville'},
    {'title': 'Africa/Lome'},
    {'title': 'Africa/Luanda'},
    {'title': 'Africa/Lubumbashi'},
    {'title': 'Africa/Lusaka'},
    {'title': 'Africa/Malabo'},
    {'title': 'Africa/Maputo'},
    {'title': 'Africa/Maseru'},
    {'title': 'Africa/Mbabane'},
    {'title': 'Africa/Mogadishu'},
    {'title': 'Africa/Monrovia'},
    {'title': 'Africa/Nairobi'},
    {'title': 'Africa/Ndjamena'},
    {'title': 'Africa/Niamey'},
    {'title': 'Africa/Nouakchott'},
    {'title': 'Africa/Ouagadougou'},
    {'title': 'Africa/Porto-Novo'},
    {'title': 'Africa/Sao_Tome'},
    {'title': 'Africa/Timbuktu'},
    {'title': 'Africa/Tripoli'},
    {'title': 'Africa/Tunis'},
    {'title': 'Africa/Windhoek'},
    {'title': 'America/Adak'},
    {'title': 'America/Anchorage'},
    {'title': 'America/Anguilla'},
    {'title': 'America/Antigua'},
    {'title': 'America/Araguaina'},
    {'title': 'America/Argentina/Buenos_Aires'},
    {'title': 'America/Argentina/Catamarca'},
    {'title': 'America/Argentina/ComodRivadavia'},
    {'title': 'America/Argentina/Cordoba'},
    {'title': 'America/Argentina/Jujuy'},
    {'title': 'America/Argentina/La_Rioja'},
    {'title': 'America/Argentina/Mendoza'},
    {'title': 'America/Argentina/Rio_Gallegos'},
    {'title': 'America/Argentina/Salta'},
    {'title': 'America/Argentina/San_Juan'},
    {'title': 'America/Argentina/San_Luis'},
    {'title': 'America/Argentina/Tucuman'},
    {'title': 'America/Argentina/Ushuaia'},
    {'title': 'America/Aruba'},
    {'title': 'America/Asuncion'},
    {'title': 'America/Atikokan'},
    {'title': 'America/Atka'},
    {'title': 'America/Bahia'},
    {'title': 'America/Bahia_Banderas'},
    {'title': 'America/Barbados'},
    {'title': 'America/Belem'},
    {'title': 'America/Belize'},
    {'title': 'America/Blanc-Sablon'},
    {'title': 'America/Boa_Vista'},
    {'title': 'America/Bogota'},
    {'title': 'America/Boise'},
    {'title': 'America/Buenos_Aires'},
    {'title': 'America/Cambridge_Bay'},
    {'title': 'America/Campo_Grande'},
    {'title': 'America/Cancun'},
    {'title': 'America/Caracas'},
    {'title': 'America/Catamarca'},
    {'title': 'America/Cayenne'},
    {'title': 'America/Cayman'},
    {'title': 'America/Chicago'},
    {'title': 'America/Chihuahua'},
    {'title': 'America/Coral_Harbour'},
    {'title': 'America/Cordoba'},
    {'title': 'America/Costa_Rica'},
    {'title': 'America/Creston'},
    {'title': 'America/Cuiaba'},
    {'title': 'America/Curacao'},
    {'title': 'America/Danmarkshavn'},
    {'title': 'America/Dawson'},
    {'title': 'America/Dawson_Creek'},
    {'title': 'America/Denver'},
    {'title': 'America/Detroit'},
    {'title': 'America/Dominica'},
    {'title': 'America/Edmonton'},
    {'title': 'America/Eirunepe'},
    {'title': 'America/El_Salvador'},
    {'title': 'America/Ensenada'},
    {'title': 'America/Fort_Nelson'},
    {'title': 'America/Fort_Wayne'},
    {'title': 'America/Fortaleza'},
    {'title': 'America/Glace_Bay'},
    {'title': 'America/Godthab'},
    {'title': 'America/Goose_Bay'},
    {'title': 'America/Grand_Turk'},
    {'title': 'America/Grenada'},
    {'title': 'America/Guadeloupe'},
    {'title': 'America/Guatemala'},
    {'title': 'America/Guayaquil'},
    {'title': 'America/Guyana'},
    {'title': 'America/Halifax'},
    {'title': 'America/Havana'},
    {'title': 'America/Hermosillo'},
    {'title': 'America/Indiana/Indianapolis'},
    {'title': 'America/Indiana/Knox'},
    {'title': 'America/Indiana/Marengo'},
    {'title': 'America/Indiana/Petersburg'},
    {'title': 'America/Indiana/Tell_City'},
    {'title': 'America/Indiana/Vevay'},
    {'title': 'America/Indiana/Vincennes'},
    {'title': 'America/Indiana/Winamac'},
    {'title': 'America/Indianapolis'},
    {'title': 'America/Inuvik'},
    {'title': 'America/Iqaluit'},
    {'title': 'America/Jamaica'},
    {'title': 'America/Jujuy'},
    {'title': 'America/Juneau'},
    {'title': 'America/Kentucky/Louisville'},
    {'title': 'America/Kentucky/Monticello'},
    {'title': 'America/Knox_IN'},
    {'title': 'America/Kralendijk'},
    {'title': 'America/La_Paz'},
    {'title': 'America/Lima'},
    {'title': 'America/Los_Angeles'},
    {'title': 'America/Louisville'},
    {'title': 'America/Lower_Princes'},
    {'title': 'America/Maceio'},
    {'title': 'America/Managua'},
    {'title': 'America/Manaus'},
    {'title': 'America/Marigot'},
    {'title': 'America/Martinique'},
    {'title': 'America/Matamoros'},
    {'title': 'America/Mazatlan'},
    {'title': 'America/Mendoza'},
    {'title': 'America/Menominee'},
    {'title': 'America/Merida'},
    {'title': 'America/Metlakatla'},
    {'title': 'America/Mexico_City'},
    {'title': 'America/Miquelon'},
    {'title': 'America/Moncton'},
    {'title': 'America/Monterrey'},
    {'title': 'America/Montevideo'},
    {'title': 'America/Montreal'},
    {'title': 'America/Montserrat'},
    {'title': 'America/Nassau'},
    {'title': 'America/New_York'},
    {'title': 'America/Nipigon'},
    {'title': 'America/Nome'},
    {'title': 'America/Noronha'},
    {'title': 'America/North_Dakota/Beulah'},
    {'title': 'America/North_Dakota/Center'},
    {'title': 'America/North_Dakota/New_Salem'},
    {'title': 'America/Nuuk'},
    {'title': 'America/Ojinaga'},
    {'title': 'America/Panama'},
    {'title': 'America/Pangnirtung'},
    {'title': 'America/Paramaribo'},
    {'title': 'America/Phoenix'},
    {'title': 'America/Port-au-Prince'},
    {'title': 'America/Port_of_Spain'},
    {'title': 'America/Porto_Acre'},
    {'title': 'America/Porto_Velho'},
    {'title': 'America/Puerto_Rico'},
    {'title': 'America/Punta_Arenas'},
    {'title': 'America/Rainy_River'},
    {'title': 'America/Rankin_Inlet'},
    {'title': 'America/Recife'},
    {'title': 'America/Regina'},
    {'title': 'America/Resolute'},
    {'title': 'America/Rio_Branco'},
    {'title': 'America/Rosario'},
    {'title': 'America/Santa_Isabel'},
    {'title': 'America/Santarem'},
    {'title': 'America/Santiago'},
    {'title': 'America/Santo_Domingo'},
    {'title': 'America/Sao_Paulo'},
    {'title': 'America/Scoresbysund'},
    {'title': 'America/Shiprock'},
    {'title': 'America/Sitka'},
    {'title': 'America/St_Barthelemy'},
    {'title': 'America/St_Johns'},
    {'title': 'America/St_Kitts'},
    {'title': 'America/St_Lucia'},
    {'title': 'America/St_Thomas'},
    {'title': 'America/St_Vincent'},
    {'title': 'America/Swift_Current'},
    {'title': 'America/Tegucigalpa'},
    {'title': 'America/Thule'},
    {'title': 'America/Thunder_Bay'},
    {'title': 'America/Tijuana'},
    {'title': 'America/Toronto'},
    {'title': 'America/Tortola'},
    {'title': 'America/Vancouver'},
    {'title': 'America/Virgin'},
    {'title': 'America/Whitehorse'},
    {'title': 'America/Winnipeg'},
    {'title': 'America/Yakutat'},
    {'title': 'America/Yellowknife'},
    {'title': 'Antarctica/Casey'},
    {'title': 'Antarctica/Davis'},
    {'title': 'Antarctica/DumontDUrville'},
    {'title': 'Antarctica/Macquarie'},
    {'title': 'Antarctica/Mawson'},
    {'title': 'Antarctica/McMurdo'},
    {'title': 'Antarctica/Palmer'},
    {'title': 'Antarctica/Rothera'},
    {'title': 'Antarctica/South_Pole'},
    {'title': 'Antarctica/Syowa'},
    {'title': 'Antarctica/Troll'},
    {'title': 'Antarctica/Vostok'},
    {'title': 'Arctic/Longyearbyen'},
    {'title': 'Asia/Aden'},
    {'title': 'Asia/Almaty'},
    {'title': 'Asia/Amman'},
    {'title': 'Asia/Anadyr'},
    {'title': 'Asia/Aqtau'},
    {'title': 'Asia/Aqtobe'},
    {'title': 'Asia/Ashgabat'},
    {'title': 'Asia/Ashkhabad'},
    {'title': 'Asia/Atyrau'},
    {'title': 'Asia/Baghdad'},
    {'title': 'Asia/Bahrain'},
    {'title': 'Asia/Baku'},
    {'title': 'Asia/Bangkok'},
    {'title': 'Asia/Barnaul'},
    {'title': 'Asia/Beirut'},
    {'title': 'Asia/Bishkek'},
    {'title': 'Asia/Brunei'},
    {'title': 'Asia/Calcutta'},
    {'title': 'Asia/Chita'},
    {'title': 'Asia/Choibalsan'},
    {'title': 'Asia/Chongqing'},
    {'title': 'Asia/Chungking'},
    {'title': 'Asia/Colombo'},
    {'title': 'Asia/Dacca'},
    {'title': 'Asia/Damascus'},
    {'title': 'Asia/Dhaka'},
    {'title': 'Asia/Dili'},
    {'title': 'Asia/Dubai'},
    {'title': 'Asia/Dushanbe'},
    {'title': 'Asia/Famagusta'},
    {'title': 'Asia/Gaza'},
    {'title': 'Asia/Harbin'},
    {'title': 'Asia/Hebron'},
    {'title': 'Asia/Ho_Chi_Minh'},
    {'title': 'Asia/Hong_Kong'},
    {'title': 'Asia/Hovd'},
    {'title': 'Asia/Irkutsk'},
    {'title': 'Asia/Istanbul'},
    {'title': 'Asia/Jakarta'},
    {'title': 'Asia/Jayapura'},
    {'title': 'Asia/Jerusalem'},
    {'title': 'Asia/Kabul'},
    {'title': 'Asia/Kamchatka'},
    {'title': 'Asia/Karachi'},
    {'title': 'Asia/Kashgar'},
    {'title': 'Asia/Kathmandu'},
    {'title': 'Asia/Katmandu'},
    {'title': 'Asia/Khandyga'},
    {'title': 'Asia/Kolkata'},
    {'title': 'Asia/Krasnoyarsk'},
    {'title': 'Asia/Kuala_Lumpur'},
    {'title': 'Asia/Kuching'},
    {'title': 'Asia/Kuwait'},
    {'title': 'Asia/Macao'},
    {'title': 'Asia/Macau'},
    {'title': 'Asia/Magadan'},
    {'title': 'Asia/Makassar'},
    {'title': 'Asia/Manila'},
    {'title': 'Asia/Muscat'},
    {'title': 'Asia/Nicosia'},
    {'title': 'Asia/Novokuznetsk'},
    {'title': 'Asia/Novosibirsk'},
    {'title': 'Asia/Omsk'},
    {'title': 'Asia/Oral'},
    {'title': 'Asia/Phnom_Penh'},
    {'title': 'Asia/Pontianak'},
    {'title': 'Asia/Pyongyang'},
    {'title': 'Asia/Qatar'},
    {'title': 'Asia/Qostanay'},
    {'title': 'Asia/Qyzylorda'},
    {'title': 'Asia/Rangoon'},
    {'title': 'Asia/Riyadh'},
    {'title': 'Asia/Saigon'},
    {'title': 'Asia/Sakhalin'},
    {'title': 'Asia/Samarkand'},
    {'title': 'Asia/Seoul'},
    {'title': 'Asia/Shanghai'},
    {'title': 'Asia/Singapore'},
    {'title': 'Asia/Srednekolymsk'},
    {'title': 'Asia/Taipei'},
    {'title': 'Asia/Tashkent'},
    {'title': 'Asia/Tbilisi'},
    {'title': 'Asia/Tehran'},
    {'title': 'Asia/Tel_Aviv'},
    {'title': 'Asia/Thimbu'},
    {'title': 'Asia/Thimphu'},
    {'title': 'Asia/Tokyo'},
    {'title': 'Asia/Tomsk'},
    {'title': 'Asia/Ujung_Pandang'},
    {'title': 'Asia/Ulaanbaatar'},
    {'title': 'Asia/Ulan_Bator'},
    {'title': 'Asia/Urumqi'},
    {'title': 'Asia/Ust-Nera'},
    {'title': 'Asia/Vientiane'},
    {'title': 'Asia/Vladivostok'},
    {'title': 'Asia/Yakutsk'},
    {'title': 'Asia/Yangon'},
    {'title': 'Asia/Yekaterinburg'},
    {'title': 'Asia/Yerevan'},
    {'title': 'Atlantic/Azores'},
    {'title': 'Atlantic/Bermuda'},
    {'title': 'Atlantic/Canary'},
    {'title': 'Atlantic/Cape_Verde'},
    {'title': 'Atlantic/Faeroe'},
    {'title': 'Atlantic/Faroe'},
    {'title': 'Atlantic/Jan_Mayen'},
    {'title': 'Atlantic/Madeira'},
    {'title': 'Atlantic/Reykjavik'},
    {'title': 'Atlantic/South_Georgia'},
    {'title': 'Atlantic/St_Helena'},
    {'title': 'Atlantic/Stanley'},
    {'title': 'Australia/ACT'},
    {'title': 'Australia/Adelaide'},
    {'title': 'Australia/Brisbane'},
    {'title': 'Australia/Broken_Hill'},
    {'title': 'Australia/Canberra'},
    {'title': 'Australia/Currie'},
    {'title': 'Australia/Darwin'},
    {'title': 'Australia/Eucla'},
    {'title': 'Australia/Hobart'},
    {'title': 'Australia/LHI'},
    {'title': 'Australia/Lindeman'},
    {'title': 'Australia/Lord_Howe'},
    {'title': 'Australia/Melbourne'},
    {'title': 'Australia/NSW'},
    {'title': 'Australia/North'},
    {'title': 'Australia/Perth'},
    {'title': 'Australia/Queensland'},
    {'title': 'Australia/South'},
    {'title': 'Australia/Sydney'},
    {'title': 'Australia/Tasmania'},
    {'title': 'Australia/Victoria'},
    {'title': 'Australia/West'},
    {'title': 'Australia/Yancowinna'},
    {'title': 'Brazil/Acre'},
    {'title': 'Brazil/DeNoronha'},
    {'title': 'Brazil/East'},
    {'title': 'Brazil/West'},
    {'title': 'CET'},
    {'title': 'CST6CDT'},
    {'title': 'Canada/Atlantic'},
    {'title': 'Canada/Central'},
    {'title': 'Canada/Eastern'},
    {'title': 'Canada/Mountain'},
    {'title': 'Canada/Newfoundland'},
    {'title': 'Canada/Pacific'},
    {'title': 'Canada/Saskatchewan'},
    {'title': 'Canada/Yukon'},
    {'title': 'Chile/Continental'},
    {'title': 'Chile/EasterIsland'},
    {'title': 'Cuba'},
    {'title': 'EET'},
    {'title': 'EST'},
    {'title': 'EST5EDT'},
    {'title': 'Egypt'},
    {'title': 'Eire'},
    {'title': 'Etc/GMT'},
    {'title': 'Etc/GMT+0'},
    {'title': 'Etc/GMT+1'},
    {'title': 'Etc/GMT+10'},
    {'title': 'Etc/GMT+11'},
    {'title': 'Etc/GMT+12'},
    {'title': 'Etc/GMT+2'},
    {'title': 'Etc/GMT+3'},
    {'title': 'Etc/GMT+4'},
    {'title': 'Etc/GMT+5'},
    {'title': 'Etc/GMT+6'},
    {'title': 'Etc/GMT+7'},
    {'title': 'Etc/GMT+8'},
    {'title': 'Etc/GMT+9'},
    {'title': 'Etc/GMT-0'},
    {'title': 'Etc/GMT-1'},
    {'title': 'Etc/GMT-10'},
    {'title': 'Etc/GMT-11'},
    {'title': 'Etc/GMT-12'},
    {'title': 'Etc/GMT-13'},
    {'title': 'Etc/GMT-14'},
    {'title': 'Etc/GMT-2'},
    {'title': 'Etc/GMT-3'},
    {'title': 'Etc/GMT-4'},
    {'title': 'Etc/GMT-5'},
    {'title': 'Etc/GMT-6'},
    {'title': 'Etc/GMT-7'},
    {'title': 'Etc/GMT-8'},
    {'title': 'Etc/GMT-9'},
    {'title': 'Etc/GMT0'},
    {'title': 'Etc/Greenwich'},
    {'title': 'Etc/UCT'},
    {'title': 'Etc/UTC'},
    {'title': 'Etc/Universal'},
    {'title': 'Etc/Zulu'},
    {'title': 'Europe/Amsterdam'},
    {'title': 'Europe/Andorra'},
    {'title': 'Europe/Astrakhan'},
    {'title': 'Europe/Athens'},
    {'title': 'Europe/Belfast'},
    {'title': 'Europe/Belgrade'},
    {'title': 'Europe/Berlin'},
    {'title': 'Europe/Bratislava'},
    {'title': 'Europe/Brussels'},
    {'title': 'Europe/Bucharest'},
    {'title': 'Europe/Budapest'},
    {'title': 'Europe/Busingen'},
    {'title': 'Europe/Chisinau'},
    {'title': 'Europe/Copenhagen'},
    {'title': 'Europe/Dublin'},
    {'title': 'Europe/Gibraltar'},
    {'title': 'Europe/Guernsey'},
    {'title': 'Europe/Helsinki'},
    {'title': 'Europe/Isle_of_Man'},
    {'title': 'Europe/Istanbul'},
    {'title': 'Europe/Jersey'},
    {'title': 'Europe/Kaliningrad'},
    {'title': 'Europe/Kiev'},
    {'title': 'Europe/Kirov'},
    {'title': 'Europe/Lisbon'},
    {'title': 'Europe/Ljubljana'},
    {'title': 'Europe/London'},
    {'title': 'Europe/Luxembourg'},
    {'title': 'Europe/Madrid'},
    {'title': 'Europe/Malta'},
    {'title': 'Europe/Mariehamn'},
    {'title': 'Europe/Minsk'},
    {'title': 'Europe/Monaco'},
    {'title': 'Europe/Moscow'},
    {'title': 'Europe/Nicosia'},
    {'title': 'Europe/Oslo'},
    {'title': 'Europe/Paris'},
    {'title': 'Europe/Podgorica'},
    {'title': 'Europe/Prague'},
    {'title': 'Europe/Riga'},
    {'title': 'Europe/Rome'},
    {'title': 'Europe/Samara'},
    {'title': 'Europe/San_Marino'},
    {'title': 'Europe/Sarajevo'},
    {'title': 'Europe/Saratov'},
    {'title': 'Europe/Simferopol'},
    {'title': 'Europe/Skopje'},
    {'title': 'Europe/Sofia'},
    {'title': 'Europe/Stockholm'},
    {'title': 'Europe/Tallinn'},
    {'title': 'Europe/Tirane'},
    {'title': 'Europe/Tiraspol'},
    {'title': 'Europe/Ulyanovsk'},
    {'title': 'Europe/Uzhgorod'},
    {'title': 'Europe/Vaduz'},
    {'title': 'Europe/Vatican'},
    {'title': 'Europe/Vienna'},
    {'title': 'Europe/Vilnius'},
    {'title': 'Europe/Volgograd'},
    {'title': 'Europe/Warsaw'},
    {'title': 'Europe/Zagreb'},
    {'title': 'Europe/Zaporozhye'},
    {'title': 'Europe/Zurich'},
    {'title': 'GB'},
    {'title': 'GB-Eire'},
    {'title': 'GMT'},
    {'title': 'GMT+0'},
    {'title': 'GMT-0'},
    {'title': 'GMT0'},
    {'title': 'Greenwich'},
    {'title': 'HST'},
    {'title': 'Hongkong'},
    {'title': 'Iceland'},
    {'title': 'Indian/Antananarivo'},
    {'title': 'Indian/Chagos'},
    {'title': 'Indian/Christmas'},
    {'title': 'Indian/Cocos'},
    {'title': 'Indian/Comoro'},
    {'title': 'Indian/Kerguelen'},
    {'title': 'Indian/Mahe'},
    {'title': 'Indian/Maldives'},
    {'title': 'Indian/Mauritius'},
    {'title': 'Indian/Mayotte'},
    {'title': 'Indian/Reunion'},
    {'title': 'Iran'},
    {'title': 'Israel'},
    {'title': 'Jamaica'},
    {'title': 'Japan'},
    {'title': 'Kwajalein'},
    {'title': 'Libya'},
    {'title': 'MET'},
    {'title': 'MST'},
    {'title': 'MST7MDT'},
    {'title': 'Mexico/BajaNorte'},
    {'title': 'Mexico/BajaSur'},
    {'title': 'Mexico/General'},
    {'title': 'NZ'},
    {'title': 'NZ-CHAT'},
    {'title': 'Navajo'},
    {'title': 'PRC'},
    {'title': 'PST8PDT'},
    {'title': 'Pacific/Apia'},
    {'title': 'Pacific/Auckland'},
    {'title': 'Pacific/Bougainville'},
    {'title': 'Pacific/Chatham'},
    {'title': 'Pacific/Chuuk'},
    {'title': 'Pacific/Easter'},
    {'title': 'Pacific/Efate'},
    {'title': 'Pacific/Enderbury'},
    {'title': 'Pacific/Fakaofo'},
    {'title': 'Pacific/Fiji'},
    {'title': 'Pacific/Funafuti'},
    {'title': 'Pacific/Galapagos'},
    {'title': 'Pacific/Gambier'},
    {'title': 'Pacific/Guadalcanal'},
    {'title': 'Pacific/Guam'},
    {'title': 'Pacific/Honolulu'},
    {'title': 'Pacific/Johnston'},
    {'title': 'Pacific/Kiritimati'},
    {'title': 'Pacific/Kosrae'},
    {'title': 'Pacific/Kwajalein'},
    {'title': 'Pacific/Majuro'},
    {'title': 'Pacific/Marquesas'},
    {'title': 'Pacific/Midway'},
    {'title': 'Pacific/Nauru'},
    {'title': 'Pacific/Niue'},
    {'title': 'Pacific/Norfolk'},
    {'title': 'Pacific/Noumea'},
    {'title': 'Pacific/Pago_Pago'},
    {'title': 'Pacific/Palau'},
    {'title': 'Pacific/Pitcairn'},
    {'title': 'Pacific/Pohnpei'},
    {'title': 'Pacific/Ponape'},
    {'title': 'Pacific/Port_Moresby'},
    {'title': 'Pacific/Rarotonga'},
    {'title': 'Pacific/Saipan'},
    {'title': 'Pacific/Samoa'},
    {'title': 'Pacific/Tahiti'},
    {'title': 'Pacific/Tarawa'},
    {'title': 'Pacific/Tongatapu'},
    {'title': 'Pacific/Truk'},
    {'title': 'Pacific/Wake'},
    {'title': 'Pacific/Wallis'},
    {'title': 'Pacific/Yap'},
    {'title': 'Poland'},
    {'title': 'Portugal'},
    {'title': 'ROC'},
    {'title': 'ROK'},
    {'title': 'Singapore'},
    {'title': 'Turkey'},
    {'title': 'UCT'},
    {'title': 'US/Alaska'},
    {'title': 'US/Aleutian'},
    {'title': 'US/Arizona'},
    {'title': 'US/Central'},
    {'title': 'US/East-Indiana'},
    {'title': 'US/Eastern'},
    {'title': 'US/Hawaii'},
    {'title': 'US/Indiana-Starke'},
    {'title': 'US/Michigan'},
    {'title': 'US/Mountain'},
    {'title': 'US/Pacific'},
    {'title': 'US/Samoa'},
    {'title': 'UTC'},
    {'title': 'Universal'},
    {'title': 'W-SU'},
    {'title': 'WET'},
    {'title': 'Zulu'}
]


payment_method_data = [
    {'title': 'Direct Debit(ACH/eCheck)'},
    {'title': 'Credit Cards'},
]


class Command(BaseCommand):
    """Set up specialities, categories and fee_types."""

    def handle(self, *args, **options):
        """Run set up."""
        self.stdout.write('Setting up Specialities')
        Speciality.objects.bulk_create(
            Speciality(**speciality_data) for speciality_data in
            specialities_data
        )

        self.stdout.write('Setting up Forum-Topics')
        Topic.objects.bulk_create(
            Topic(
                practice_area=ForumPracticeAreas.objects.get(
                    title=category_data['title']
                ),
                **category_data
            ) for category_data in categories_data
        )

        self.stdout.write('Setting up FeeKinds')
        FeeKind.objects.bulk_create(
            FeeKind(**fee_kind_data) for fee_kind_data in fee_kinds_data
        )

        self.stdout.write('Setting up Appointment Types')
        AppointmentType.objects.bulk_create(
            AppointmentType(**obj) for obj in appointment_type_data
        )

        self.stdout.write('Setting up Payment Types')
        PaymentType.objects.bulk_create(
            PaymentType(**obj) for obj in payment_type_data
        )

        self.stdout.write('Setting up Payment Methods')
        PaymentMethods.objects.bulk_create(
            PaymentMethods(**obj) for obj in payment_method_data
        )

        self.stdout.write('Setting up languages')
        Language.objects.bulk_create(
            Language(**obj) for obj in language_data
        )

        self.stdout.write('Setting up currencies')
        Currencies.objects.bulk_create(
            Currencies(**obj) for obj in currencies_data
        )

        self.stdout.write('Setting up firm size')
        FirmSize.objects.bulk_create(
            FirmSize(**obj) for obj in firm_size_data
        )

        self.stdout.write('Setting up timezone')
        TimeZone.objects.bulk_create(
            TimeZone(**obj) for obj in timezone_data
        )

        self.stdout.write('Setting up done')
