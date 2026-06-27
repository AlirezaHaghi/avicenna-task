from datetime import datetime

from ninja import Router

from .schemas import IngestResponseOut, NotificationOut, StateReportIn
from .service import get_all_notifications, ingest_state_reports

router = Router()


@router.get("/", response=list[NotificationOut])
def list_notifications(
    request,
    limit: int = 20,
    offset: int = 0,
    deliver_after: datetime | None = None,
    deliver_before: datetime | None = None,
):
    """List notifications, each with a single aggregated status (see CHALLENGE.md, Task 3)."""
    return get_all_notifications(limit=limit, offset=offset)


@router.post("/", response=IngestResponseOut)
def update_notifications(request, reports: list[StateReportIn]):
    """Ingest lifecycle state reports (see CHALLENGE.md, Task 2)."""
    return ingest_state_reports(reports)
