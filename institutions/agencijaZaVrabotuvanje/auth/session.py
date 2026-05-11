from shared.session import SessionManager
from institutions.agencijaZaVrabotuvanje.config import SESSION_FILE

session_manager = SessionManager(
    session_file=SESSION_FILE,
    institution_id="agencijaZaVrabotuvanje",
)