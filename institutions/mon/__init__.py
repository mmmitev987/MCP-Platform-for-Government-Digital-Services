"""
institutions/mon/
────────────────────────────────────────────────────────────────────────────────
MCP adapter for the Ministry of Education and Science of North Macedonia.

Integrates two portals:
  • mon.gov.mk          — main ministry website (public information)
  • e-uslugi.mon.gov.mk — dedicated MON e-services portal (authenticated ops)

Public tools (no auth): info_mon_services, info_mon_service_details
Authenticated tools:    login_mon, logout_mon, check_session_mon,
                        apply_mon_service, check_mon_application_status,
                        get_mon_document, list_mon_document_types
"""
