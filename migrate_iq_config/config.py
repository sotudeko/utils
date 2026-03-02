# config.py
from requests.auth import HTTPBasicAuth

# --- SOURCE (EXPORT FROM) ---
SOURCE_URL = "http://localhost:8070"
SOURCE_USER = "admin"
SOURCE_PASS = "admin123"
SOURCE_AUTH = HTTPBasicAuth(SOURCE_USER, SOURCE_PASS)

# --- TARGET (IMPORT TO) ---
TARGET_URL = "http://localhost:8077"
TARGET_USER = "admin"
TARGET_PASS = "admin123"
TARGET_AUTH = HTTPBasicAuth(TARGET_USER, TARGET_PASS)

# --- SHARED ---
DATA_DIR = "./migration_data"
ORGS_APPS_FILE = "orgs_apps.json"
ROLE_MAPPINGS_FILE = "role_mappings.json"
HEADERS = {"Content-Type": "application/json"}

