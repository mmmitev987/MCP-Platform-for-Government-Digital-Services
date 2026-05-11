from .jobs_parser import (
    parse_oglasi,
    parse_total_pages,
    parse_job_details,
    parse_favourite_jobs,
)
from .dashboard_parser import parse_dashboard
from .cv_parser import parse_cv_list, parse_cv_edit_page

__all__ = [
    "parse_oglasi",
    "parse_total_pages",
    "parse_job_details",
    "parse_favourite_jobs",
    "parse_dashboard",
    "parse_cv_list",
    "parse_cv_edit_page",
]