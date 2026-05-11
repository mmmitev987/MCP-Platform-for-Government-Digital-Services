from mcp.server.fastmcp import FastMCP

from institutions.agencijaZaVrabotuvanje.auth.session_tools import (
    login as _login,
    logout as _logout,
    check_session as _check_session,
)

from institutions.agencijaZaVrabotuvanje.tools.public_tools import (
    view_jobs as _view_jobs,
    search_jobs as _search_jobs,
    get_job_details as _get_job_details,
)

from institutions.agencijaZaVrabotuvanje.tools.authenticated_tools import (
    get_user_dashboard as _get_user_dashboard,
    view_cv as _view_cv,
    download_cv as _download_cv,
    create_cv as _create_cv,
    edit_cv as _edit_cv,
    save_job_favourite as _save_job_favourite,
    view_favourite_jobs as _view_favourite_jobs,
    remove_favourite_job as _remove_favourite_job,
    send_job_invitation as _send_job_invitation,
)

mcp = FastMCP("agencija-za-vrabotuvanje")


@mcp.tool()
def login() -> dict:
    """
    Starts browser-based authentication via eID SSO.
    Opens a browser window and saves session cookies after login.
    """
    return _login()


@mcp.tool()
def logout() -> dict:
    """
    Clears stored session cookies (logs the user out locally).
    """
    return _logout()


@mcp.tool()
def check_session() -> dict:
    """
    Checks whether a valid session exists in local storage.
    """
    return _check_session()


# ─────────────────────────────────────────────
# PUBLIC JOB SEARCH TOOLS
# ─────────────────────────────────────────────

@mcp.tool()
def view_jobs(page: int = 1) -> dict:
    """
    Returns all active job listings (no filters).
    """
    return _view_jobs(page=page)


@mcp.tool()
def search_jobs(
    zanimanje: str = "",
    centar: str = "",
    opstina: str = "",
    page: int = 1,
) -> dict:
    """
    Performs basic job search using filters:
    - occupation (zanimanje)
    - employment center (centar)
    - municipality (opstina)
    """
    return _search_jobs(
        zanimanje=zanimanje,
        centar=centar,
        opstina=opstina,
        page=page,
    )


@mcp.tool()
def get_job_details(oglas_id: str) -> dict:
    """
    Returns full details for a specific job listing.
    Requires oglas_id (internal job identifier).
    """
    return _get_job_details(oglas_id=oglas_id)


# ─────────────────────────────────────────────
# AUTHENTICATED USER TOOLS
# ─────────────────────────────────────────────

@mcp.tool()
def get_user_dashboard() -> dict:
    """
    Returns user dashboard data:
    - CV views
    - favourite companies
    - recommended jobs

    Requires authentication.
    """
    return _get_user_dashboard()


@mcp.tool()
def view_cv() -> dict:
    """
    Returns all CVs for the logged-in user.

    Requires authentication.
    """
    return _view_cv()


@mcp.tool()
def download_cv(cv_id: str = "") -> dict:
    """
    Downloads a CV.

    If cv_id is not provided:
    - Automatically selects the CV if only one exists
    - Otherwise requests user selection

    Requires authentication.
    """
    return _download_cv(cv_id=cv_id or None)


@mcp.tool()
def create_cv(data: dict) -> dict:
    """
    Creates a new CV using provided data.

    Requires authentication.
    """
    return _create_cv(data=data)


@mcp.tool()
def edit_cv(cv_id: str = "", data: dict | None = None) -> dict:
    """
    Edits an existing CV.

    If cv_id is not provided:
    - Automatically selects the CV if only one exists
    - Otherwise requests user selection

    If no data is provided:
    - Returns editable CV structure

    Requires authentication.
    """
    return _edit_cv(cv_id=cv_id or None, data=data)


# ─────────────────────────────────────────────
# JOB FAVOURITES & INVITATIONS
# ─────────────────────────────────────────────

@mcp.tool()
def save_job_favourite(oglas_id: str, favourite_name: str = "") -> dict:
    """
    Adds a job listing to user's favourites.

    Optional:
    - favourite_name: custom label for the saved job

    Requires authentication.
    """
    return _save_job_favourite(
        oglas_id=oglas_id,
        favourite_name=favourite_name or None,
    )


@mcp.tool()
def view_favourite_jobs() -> dict:
    """
    Returns all favourite job listings for the user.

    Requires authentication.
    """
    return _view_favourite_jobs()


@mcp.tool()
def remove_favourite_job(oglas_id: str) -> dict:
    """
    Removes a job listing from favourites.

    Requires authentication.
    """
    return _remove_favourite_job(oglas_id=oglas_id)


@mcp.tool()
def send_job_invitation(
    oglas_id: str,
    message: str = "",
    show_personal_data: bool = True,
) -> dict:
    """
    Sends a job application/invitation message to the employer.

    Parameters:
    - oglas_id: job identifier
    - message: optional message (max ~400 chars)
    - show_personal_data: whether to share personal info

    Requires authentication.
    """
    return _send_job_invitation(
        oglas_id=oglas_id,
        message=message,
        show_personal_data=show_personal_data,
    )

if __name__ == "__main__":
    mcp.run()