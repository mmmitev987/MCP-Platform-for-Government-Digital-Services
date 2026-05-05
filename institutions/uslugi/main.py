"""
institutions/uslugi/main.py
────────────────────────────────────────────────────────────────────────────────
FastMCP server entry point for uslugi.gov.mk.

This file wires together all tools for this institution and exposes them via
the MCP stdio transport.  It is designed to be run as a subprocess by the
gateway (gateway/main.py), but can also be run standalone for testing:

    python -m institutions.uslugi.main

Architecture in context:
  gateway/main.py
    └── spawns this as a subprocess
    └── connects via MCP stdio
    └── exposes tools to the agent under the "uslugi__" namespace

Adding new tools:
  1. Create the tool function in institutions/uslugi/tools/<file>.py.
  2. Import it here and decorate the wrapper with @mcp.tool().
  3. Write a clear docstring — it becomes the tool description shown to the LLM.
"""

from mcp.server.fastmcp import FastMCP

# ── Tool implementations ──────────────────────────────────────────────────────
from institutions.uslugi.tools.passport import info_passport_renewal as _info_passport_renewal
from institutions.uslugi.tools.session_tools import (
    login as _login,
    logout as _logout,
    check_session as _check_session,
)
from institutions.uslugi.tools.mvr_info import (
    info_mvr_passport_renewal,
    info_mvr_passport_lost,
    info_mvr_passport_first_time,
    info_mvr_passport_minor,
    info_mvr_id_first_time,
    info_mvr_id_renewal,
    info_mvr_id_minor,
    info_mvr_license_first_time,
    info_mvr_license_driving_school,
    info_mvr_license_instructor,
    info_mvr_vehicle_registration_new,
    info_mvr_vehicle_registration_used,
    info_mvr_vehicle_deregistration,
    info_mvr_vehicle_test_drive,
    info_mvr_residence_certificate,
    info_mvr_citizenship_certificate,
    info_mvr_weapon_permit_individual,
    info_mvr_weapon_permit_company,
    info_mvr_weapon_collector,
    info_mvr_weapon_ammo_permit,
    info_mvr_weapon_transport_import,
    info_mvr_weapon_transport_export,
    info_mvr_weapon_transport_transit,
    info_mvr_weapon_cross_border,
    info_mvr_residence_registration,
    info_mvr_temporary_residence_registration,
    info_mvr_address_change,
    info_mvr_citizenship_by_origin_both_parents,
    info_mvr_citizenship_by_origin_one_parent,
    info_mvr_citizenship_by_origin_born_abroad,
    info_mvr_citizenship_by_birth,
    info_mvr_citizenship_naturalization,
    info_mvr_citizenship_naturalization_married,
    info_mvr_citizenship_naturalization_married_abroad,
    info_mvr_citizenship_naturalization_stateless,
    info_mvr_citizenship_naturalization_national_interest,
    info_mvr_citizenship_naturalization_sports,
    info_mvr_citizenship_naturalization_cultural,
    info_mvr_citizenship_naturalization_economic,
    info_mvr_citizenship_naturalization_scientific,
    info_mvr_citizenship_naturalization_diaspora,
    info_mvr_citizenship_renunciation,
    info_mvr_name_change_adult,
    info_mvr_name_change_minor_over10,
    info_mvr_name_change_minor_under10,
    info_mvr_embg_assign,
    info_mvr_embg_cancel,
    info_mvr_visa_border,
    info_mvr_temporary_stay_student_exchange,
    info_mvr_asylum_regular,
    info_mvr_asylum_urgent,
    info_mvr_asylum_family_reunification,
    info_mvr_asylum_id_card,
    info_mvr_asylum_travel_document,
    info_mvr_asylum_applicant_id,
    info_mvr_private_security_physical,
    info_mvr_private_security_technical,
    info_mvr_private_security_own_needs,
    info_mvr_detective_license,
    info_mvr_technical_inspection_authorization,
    info_mvr_technical_inspection_license,
    info_mvr_test_drive_authorization,
    info_mvr_dangerous_goods_authorization,
    info_mvr_sports_event_on_road,
    info_mvr_foreign_vehicle_permission,
    info_mvr_border_crossing_permit,
    info_mvr_border_zone_settlement,
)
from institutions.uslugi.tools.fk_info import (
    info_fk_license_pharmacist_mk,
    info_fk_license_pharmacist_foreign_edu,
    info_fk_license_pharmacist_foreign_license,
    info_fk_license_pharmacist_foreign_citizen,
    info_fk_license_renewal,
    info_fk_license_extend,
    info_fk_license_reacquire,
    info_fk_register_pharmacist,
    info_fk_update_personal_data,
    info_fk_update_professional_data,
    info_fk_professional_exam,
    info_fk_additional_training,
    info_fk_recognize_foreign_exam,
    info_fk_confirmation,
    info_fk_confirmation_abroad,
    info_fk_license_duplicate,
    info_fk_probation_work,
)

# ── Create the FastMCP server instance ───────────────────────────────────────
# The name here is only used in MCP handshake metadata — it is NOT the
# tool prefix.  The gateway adds the "uslugi__" prefix when it registers
# these tools in its own namespace.
mcp = FastMCP("uslugi-gov-mk")


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION TOOLS
# Control the authentication lifecycle.  The LLM can call these but never
# sees passwords or raw cookie values.
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def login() -> dict:
    """
    Authenticate the user on uslugi.gov.mk via browser and save the session.

    Opens a Chromium window for the user to complete the eid.mk SSO login.

    Returns:
        { "success": bool, "message": str, "strategy_used": str, "cookies_saved": int }
    """
    return _login()


@mcp.tool()
def logout() -> dict:
    """
    Log out of uslugi.gov.mk by deleting the stored session cookies.

    Returns:
        { "success": bool, "message": str }
    """
    return _logout()


@mcp.tool()
def check_session() -> dict:
    """
    Check whether an active session exists for uslugi.gov.mk.

    This is a local file check — it does NOT make a network request.
    Call this before authenticated requests to surface a friendly error
    instead of an unexpected HTTP failure.

    Returns:
        { "active": bool, "saved_at": str | None, "message": str }
    """
    return _check_session()


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC INFORMATION TOOLS
# These do not require authentication.
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def info_passport_renewal() -> dict:
    """
    Fetch detailed information about the passport renewal service (ID 5200)
    from uslugi.gov.mk.

    No login required — this endpoint is publicly accessible.

    Returns a dict with:
        name, description, requirements, conditions, deadlines,
        delivery_in, delivery_out, contact, applyUrl.
    """
    return _info_passport_renewal()


@mcp.tool()
def search_services(query: str) -> list[dict]:
    """
    Search the portal for services (e.g., 'passport', 'driver license').
    Returns a list of results. If a result has 'is_group': true,
    you MUST call get_group_contents(id) to see the specific services inside.
    """
    return _search(query)

@mcp.tool()
def get_group_contents(group_id: int) -> list[dict]:
    """
    Lists all specific services within a service category/group.
    Call this when search_services indicates a result is a group.
    """
    return _get_group(group_id)

@mcp.tool()
def get_service_requirements(service_id: int) -> dict:
    """
    Fetches the documents, price, and application link for a specific service ID.
    Call this once you have identified the exact service the user wants.
    """
    return _get_details(service_id)

# ═══════════════════════════════════════════════════════════════════════════════
# MVR — МИНИСТЕРСТВО ЗА ВНАТРЕШНИ РАБОТИ
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def mvr_info_passport_renewal() -> dict:
    """MVR: Requirements and info for passport renewal (service 5200). No login required."""
    return info_mvr_passport_renewal()

@mcp.tool()
def mvr_info_passport_lost() -> dict:
    """MVR: Requirements and info for replacing a lost passport (service 5201). No login required."""
    return info_mvr_passport_lost()

@mcp.tool()
def mvr_info_passport_first_time() -> dict:
    """MVR: Requirements and info for a first-time passport (service 5202). No login required."""
    return info_mvr_passport_first_time()

@mcp.tool()
def mvr_info_passport_minor() -> dict:
    """MVR: Requirements and info for a minor's passport (service 5204). No login required."""
    return info_mvr_passport_minor()

@mcp.tool()
def mvr_info_id_first_time() -> dict:
    """MVR: Requirements and info for a first-time ID card (service 5227). No login required."""
    return info_mvr_id_first_time()

@mcp.tool()
def mvr_info_id_renewal() -> dict:
    """MVR: Requirements and info for ID card renewal (service 5225). No login required."""
    return info_mvr_id_renewal()

@mcp.tool()
def mvr_info_id_minor() -> dict:
    """MVR: Requirements and info for a minor's ID card (service 5226). No login required."""
    return info_mvr_id_minor()

@mcp.tool()
def mvr_info_license_first_time() -> dict:
    """MVR: Requirements and info for a first-time driver's license (service 5208). No login required."""
    return info_mvr_license_first_time()

@mcp.tool()
def mvr_info_license_driving_school() -> dict:
    """MVR: Requirements and info for a driving school license (service 2965). No login required."""
    return info_mvr_license_driving_school()

@mcp.tool()
def mvr_info_license_instructor() -> dict:
    """MVR: Requirements and info for a driving instructor license (service 2981). No login required."""
    return info_mvr_license_instructor()

@mcp.tool()
def mvr_info_vehicle_registration_new() -> dict:
    """MVR: Requirements and info for registering a new vehicle (service 4452). No login required."""
    return info_mvr_vehicle_registration_new()

@mcp.tool()
def mvr_info_vehicle_registration_used() -> dict:
    """MVR: Requirements and info for registering a used vehicle (service 4268). No login required."""
    return info_mvr_vehicle_registration_used()

@mcp.tool()
def mvr_info_vehicle_deregistration() -> dict:
    """MVR: Requirements and info for vehicle deregistration (service 4472). No login required."""
    return info_mvr_vehicle_deregistration()

@mcp.tool()
def mvr_info_vehicle_test_drive() -> dict:
    """MVR: Requirements and info for a test drive permit (service 1960). No login required."""
    return info_mvr_vehicle_test_drive()

@mcp.tool()
def mvr_info_residence_certificate() -> dict:
    """MVR: Requirements and info for a residence certificate (service 5737). No login required."""
    return info_mvr_residence_certificate()

@mcp.tool()
def mvr_info_citizenship_certificate() -> dict:
    """MVR: Requirements and info for a citizenship certificate (service 5780). No login required."""
    return info_mvr_citizenship_certificate()

@mcp.tool()
def mvr_info_weapon_permit_individual() -> dict:
    """MVR: Requirements and info for an individual weapon permit (service 4044). No login required."""
    return info_mvr_weapon_permit_individual()

@mcp.tool()
def mvr_info_weapon_permit_company() -> dict:
    """MVR: Requirements and info for a company weapon permit (service 4045). No login required."""
    return info_mvr_weapon_permit_company()

@mcp.tool()
def mvr_info_weapon_collector() -> dict:
    """MVR: Requirements and info for a weapon collector permit (service 4046). No login required."""
    return info_mvr_weapon_collector()

@mcp.tool()
def mvr_info_weapon_ammo_permit() -> dict:
    """MVR: Requirements and info for an ammunition permit (service 4043). No login required."""
    return info_mvr_weapon_ammo_permit()

@mcp.tool()
def mvr_info_weapon_transport_import() -> dict:
    """MVR: Requirements and info for weapon import transport permit (service 4048). No login required."""
    return info_mvr_weapon_transport_import()

@mcp.tool()
def mvr_info_weapon_transport_export() -> dict:
    """MVR: Requirements and info for weapon export transport permit (service 4056). No login required."""
    return info_mvr_weapon_transport_export()

@mcp.tool()
def mvr_info_weapon_transport_transit() -> dict:
    """MVR: Requirements and info for weapon transit transport permit (service 4063). No login required."""
    return info_mvr_weapon_transport_transit()

@mcp.tool()
def mvr_info_weapon_cross_border() -> dict:
    """MVR: Requirements and info for cross-border weapon transport (service 4064). No login required."""
    return info_mvr_weapon_cross_border()

@mcp.tool()
def mvr_info_residence_registration() -> dict:
    """MVR: Requirements and info for registering permanent residence (service 1668). No login required."""
    return info_mvr_residence_registration()

@mcp.tool()
def mvr_info_temporary_residence_registration() -> dict:
    """MVR: Requirements and info for registering temporary residence (service 1673). No login required."""
    return info_mvr_temporary_residence_registration()

@mcp.tool()
def mvr_info_address_change() -> dict:
    """MVR: Requirements and info for changing registered address (service 1674). No login required."""
    return info_mvr_address_change()

@mcp.tool()
def mvr_info_citizenship_by_origin_both_parents() -> dict:
    """MVR: Citizenship by origin — both parents Macedonian citizens (service 1716). No login required."""
    return info_mvr_citizenship_by_origin_both_parents()

@mcp.tool()
def mvr_info_citizenship_by_origin_one_parent() -> dict:
    """MVR: Citizenship by origin — one parent a Macedonian citizen (service 1717). No login required."""
    return info_mvr_citizenship_by_origin_one_parent()

@mcp.tool()
def mvr_info_citizenship_by_origin_born_abroad() -> dict:
    """MVR: Citizenship by origin — born abroad (service 1623). No login required."""
    return info_mvr_citizenship_by_origin_born_abroad()

@mcp.tool()
def mvr_info_citizenship_by_birth() -> dict:
    """MVR: Citizenship by birth on Macedonian territory (service 1670). No login required."""
    return info_mvr_citizenship_by_birth()

@mcp.tool()
def mvr_info_citizenship_naturalization() -> dict:
    """MVR: Citizenship by naturalization (service 5242). No login required."""
    return info_mvr_citizenship_naturalization()

@mcp.tool()
def mvr_info_citizenship_naturalization_married() -> dict:
    """MVR: Citizenship by naturalization — married to a citizen (service 5243). No login required."""
    return info_mvr_citizenship_naturalization_married()

@mcp.tool()
def mvr_info_citizenship_naturalization_married_abroad() -> dict:
    """MVR: Citizenship by naturalization — married abroad (service 5244). No login required."""
    return info_mvr_citizenship_naturalization_married_abroad()

@mcp.tool()
def mvr_info_citizenship_naturalization_stateless() -> dict:
    """MVR: Citizenship by naturalization — stateless persons (service 5245). No login required."""
    return info_mvr_citizenship_naturalization_stateless()

@mcp.tool()
def mvr_info_citizenship_naturalization_national_interest() -> dict:
    """MVR: Citizenship by naturalization — national interest (service 5246). No login required."""
    return info_mvr_citizenship_naturalization_national_interest()

@mcp.tool()
def mvr_info_citizenship_naturalization_sports() -> dict:
    """MVR: Citizenship by naturalization — sports merit (service 5247). No login required."""
    return info_mvr_citizenship_naturalization_sports()

@mcp.tool()
def mvr_info_citizenship_naturalization_cultural() -> dict:
    """MVR: Citizenship by naturalization — cultural merit (service 5248). No login required."""
    return info_mvr_citizenship_naturalization_cultural()

@mcp.tool()
def mvr_info_citizenship_naturalization_economic() -> dict:
    """MVR: Citizenship by naturalization — economic contribution (service 5249). No login required."""
    return info_mvr_citizenship_naturalization_economic()

@mcp.tool()
def mvr_info_citizenship_naturalization_scientific() -> dict:
    """MVR: Citizenship by naturalization — scientific merit (service 5250). No login required."""
    return info_mvr_citizenship_naturalization_scientific()

@mcp.tool()
def mvr_info_citizenship_naturalization_diaspora() -> dict:
    """MVR: Citizenship by naturalization — diaspora (service 5251). No login required."""
    return info_mvr_citizenship_naturalization_diaspora()

@mcp.tool()
def mvr_info_citizenship_renunciation() -> dict:
    """MVR: Requirements and info for renouncing Macedonian citizenship (service 1685). No login required."""
    return info_mvr_citizenship_renunciation()

@mcp.tool()
def mvr_info_name_change_adult() -> dict:
    """MVR: Requirements and info for changing name — adult (service 1688). No login required."""
    return info_mvr_name_change_adult()

@mcp.tool()
def mvr_info_name_change_minor_over10() -> dict:
    """MVR: Requirements and info for changing name — minor over 10 (service 5451). No login required."""
    return info_mvr_name_change_minor_over10()

@mcp.tool()
def mvr_info_name_change_minor_under10() -> dict:
    """MVR: Requirements and info for changing name — minor under 10 (service 5452). No login required."""
    return info_mvr_name_change_minor_under10()

@mcp.tool()
def mvr_info_embg_assign() -> dict:
    """MVR: Requirements and info for assigning a personal ID number (EMBG) (service 1699). No login required."""
    return info_mvr_embg_assign()

@mcp.tool()
def mvr_info_embg_cancel() -> dict:
    """MVR: Requirements and info for cancelling a personal ID number (EMBG) (service 1704). No login required."""
    return info_mvr_embg_cancel()

@mcp.tool()
def mvr_info_visa_border() -> dict:
    """MVR: Requirements and info for a border visa (service 1919). No login required."""
    return info_mvr_visa_border()

@mcp.tool()
def mvr_info_temporary_stay_student_exchange() -> dict:
    """MVR: Requirements and info for temporary stay — student exchange (service 5389). No login required."""
    return info_mvr_temporary_stay_student_exchange()

@mcp.tool()
def mvr_info_asylum_regular() -> dict:
    """MVR: Requirements and info for regular asylum application (service 1785). No login required."""
    return info_mvr_asylum_regular()

@mcp.tool()
def mvr_info_asylum_urgent() -> dict:
    """MVR: Requirements and info for urgent asylum application (service 1786). No login required."""
    return info_mvr_asylum_urgent()

@mcp.tool()
def mvr_info_asylum_family_reunification() -> dict:
    """MVR: Requirements and info for asylum — family reunification (service 1790). No login required."""
    return info_mvr_asylum_family_reunification()

@mcp.tool()
def mvr_info_asylum_id_card() -> dict:
    """MVR: Requirements and info for asylum seeker ID card (service 1788). No login required."""
    return info_mvr_asylum_id_card()

@mcp.tool()
def mvr_info_asylum_travel_document() -> dict:
    """MVR: Requirements and info for asylum travel document (service 1789). No login required."""
    return info_mvr_asylum_travel_document()

@mcp.tool()
def mvr_info_asylum_applicant_id() -> dict:
    """MVR: Requirements and info for asylum applicant ID (service 1787). No login required."""
    return info_mvr_asylum_applicant_id()

@mcp.tool()
def mvr_info_private_security_physical() -> dict:
    """MVR: Requirements and info for physical private security license (service 2994). No login required."""
    return info_mvr_private_security_physical()

@mcp.tool()
def mvr_info_private_security_technical() -> dict:
    """MVR: Requirements and info for technical private security license (service 3013). No login required."""
    return info_mvr_private_security_technical()

@mcp.tool()
def mvr_info_private_security_own_needs() -> dict:
    """MVR: Requirements and info for private security for own needs (service 3015). No login required."""
    return info_mvr_private_security_own_needs()

@mcp.tool()
def mvr_info_detective_license() -> dict:
    """MVR: Requirements and info for a detective license (service 4068). No login required."""
    return info_mvr_detective_license()

@mcp.tool()
def mvr_info_technical_inspection_authorization() -> dict:
    """MVR: Requirements and info for technical inspection authorization (service 4139). No login required."""
    return info_mvr_technical_inspection_authorization()

@mcp.tool()
def mvr_info_technical_inspection_license() -> dict:
    """MVR: Requirements and info for technical inspection license (service 4468). No login required."""
    return info_mvr_technical_inspection_license()

@mcp.tool()
def mvr_info_test_drive_authorization() -> dict:
    """MVR: Requirements and info for test drive authorization (service 4440). No login required."""
    return info_mvr_test_drive_authorization()

@mcp.tool()
def mvr_info_dangerous_goods_authorization() -> dict:
    """MVR: Requirements and info for dangerous goods transport authorization (service 4257). No login required."""
    return info_mvr_dangerous_goods_authorization()

@mcp.tool()
def mvr_info_sports_event_on_road() -> dict:
    """MVR: Requirements and info for organizing a sports event on a public road (service 2963). No login required."""
    return info_mvr_sports_event_on_road()

@mcp.tool()
def mvr_info_foreign_vehicle_permission() -> dict:
    """MVR: Requirements and info for foreign vehicle road permit (service 2979). No login required."""
    return info_mvr_foreign_vehicle_permission()

@mcp.tool()
def mvr_info_border_crossing_permit() -> dict:
    """MVR: Requirements and info for a border crossing permit (service 4240). No login required."""
    return info_mvr_border_crossing_permit()

@mcp.tool()
def mvr_info_border_zone_settlement() -> dict:
    """MVR: Requirements and info for border zone settlement permit (service 4069). No login required."""
    return info_mvr_border_zone_settlement()


# ═══════════════════════════════════════════════════════════════════════════════
# FK — ФАРМАЦЕВТСКА КОМОРА НА МАКЕДОНИЈА
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def fk_info_license_pharmacist_mk() -> dict:
    """FK: Info for pharmacist work license — education in North Macedonia (service 5064). No login required."""
    return info_fk_license_pharmacist_mk()

@mcp.tool()
def fk_info_license_pharmacist_foreign_edu() -> dict:
    """FK: Info for pharmacist work license — foreign university education (service 5601). No login required."""
    return info_fk_license_pharmacist_foreign_edu()

@mcp.tool()
def fk_info_license_pharmacist_foreign_license() -> dict:
    """FK: Info for pharmacist work license — holder of foreign license (service 5604). No login required."""
    return info_fk_license_pharmacist_foreign_license()

@mcp.tool()
def fk_info_license_pharmacist_foreign_citizen() -> dict:
    """FK: Info for pharmacist work license — foreign citizen (service 5605). No login required."""
    return info_fk_license_pharmacist_foreign_citizen()

@mcp.tool()
def fk_info_license_renewal() -> dict:
    """FK: Info for pharmacist license renewal (every 7 years, service 5112). No login required."""
    return info_fk_license_renewal()

@mcp.tool()
def fk_info_license_extend() -> dict:
    """FK: Info for pharmacist license extension (6-month extension, service 5611). No login required."""
    return info_fk_license_extend()

@mcp.tool()
def fk_info_license_reacquire() -> dict:
    """FK: Info for reacquiring a pharmacist license after loss (service 5612). No login required."""
    return info_fk_license_reacquire()

@mcp.tool()
def fk_info_register_pharmacist() -> dict:
    """FK: Info for registering in the Pharmacist Registry (service 5111). No login required."""
    return info_fk_register_pharmacist()

@mcp.tool()
def fk_info_update_personal_data() -> dict:
    """FK: Info for updating personal data in the Pharmacist Registry (service 5621). No login required."""
    return info_fk_update_personal_data()

@mcp.tool()
def fk_info_update_professional_data() -> dict:
    """FK: Info for updating professional data in the Pharmacist Registry (service 5652). No login required."""
    return info_fk_update_professional_data()

@mcp.tool()
def fk_info_professional_exam() -> dict:
    """FK: Info for applying to take the professional pharmacist exam (service 5617). No login required."""
    return info_fk_professional_exam()

@mcp.tool()
def fk_info_additional_training() -> dict:
    """FK: Info for additional pharmacist training and knowledge verification (service 5618). No login required."""
    return info_fk_additional_training()

@mcp.tool()
def fk_info_recognize_foreign_exam() -> dict:
    """FK: Info for recognizing a professional exam passed abroad (service 5619). No login required."""
    return info_fk_recognize_foreign_exam()

@mcp.tool()
def fk_info_confirmation() -> dict:
    """FK: Info for requesting an official confirmation from the Pharmacist Chamber (service 5620). No login required."""
    return info_fk_confirmation()

@mcp.tool()
def fk_info_confirmation_abroad() -> dict:
    """FK: Info for a pharmacist confirmation for working abroad (service 5622). No login required."""
    return info_fk_confirmation_abroad()

@mcp.tool()
def fk_info_license_duplicate() -> dict:
    """FK: Info for requesting a duplicate pharmacist license (lost or damaged, service 5624). No login required."""
    return info_fk_license_duplicate()

@mcp.tool()
def fk_info_probation_work() -> dict:
    """FK: Info for pharmacist probation work (required before professional exam, service 5613). No login required."""
    return info_fk_probation_work()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # mcp.run() starts the stdio transport loop.
    # This process will block, reading MCP JSON-RPC from stdin and writing
    # responses to stdout until the parent process (the gateway) closes the pipe.
    mcp.run()