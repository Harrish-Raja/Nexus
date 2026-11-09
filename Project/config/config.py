ORGANISATION_NAME = "Merrowfield Digital"

HUB_CODE_BY_HUB = {
    "Bengaluru": "BLR",
    "Lisbon": "LIS",
    "Warsaw": "WAW",
    "Tallinn": "TLL",
}

HUB_TIME_ZONE_BY_HUB = {
    "Bengaluru": "Asia/Kolkata",
    "Lisbon": "Europe/Lisbon",
    "Warsaw": "Europe/Warsaw",
    "Tallinn": "Europe/Tallinn",
}


DOCS_DIRECTORY = "data/docs"
DATABASE_DIRECTORY = "database"


RAW_INCIDENTS_TRAIN_FILE = "data/security_incidents_train.csv"
RAW_INCIDENTS_EVAL_FILE = "data/security_incidents_eval.csv"
RAW_EFFORT_TRAIN_FILE = "data/containment_effort_train.csv"
RAW_EFFORT_EVAL_FILE = "data/containment_effort_eval.csv"
RAW_INCIDENT_NOTES_FILE = "data/analyst_incident_notes.csv"
OPEN_INCIDENTS_FILE = "data/input/open_incidents.csv"
OPEN_INCIDENT_NOTES_FILE = "data/input/open_incident_notes.csv"


CLEAN_INCIDENTS_TRAIN_FILE = "processed/security_incidents_train_clean.csv"
CLEAN_INCIDENTS_EVAL_FILE = "processed/security_incidents_eval_clean.csv"
CLEAN_EFFORT_TRAIN_FILE = "processed/containment_effort_train_clean.csv"
CLEAN_EFFORT_EVAL_FILE = "processed/containment_effort_eval_clean.csv"
CLEAN_INCIDENT_NOTES_FILE = "processed/analyst_incident_notes_clean.csv"


HARM_MODEL_FILE = "output/models/harm_model.pkl"
EFFORT_MODEL_FILE = "output/models/effort_model.pkl"
ATTACK_MODEL_FILE = "output/models/attack_model.pkl"
HARM_SCHEMA_FILE = "output/models/harm_features.json"
EFFORT_SCHEMA_FILE = "output/models/effort_features.json"
MODEL_METRICS_FILE = "output/model_metrics.json"
DATA_QUALITY_REPORT_FILE = "output/data_quality_report.json"


APPLICATION_DATABASE_FILE = "database/breachwatch.db"
APPLICATION_DATABASE_URL = "sqlite:///./" + APPLICATION_DATABASE_FILE
CHECKPOINT_DATABASE_FILE = "database/checkpoint.db"
VECTOR_STORE_DIRECTORY = "database/chroma_store"
VECTOR_COLLECTION_NAME = "incident_response_documents"


RANDOM_SEED = 42
VALIDATION_SPLIT_RATIO = 0.2


NULL_TOKEN_LIST = ["", " ", "NA", "N/A", "n/a", "NULL", "null", "none", "None",
                   "NaN", "nan", "-", "?", "Not recorded"]


UNKNOWN_CATEGORY_VALUE = "Unknown"

BOOLEAN_TRUE_TOKENS = ["yes", "y", "true", "t", "1"]
BOOLEAN_FALSE_TOKENS = ["no", "n", "false", "f", "0"]
BOOLEAN_YES = "Yes"
BOOLEAN_NO = "No"


TIMESTAMP_FORMAT_LIST = ["%Y-%m-%dT%H:%M:%S%z", "%d/%m/%Y %H:%M %z", "%d-%b-%Y %H:%M %z"]
EPOCH_SECONDS_PATTERN = r"^\d{9,10}$"
ZONE_ABBREVIATION_PATTERN = r"\s([A-Z]{3,4})$"
UTC_OFFSET_SUFFIX_PATTERN = r"[+-]\d{2}:\d{2}$"
ISO_UTC_SUFFIX = "Z"

TIMEZONE_ABBREVIATION_OFFSETS = {
    "UTC": "+00:00",
    "GMT": "+00:00",
    "WET": "+00:00",
    "WEST": "+01:00",
    "CET": "+01:00",
    "CEST": "+02:00",
    "EET": "+02:00",
    "EEST": "+03:00",
    "IST": "+05:30",
}

OUTPUT_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DISPLAY_TIMESTAMP_FORMAT = "%d %b %Y %H:%M"

DATE_FORMAT_LIST = ["%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y"]
OUTPUT_DATE_FORMAT = "%Y-%m-%d"


COUNT_SUFFIX_MULTIPLIERS = {
    "lakh": 100000,
    "k": 1000,
}
DIGIT_GROUPING_SEPARATOR = ","
CURRENCY_MARKERS = ["€", "EUR"]


HOURS_AND_MINUTES_PATTERN = r"^(\d+)\s*h\s+(\d+)\s*m$"
MINUTES_UNIT_PATTERN = r"^(\d+(?:\.\d+)?)\s*min$"
HOURS_UNIT_PATTERN = r"^(\d+(?:\.\d+)?)\s*h$"


ENCODING_ARTIFACT_LIST = ["&nbsp;", "&amp;", "&lt;", "&gt;", "&quot;", "&#39;", "\xa0"]

MARKUP_PATTERN = r"<[^>]+>"
WHITESPACE_RUN_PATTERN = r"\s+"


INCIDENT_TARGET_COLUMN = "high_risk_to_individuals"


INCIDENT_IDENTIFIER_COLUMNS = [
    "incident_id", "incident_reference", "campaign_reference",
    "first_alert_at", "triage_started_at", "confirmed_at",
]

INCIDENT_TIMESTAMP_COLUMNS = ["first_alert_at", "triage_started_at", "confirmed_at"]

FIRST_ALERT_COLUMN = "first_alert_at"
AWARENESS_COLUMN = "confirmed_at"
INCIDENT_INTERVAL_COLUMN = "detection_to_confirmation_minutes"

INCIDENT_BOOLEAN_COLUMNS = [
    "internet_facing_flag", "personal_data_involved_flag", "contact_details_flag",
    "account_credentials_flag", "government_id_flag", "payment_token_flag",
    "health_data_flag", "child_accounts_flag", "mfa_enforced_flag",
    "exfiltration_confirmed_flag", "attacker_still_active_flag",
    "third_party_supplier_involved_flag", "backups_available_flag",
]

INCIDENT_CATEGORY_COLUMNS = [
    "soc_hub", "detection_source", "initial_severity", "affected_system_class",
    "hosting_region", "attack_vector", "data_protection_state", "ticket_queue_code",
    "weekday_detected", "analyst_shift_code",
]

INCIDENT_COUNT_COLUMNS = [
    "eu_data_subjects_count", "india_data_subjects_count", "customers_affected_count",
    "records_affected_count",
]

INCIDENT_DURATION_MINUTES_COLUMNS = ["service_outage_minutes"]

INCIDENT_MONEY_COLUMNS = ["direct_financial_loss_eur"]

INCIDENT_NUMERIC_COLUMNS = [
    "detection_to_confirmation_minutes", "systems_affected_count",
    "eu_data_subjects_count", "india_data_subjects_count", "customers_affected_count",
    "records_affected_count", "service_outage_minutes", "direct_financial_loss_eur",
    "data_subject_countries_count", "prior_incidents_on_system_12m",
    "days_since_last_incident_on_system", "linked_incidents_in_campaign",
    "exploited_weakness_age_days", "log_retention_days",
]


INCIDENT_RANGE_LIMITS = {
    "detection_to_confirmation_minutes": (0.0, 60000.0),
    "systems_affected_count": (1.0, 400.0),
    "eu_data_subjects_count": (0.0, 25000000.0),
    "india_data_subjects_count": (0.0, 25000000.0),
    "customers_affected_count": (0.0, 25000000.0),
    "records_affected_count": (0.0, 25000000.0),
    "service_outage_minutes": (0.0, 20000.0),
    "direct_financial_loss_eur": (0.0, 25000000.0),
    "data_subject_countries_count": (0.0, 28.0),
    "prior_incidents_on_system_12m": (0.0, 50.0),
    "days_since_last_incident_on_system": (0.0, 3650.0),
    "linked_incidents_in_campaign": (0.0, 50.0),
    "exploited_weakness_age_days": (0.0, 3650.0),
    "log_retention_days": (1.0, 3650.0),
}


EFFORT_TARGET_COLUMN = "containment_hours"

EFFORT_IDENTIFIER_COLUMNS = [
    "effort_record_id", "incident_reference", "analyst_id", "containment_started_on",
]

EFFORT_DATE_COLUMNS = ["containment_started_on"]

EFFORT_DURATION_HOURS_COLUMNS = ["containment_hours"]

EFFORT_BOOLEAN_COLUMNS = [
    "forensic_image_required_flag", "third_party_supplier_involved_flag",
    "cloud_provider_support_case_flag", "legal_hold_required_flag",
    "sensitive_data_review_flag", "attacker_still_active_flag",
    "log_coverage_incomplete_flag", "out_of_hours_start_flag",
]

EFFORT_CATEGORY_COLUMNS = [
    "soc_hub", "attack_type", "harm_band", "initial_severity", "analyst_grade",
    "weekday_started", "ticket_queue_code",
]

EFFORT_NUMERIC_COLUMNS = [
    "systems_affected_count", "endpoints_affected_count", "log_sources_to_review",
    "records_affected_count", "data_categories_affected_count", "regions_affected_count",
    "forensic_images_taken_count", "analyst_open_incident_count", "containment_hours",
]

EFFORT_RANGE_LIMITS = {
    "systems_affected_count": (1.0, 400.0),
    "endpoints_affected_count": (0.0, 2000.0),
    "log_sources_to_review": (1.0, 60.0),
    "records_affected_count": (0.0, 25000000.0),
    "data_categories_affected_count": (0.0, 6.0),
    "regions_affected_count": (1.0, 2.0),
    "forensic_images_taken_count": (0.0, 50.0),
    "analyst_open_incident_count": (0.0, 40.0),
    "containment_hours": (0.25, 200.0),
}

FORENSIC_IMAGE_FLAG_COLUMN = "forensic_image_required_flag"
FORENSIC_IMAGE_COUNT_COLUMN = "forensic_images_taken_count"


NOTE_TEXT_COLUMN = "note_text"
NOTE_TARGET_COLUMN = "attack_type"
NOTE_LENGTH_COLUMN = "note_length_chars"
NOTE_TIMESTAMP_COLUMNS = ["note_written_at"]
NOTE_CATEGORY_COLUMNS = ["soc_hub", "affected_system_class", "note_source", "analyst_grade",
                         "initial_severity"]
NOTE_NUMERIC_COLUMNS = ["note_sequence", "note_length_chars"]

NOTE_RANGE_LIMITS = {
    "note_sequence": (1.0, 20.0),
    "note_length_chars": (1.0, 4000.0),
}

MINIMUM_NOTE_WORDS = 6


VALID_HUBS = ["Bengaluru", "Lisbon", "Tallinn", "Warsaw"]

VALID_DETECTION_SOURCES = [
    "Endpoint alert", "SIEM correlation rule", "User report", "Third-party notification",
    "Threat intelligence feed", "Cloud security alert", "Data loss prevention alert",
]

VALID_SEVERITIES = ["P1", "P2", "P3", "P4"]

VALID_SYSTEM_CLASSES = [
    "Customer identity service", "Seller portal", "Order management database",
    "Payment token vault", "Customer support platform", "Analytics data warehouse",
    "Corporate email", "Backup storage", "Public website", "Mobile app backend",
    "Employee workstation",
]

VALID_HOSTING_REGIONS = ["EU", "India", "EU and India"]

VALID_ATTACK_VECTORS = [
    "Email", "Web application", "Endpoint", "Cloud console", "Physical", "Network",
    "Third-party supplier", "Insider access",
]

VALID_PROTECTION_STATES = [
    "Plaintext", "Encrypted", "Encrypted key compromised", "Pseudonymised",
    "Hashed and salted", "Not applicable",
]

VALID_ANALYST_GRADES = ["Analyst I", "Analyst II", "Senior Analyst", "Lead Analyst"]

VALID_NOTE_SOURCES = ["Initial triage", "Investigation update", "Containment update",
                      "Handover note", "Closure summary"]

VALID_TICKET_QUEUES = ["SOC-Q1", "SOC-Q2", "SOC-Q3", "SOC-Q4", "SOC-Q5", "SOC-Q6",
                       "SOC-Q7", "SOC-Q8", "SOC-Q9"]

VALID_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
                  "Sunday"]

VALID_SHIFT_CODES = ["SHIFT-D", "SHIFT-E", "SHIFT-N"]



VALID_ATTACK_TYPES = [
    "Phishing and credential compromise",
    "Ransomware",
    "Other malware",
    "Misdirected disclosure",
    "Lost or stolen device",
    "Insider misuse",
    "Cloud misconfiguration",
    "Denial of service",
]


HUB_MAPPING = {
    "bengaluru": "Bengaluru",
    "bangalore": "Bengaluru",
    "blr": "Bengaluru",
    "lisbon": "Lisbon",
    "lisboa": "Lisbon",
    "lis": "Lisbon",
    "warsaw": "Warsaw",
    "warszawa": "Warsaw",
    "waw": "Warsaw",
    "tallinn": "Tallinn",
    "tallin": "Tallinn",
    "tll": "Tallinn",
}

HOSTING_REGION_MAPPING = {
    "eu": "EU",
    "e.u.": "EU",
    "european union": "EU",
    "india": "India",
    "in": "India",
    "eu and india": "EU and India",
    "eu & india": "EU and India",
    "eu+india": "EU and India",
    "eu/india": "EU and India",
}

PROTECTION_STATE_MAPPING = {
    "plaintext": "Plaintext",
    "unencrypted": "Plaintext",
    "encrypted": "Encrypted",
    "encrypted at rest": "Encrypted",
    "encrypted key compromised": "Encrypted key compromised",
    "encrypted (key compromised)": "Encrypted key compromised",
    "encrypted - key compromised": "Encrypted key compromised",
    "pseudonymised": "Pseudonymised",
    "pseudonymized": "Pseudonymised",
    "hashed and salted": "Hashed and salted",
    "hashed & salted": "Hashed and salted",
    "not applicable": "Not applicable",
    "n/a - no personal data": "Not applicable",
}

ATTACK_TYPE_MAPPING = {
    "phishing and credential compromise": "Phishing and credential compromise",
    "phishing & credential compromise": "Phishing and credential compromise",
    "phishing": "Phishing and credential compromise",
    "credential phishing": "Phishing and credential compromise",
    "credential compromise": "Phishing and credential compromise",
    "ransomware": "Ransomware",
    "ransomware attack": "Ransomware",
    "other malware": "Other malware",
    "malware": "Other malware",
    "malware (other)": "Other malware",
    "misdirected disclosure": "Misdirected disclosure",
    "misdirected email": "Misdirected disclosure",
    "disclosure in error": "Misdirected disclosure",
    "lost or stolen device": "Lost or stolen device",
    "lost device": "Lost or stolen device",
    "stolen device": "Lost or stolen device",
    "lost/stolen device": "Lost or stolen device",
    "insider misuse": "Insider misuse",
    "insider threat": "Insider misuse",
    "insider data misuse": "Insider misuse",
    "cloud misconfiguration": "Cloud misconfiguration",
    "cloud misconfig": "Cloud misconfiguration",
    "misconfigured cloud storage": "Cloud misconfiguration",
    "denial of service": "Denial of service",
    "denial-of-service": "Denial of service",
    "denial of service attack": "Denial of service",
    "dos": "Denial of service",
    "ddos": "Denial of service",
}

ANALYST_GRADE_MAPPING = {
    "analyst i": "Analyst I",
    "analyst 1": "Analyst I",
    "l1 analyst": "Analyst I",
    "analyst ii": "Analyst II",
    "analyst 2": "Analyst II",
    "l2 analyst": "Analyst II",
    "senior analyst": "Senior Analyst",
    "sr analyst": "Senior Analyst",
    "lead analyst": "Lead Analyst",
    "team lead analyst": "Lead Analyst",
    "lead": "Lead Analyst",
}

SYSTEM_CLASS_MAPPING = {value.lower(): value for value in VALID_SYSTEM_CLASSES}
DETECTION_SOURCE_MAPPING = {value.lower(): value for value in VALID_DETECTION_SOURCES}
ATTACK_VECTOR_MAPPING = {value.lower(): value for value in VALID_ATTACK_VECTORS}


HARM_BAND_HIGH = "HIGH"
HARM_BAND_MEDIUM = "MEDIUM"
HARM_BAND_LOW = "LOW"
HARM_BAND_OPTIONS = [HARM_BAND_HIGH, HARM_BAND_MEDIUM, HARM_BAND_LOW]
HARM_BAND_ALL = "ALL"

HARM_BAND_MAPPING = {band.lower(): band for band in HARM_BAND_OPTIONS}


HARM_BAND_HIGH_THRESHOLD = 0.60
HARM_BAND_MEDIUM_THRESHOLD = 0.30


MINIMUM_HARM_ROC_AUC = 0.75
MINIMUM_EFFORT_R2 = 0.55
MINIMUM_ATTACK_MACRO_F1 = 0.75


DATA_CATEGORY_FLAG_COLUMNS = [
    "contact_details_flag", "account_credentials_flag", "government_id_flag",
    "payment_token_flag", "health_data_flag", "child_accounts_flag",
]

HIGH_IMPACT_DATA_FLAG_COLUMNS = [
    "account_credentials_flag", "government_id_flag", "payment_token_flag",
    "health_data_flag", "child_accounts_flag",
]

SENSITIVE_DATA_FLAG_COLUMNS = ["government_id_flag", "health_data_flag", "child_accounts_flag"]

DATA_CATEGORY_LABELS = {
    "contact_details_flag": "contact details",
    "account_credentials_flag": "account credentials",
    "government_id_flag": "government ID",
    "payment_token_flag": "payment tokens",
    "health_data_flag": "health-related data",
    "child_accounts_flag": "children's accounts",
}

REGIONS_AFFECTED_BY_HOSTING_REGION = {
    "EU": 1,
    "India": 1,
    "EU and India": 2,
}


CAMPAIGN_COLUMN = "campaign_reference"
NO_CAMPAIGN_VALUE = "Not linked"
CAMPAIGN_INCIDENT_COLUMNS = ["incident_reference", "soc_hub", "affected_system_class",
                             "attack_vector", "customers_affected_count"]


PROCEDURE_EU_PERSONAL_DATA_BREACH = "Procedure 01"
PROCEDURE_SIGNIFICANT_INCIDENT = "Procedure 02"
PROCEDURE_INDIA_CYBER_INCIDENT = "Procedure 03"
PROCEDURE_OPTIONS = [PROCEDURE_EU_PERSONAL_DATA_BREACH, PROCEDURE_SIGNIFICANT_INCIDENT,
                     PROCEDURE_INDIA_CYBER_INCIDENT]

PROCEDURE_DOCUMENT_BY_CODE = {
    PROCEDURE_EU_PERSONAL_DATA_BREACH: "Procedure-01-EU-Personal-Data-Breach.pdf",
    PROCEDURE_SIGNIFICANT_INCIDENT: "Procedure-02-Significant-Incident-Reporting.pdf",
    PROCEDURE_INDIA_CYBER_INCIDENT: "Procedure-03-India-Cyber-Incident-Reporting.pdf",
}

PROCEDURE_TITLE_BY_CODE = {
    PROCEDURE_EU_PERSONAL_DATA_BREACH: "EU personal data breach",
    PROCEDURE_SIGNIFICANT_INCIDENT: "Significant incident",
    PROCEDURE_INDIA_CYBER_INCIDENT: "India cyber incident",
}

PROCEDURE_AUTHORITY_BY_CODE = {
    PROCEDURE_EU_PERSONAL_DATA_BREACH: "Lead supervisory authority",
    PROCEDURE_SIGNIFICANT_INCIDENT: "National CSIRT",
    PROCEDURE_INDIA_CYBER_INCIDENT: "CERT-In",
}


EU_PROCEDURE_HARM_BANDS = [HARM_BAND_HIGH, HARM_BAND_MEDIUM]
EU_DATA_SUBJECTS_COLUMN = "eu_data_subjects_count"

SIGNIFICANT_OUTAGE_MINUTES = 60
SIGNIFICANT_CUSTOMERS_ACROSS_CAMPAIGN = 100000
SIGNIFICANT_DIRECT_LOSS_EUR = 500000

INDIA_HOSTING_REGIONS = ["India", "EU and India"]
INDIA_DATA_SUBJECTS_COLUMN = "india_data_subjects_count"

CUSTOMER_NOTICE_HARM_BANDS = [HARM_BAND_HIGH]


SNAPSHOT_AT_UTC = "2026-03-14T01:40:00Z"

CLOCK_START_COLUMN_BY_PHRASE = {
    "awareness": AWARENESS_COLUMN,
    "the first alert": FIRST_ALERT_COLUMN,
}

FILING_RESERVE_HOURS = 0.5


DEADLINE_QUESTION_TEMPLATE = "%s: which reports are due, within how many hours, counted from which moment"
EXEMPTION_QUESTION_TEMPLATE = "%s: when must customers be told, and which data protection excuses telling them"
PROCEDURE_RESULT_COUNT = 3

MILESTONE_STATEMENT_PATTERN = r"The ([a-z][A-Za-z -]*?) is due within (\d+) hours of (awareness|the first alert)\."
FILED_MILESTONE_STATEMENT_PATTERN = r"The ([a-z][A-Za-z -]*?) is due (one|two|three) months? after the ([a-z][A-Za-z -]*?) is filed\."
EXEMPTION_STATEMENT_PATTERN = r"Customers need not be told where the data protection state is ([A-Z][A-Za-z ]*?)\."

MONTHS_BY_WORD = {
    "one": 1,
    "two": 2,
    "three": 3,
}


INCIDENT_NOT_IN_QUEUE_MESSAGE = "%s is not in the incident queue"
INCIDENT_WITHOUT_NOTES_MESSAGE = "%s has no analyst notes to read"
PROCEDURE_UNREAD_MESSAGE = "%s did not state %s in a form that could be read"
NO_PROCEDURE_APPLIES_MESSAGE = "No reporting procedure applies to this incident"
DEADLINE_BREACH_MESSAGE = "The estimated effort does not fit in the hours left before the earliest deadline"
DEADLINE_OVERDUE_MESSAGE = "The earliest deadline has already passed"
CLOCK_NOT_STARTED_MESSAGE = "Not started - the incident is awaiting confirmation"
CAMPAIGN_SIGNIFICANCE_MESSAGE = "Significant only when its campaign is counted"


SENSITIVE_DATA_EFFORT_MULTIPLIER = 1.5
EFFORT_MODEL_BASELINES = {
    "sensitive_data_review_flag": BOOLEAN_NO,
}


CONTAINMENT_PLANNING_ASSUMPTIONS = {
    "endpoints_affected_count": 1,
    "log_sources_to_review": 5,
    "forensic_image_required_flag": BOOLEAN_NO,
    "forensic_images_taken_count": 0,
    "cloud_provider_support_case_flag": BOOLEAN_NO,
    "legal_hold_required_flag": BOOLEAN_NO,
    "log_coverage_incomplete_flag": BOOLEAN_NO,
    "analyst_grade": "Senior Analyst",
    "analyst_open_incident_count": 4,
}

WORKING_HOURS_START_HOUR = 8
WORKING_HOURS_END_HOUR = 18
WEEKEND_DAYS = ["Saturday", "Sunday"]


PLAYBOOK_DOCUMENT_BY_ATTACK_TYPE = {
    "Phishing and credential compromise": "Playbook-Phishing-And-Credential-Compromise.pdf",
    "Ransomware": "Playbook-Ransomware.pdf",
    "Other malware": "Playbook-Other-Malware.pdf",
    "Misdirected disclosure": "Playbook-Misdirected-Disclosure.pdf",
    "Lost or stolen device": "Playbook-Lost-Or-Stolen-Device.pdf",
    "Insider misuse": "Playbook-Insider-Misuse.pdf",
    "Cloud misconfiguration": "Playbook-Cloud-Misconfiguration.pdf",
    "Denial of service": "Playbook-Denial-Of-Service.pdf",
}

CUSTOMER_STEPS_QUESTION_TEMPLATE = "%s: what should affected customers do now"
PLAYBOOK_RESULT_COUNT = 3


AGENT_RUN_STATUS_RUNNING = "RUNNING"
AGENT_RUN_STATUS_AWAITING_DECISION = "AWAITING_DECISION"
AGENT_RUN_STATUS_COMPLETE = "COMPLETE"


DECISION_RECORD_ONLY = "RECORD ONLY"
DECISION_NOTIFY_REGULATOR = "NOTIFY REGULATOR"
DECISION_NOTIFY_REGULATOR_AND_CUSTOMERS = "NOTIFY REGULATOR AND CUSTOMERS"
DECISION_OPTIONS = [DECISION_RECORD_ONLY, DECISION_NOTIFY_REGULATOR,
                    DECISION_NOTIFY_REGULATOR_AND_CUSTOMERS]


INCIDENT_STATUS_PENDING = "PENDING_DECISION"
INCIDENT_STATUS_RECORDED = "RECORDED"
INCIDENT_STATUS_NOTIFIED = "NOTIFIED"
INCIDENT_STATUS_NOTIFIED_AND_DISCLOSED = "NOTIFIED_AND_DISCLOSED"
INCIDENT_STATUS_OPTIONS = [INCIDENT_STATUS_PENDING, INCIDENT_STATUS_RECORDED,
                           INCIDENT_STATUS_NOTIFIED, INCIDENT_STATUS_NOTIFIED_AND_DISCLOSED]

INCIDENT_STATUS_BY_DECISION = {
    DECISION_RECORD_ONLY: INCIDENT_STATUS_RECORDED,
    DECISION_NOTIFY_REGULATOR: INCIDENT_STATUS_NOTIFIED,
    DECISION_NOTIFY_REGULATOR_AND_CUSTOMERS: INCIDENT_STATUS_NOTIFIED_AND_DISCLOSED,
}


ANALYST_REQUEST_MINIMUM_CHARACTERS = 5
DECISION_REASON_MINIMUM_CHARACTERS = 10


ROLE_ANALYST = "Security Analyst"
ROLE_DPO = "Data Protection Officer"
ROLE_COMMUNICATIONS = "Customer Communications Agent"

PAGE_QUEUE = "Incident queue"
PAGE_INCIDENT = "Incident detail"
PAGE_DECISION = "Decision queue"
PAGE_AUDIT = "Audit trail"
PAGE_CHAT = "Response chat"


ROLE_PAGE_ACCESS = {
    ROLE_DPO: [PAGE_QUEUE, PAGE_INCIDENT, PAGE_DECISION, PAGE_AUDIT, PAGE_CHAT],
    ROLE_ANALYST: [PAGE_QUEUE, PAGE_INCIDENT, PAGE_AUDIT, PAGE_CHAT],
    ROLE_COMMUNICATIONS: [PAGE_CHAT],
}


AREA_INTAKE = "intake"
AREA_ASSESSMENT = "assessment"
AREA_DECISION = "decision"
AREA_AUDIT = "audit"
AREA_CHAT = "chat"


ROLE_AREA_ACCESS = {
    ROLE_DPO: [AREA_INTAKE, AREA_ASSESSMENT, AREA_DECISION, AREA_AUDIT, AREA_CHAT],
    ROLE_ANALYST: [AREA_INTAKE, AREA_ASSESSMENT, AREA_AUDIT, AREA_CHAT],
    ROLE_COMMUNICATIONS: [AREA_CHAT],
}


AREA_BY_PATH_START = {
    "/queue": AREA_INTAKE,
    "/assessments": AREA_ASSESSMENT,
    "/incidents": AREA_AUDIT,
    "/audit": AREA_AUDIT,
    "/chat": AREA_CHAT,
}


DECISION_PATH_ENDING = "/decision"


SEED_USER_ACCOUNTS = [
    {"username": "ines", "display_name": "Ines Carvalho", "role": ROLE_DPO, "password": "11111111"},
    {"username": "arjun", "display_name": "Arjun Menon", "role": ROLE_DPO, "password": "11111111"},
    {"username": "katarzyna", "display_name": "Katarzyna Wojcik", "role": ROLE_DPO, "password": "11111111"},
    {"username": "priya", "display_name": "Priya Raghavan", "role": ROLE_ANALYST, "password": "22222222"},
    {"username": "tomasz", "display_name": "Tomasz Nowak", "role": ROLE_ANALYST, "password": "22222222"},
    {"username": "kadri", "display_name": "Kadri Tamm", "role": ROLE_ANALYST, "password": "22222222"},
    {"username": "joao", "display_name": "Joao Ferreira", "role": ROLE_ANALYST, "password": "22222222"},
    {"username": "meera", "display_name": "Meera Pillai", "role": ROLE_ANALYST, "password": "22222222"},
    {"username": "rasmus", "display_name": "Rasmus Kask", "role": ROLE_ANALYST, "password": "22222222"},
    {"username": "ananya", "display_name": "Ananya Kulkarni", "role": ROLE_COMMUNICATIONS, "password": "33333333"},
    {"username": "mateusz", "display_name": "Mateusz Zielinski", "role": ROLE_COMMUNICATIONS, "password": "33333333"},
    {"username": "liis", "display_name": "Liis Saar", "role": ROLE_COMMUNICATIONS, "password": "33333333"},
    {"username": "beatriz", "display_name": "Beatriz Sousa", "role": ROLE_COMMUNICATIONS, "password": "33333333"},
    {"username": "rohan", "display_name": "Rohan Desai", "role": ROLE_COMMUNICATIONS, "password": "33333333"},
    {"username": "marta", "display_name": "Marta Kowalczyk", "role": ROLE_COMMUNICATIONS, "password": "33333333"},
]

PASSWORD_HASH_ALGORITHM = "sha256"
PASSWORD_HASH_ROUNDS = 200000
PASSWORD_SALT_BYTES = 16
SESSION_TOKEN_BYTES = 24


SESSION_TOKEN_HEADER = "X-Session-Token"
SIGN_IN_FAILED_MESSAGE = "Username or password is not correct"
SIGN_IN_REQUIRED_MESSAGE = "Sign in first"
AREA_REFUSED_MESSAGE = "A %s may not use the %s area"
ASSESSMENT_NOT_FOUND_MESSAGE = "No assessment has that identifier"
ALREADY_DECIDED_MESSAGE = "This assessment has already been decided"


CHUNK_SIZE_CHARACTERS = 700
CHUNK_OVERLAP_CHARACTERS = 120
RETRIEVAL_RESULT_COUNT = 4

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cpu"


SECTION_HEADING_PATTERN = r"(?:^|(?<=\s))(\d{1,2})\.\s+[A-Z]"

SENTENCE_BOUNDARY_PATTERN = r"(?<=[.:;])(?<![0-9]\.)\s+"


DOCUMENT_HEADER_PATTERN = r"Document\s+[A-Za-z0-9 ]+\|\s*(?:Rev|Version)\s*\d+.*?Review cycle:\s*[A-Za-z0-9 ]+"


INCIDENT_REFERENCE_PATTERN = r"\bINC-(?:%s)-\d{7}\b" % "|".join(HUB_CODE_BY_HUB.values())


GEMINI_API_KEY_VARIABLE = "GEMINI_API_KEY"
GEMINI_MODEL_VARIABLE = "GEMINI_MODEL"
GEMINI_MAX_OUTPUT_TOKENS = 900
GEMINI_TEMPERATURE = 0.2

AGENT_NAME_PLANNER = "incident_intake_planner"
AGENT_NAME_HARM = "harm_analyst"
AGENT_NAME_ATTACK = "attack_analyst"
AGENT_NAME_REPORTING = "reporting_duty_advisor"
AGENT_NAME_WRITER = "incident_writer"
AGENT_NAME_CUSTOMER_NOTICE = "customer_notice_agent"
AGENT_NAME_REGULATOR_FILING = "regulator_filing_agent"
AGENT_NAME_RESPONSE_ASSISTANT = "response_assistant"


RESPONSE_DECORATION_CHARACTERS = "*#`_~ \t-–—•>:[]"


LLM_CALLS_BEFORE_DECISION = 5
LLM_CALLS_BY_DECISION = {
    DECISION_RECORD_ONLY: 5,
    DECISION_NOTIFY_REGULATOR: 6,
    DECISION_NOTIFY_REGULATOR_AND_CUSTOMERS: 7,
}


CHAT_TYPE_PROCEDURE = "PROCEDURE"
CHAT_TYPE_REGULATION = "REGULATION"
CHAT_TYPE_CUSTOMER_ADVICE = "CUSTOMER ADVICE"
CHAT_TYPE_INCIDENT_STATUS = "INCIDENT STATUS"
CHAT_TYPE_OUT_OF_SCOPE = "OUT OF SCOPE"
CHAT_TYPE_OPTIONS = [CHAT_TYPE_PROCEDURE, CHAT_TYPE_REGULATION, CHAT_TYPE_CUSTOMER_ADVICE,
                     CHAT_TYPE_INCIDENT_STATUS, CHAT_TYPE_OUT_OF_SCOPE]
CHAT_ANSWERED_TYPES = [CHAT_TYPE_PROCEDURE, CHAT_TYPE_REGULATION, CHAT_TYPE_CUSTOMER_ADVICE]

CHAT_QUESTION_MINIMUM_CHARACTERS = 3
CHAT_EXCLUDED_DOCUMENTS = ["Past-Incidents-Casebook.pdf"]


CHAT_INCIDENT_STATUS_ROLES = [ROLE_ANALYST, ROLE_DPO]
CHAT_DISCLOSED_INCIDENT_STATUSES = [INCIDENT_STATUS_NOTIFIED_AND_DISCLOSED]


CHAT_INCIDENT_REFUSAL_MESSAGE = "I can't share anything about that incident. I can explain what Merrowfield does after a security incident and what customers can do to protect themselves."


CHAT_HISTORY_TURN_LIMIT = 3
CHAT_PAGE_TURN_LIMIT = 20


CHAT_MAX_RELEVANCE_DISTANCE = 0.6

CHAT_REFUSAL_MESSAGE = "I can only answer from Merrowfield's reporting procedures, policies, standards and playbooks. I could not find anything in them that answers that."
CHAT_UNKNOWN_INCIDENT_MESSAGE = "I could not find that incident in the incident queue. Name it by its reference, in the form INC-BLR-1234567."
CHAT_NOT_ASSESSED_TEMPLATE = "%s is in the incident queue and has not been assessed yet, so there is no assessment to report on."
CHAT_PUBLISHED_NOTICE_TEMPLATE = "Merrowfield told the customers affected by %s in a notice sent at %s. This is the notice as it was published:\n\n%s"
CHAT_PUBLISHED_NOTICE_SOURCE_TEMPLATE = "Customer notice for %s"


CHAT_AUDIT_MAX_ROWS = 200


CHAT_AUDIT_RECENT_ROWS = 25


API_HOST = "0.0.0.0"
API_PORT = 8081
API_TITLE = "BreachWatch AI API"


API_BASE_URL = "http://localhost:8081"
API_REQUEST_TIMEOUT_SECONDS = 180

DASHBOARD_TITLE = "BreachWatch AI"
DASHBOARD_SUBTITLE = ORGANISATION_NAME + " - Incident Triage and Breach Reporting"


HARM_BAND_BADGE_COLOURS = {
    HARM_BAND_HIGH: "red",
    HARM_BAND_MEDIUM: "orange",
    HARM_BAND_LOW: "green",
}
DECISION_BADGE_COLOURS = {
    DECISION_RECORD_ONLY: "green",
    DECISION_NOTIFY_REGULATOR: "orange",
    DECISION_NOTIFY_REGULATOR_AND_CUSTOMERS: "red",
}
DEADLINE_OVERDUE_COLOUR = "red"
DEADLINE_EARLIEST_COLOUR = "orange"
CHAT_TYPE_BADGE_COLOURS = {
    CHAT_TYPE_PROCEDURE: "blue",
    CHAT_TYPE_REGULATION: "violet",
    CHAT_TYPE_CUSTOMER_ADVICE: "green",
    CHAT_TYPE_INCIDENT_STATUS: "orange",
    CHAT_TYPE_OUT_OF_SCOPE: "gray",
}
