import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
load_dotenv(PROJECT_ROOT / ".env")

PORTAL_BASE_URL = os.getenv("AV_BASE_URL", "https://e-rabota.av.gov.mk")
PROTECTED_HOME_URL = f"{PORTAL_BASE_URL}/protected/Default.aspx"
EDIT_CV_LIST_URL = f"{PORTAL_BASE_URL}/protected/EditCV.aspx"
CV_CREATE_EDIT_URL = f"{PORTAL_BASE_URL}/protected/KreiranjeNaCv.aspx"
CV_PRINT_URL = f"{PORTAL_BASE_URL}/protected/CvPrintanje.aspx"

LOGIN_URL = PORTAL_BASE_URL
POST_LOGIN_HOSTNAME = "e-rabota.av.gov.mk"
POST_LOGIN_PATH = "/protected/Default.aspx"
COOKIE_DOMAIN = "e-rabota.av.gov.mk"

OGLASI_URL = f"{PORTAL_BASE_URL}/OglasSearch.aspx"
DETALI_URL = f"{PORTAL_BASE_URL}/OglasDetali.aspx"

SESSION_FILE = PROJECT_ROOT / os.getenv(
    "AV_SESSION_FILE",
    "storage/av_session.enc"
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")