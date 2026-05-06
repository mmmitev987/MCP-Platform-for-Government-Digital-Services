from fastapi import APIRouter, Depends
from backend.dependencies import get_current_user
from backend.models.user import User

router = APIRouter()

SERVICES_CATALOGUE = [
    {
        "category": "Appointments",
        "services": [
            {"name": "Book Medical Appointment", "tool": "mojtermin__get_available_appointments_by_name", "status": "connected"},
            {"name": "Find Doctors by City", "tool": "mojtermin__get_doctors_by_city", "status": "connected"},
            {"name": "Browse Specialties", "tool": "mojtermin__get_specialties", "status": "connected"},
            {"name": "List Clinics", "tool": "mojtermin__get_clinics", "status": "connected"},
            {"name": "Browse All Locations", "tool": "mojtermin__get_locations", "status": "connected"},
            {"name": "Find Location by Name", "tool": "mojtermin__get_location_by_name", "status": "connected"},
            {"name": "Browse All Doctors", "tool": "mojtermin__get_doctors", "status": "connected"},
            {"name": "Search Resources", "tool": "mojtermin__search_resources", "status": "connected"},
            {"name": "List Resources by City", "tool": "mojtermin__get_resources_by_city", "status": "connected"},
            {"name": "Check Appointment Slots", "tool": "mojtermin__get_available_slots", "status": "connected"},
            {"name": "Check Slots by Date Range", "tool": "mojtermin__get_slots_range", "status": "connected"},
            {"name": "Find First Available Slot", "tool": "mojtermin__get_first_available", "status": "connected"},
            {"name": "View Availability Summary", "tool": "mojtermin__get_availability_summary", "status": "connected"},
            {"name": "Check City Slots", "tool": "mojtermin__get_slots_for_city", "status": "connected"},
        ],
    },
    {
        "category": "Documents",
        "services": [
            {"name": "Passport Renewal", "tool": "uslugi__mvr_info_passport_renewal", "status": "connected"},
            {"name": "First-time Passport", "tool": "uslugi__mvr_info_passport_first_time", "status": "connected"},
            {"name": "ID Card Renewal", "tool": "uslugi__mvr_info_id_renewal", "status": "connected"},
            {"name": "First-time ID Card", "tool": "uslugi__mvr_info_id_first_time", "status": "connected"},
        ],
    },
    {
        "category": "Transport",
        "services": [
            {"name": "Driver's License", "tool": "uslugi__mvr_info_license_first_time", "status": "connected"},
            {"name": "Vehicle Registration (New)", "tool": "uslugi__mvr_info_vehicle_registration_new", "status": "connected"},
            {"name": "Vehicle Registration (Used)", "tool": "uslugi__mvr_info_vehicle_registration_used", "status": "connected"},
        ],
    },
    {
        "category": "Citizenship",
        "services": [
            {"name": "Citizenship by Birth", "tool": "uslugi__mvr_info_citizenship_by_birth", "status": "connected"},
            {"name": "Citizenship Naturalization", "tool": "uslugi__mvr_info_citizenship_naturalization", "status": "connected"},
            {"name": "Citizenship Renunciation", "tool": "uslugi__mvr_info_citizenship_renunciation", "status": "connected"},
        ],
    },
    {
        "category": "Health",
        "services": [
            {"name": "Pharmacist License", "tool": "uslugi__fk_info_license_pharmacist_mk", "status": "connected"},
            {"name": "Pharmacist Registry", "tool": "uslugi__fk_info_register_pharmacist", "status": "connected"},
            {"name": "Professional Pharmacist Exam", "tool": "uslugi__fk_info_professional_exam", "status": "connected"},
        ],
    },
    {
        "category": "General",
        "services": [
            {"name": "Residence Registration", "tool": "uslugi__mvr_info_residence_registration", "status": "connected"},
            {"name": "Address Change", "tool": "uslugi__mvr_info_address_change", "status": "connected"},
            {"name": "Residence Certificate", "tool": "uslugi__mvr_info_residence_certificate", "status": "connected"},
        ],
    },
]


@router.get("")
def get_services(_: User = Depends(get_current_user)):
    return SERVICES_CATALOGUE
