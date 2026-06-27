from datetime import datetime

from ninja import Schema
from pydantic import Field, field_validator


class StateReportIn(Schema):
    tracking_id: str = Field(..., max_length=100)
    status: str = Field(..., max_length=50)
    occurred_at: datetime
    # received_at is the wall-clock time the provider sent the webhook;
    # we store it for observability but never use it for ordering — that
    # would hide out-of-order delivery bugs in provider pipelines.
    received_at: datetime | None = None

    @field_validator("status")
    @classmethod
    def status_must_be_recognised(cls, v: str) -> str:
        # Lazy import: avoids a top-level dependency on models at Django init time.
        from .models import EmailStatus, SMSStatus
        if v not in {*EmailStatus.values, *SMSStatus.values}:
            raise ValueError(f"unrecognised status '{v}'")
        return v


class ReportResultOut(Schema):
    tracking_id: str
    result: str              # "accepted" | "skipped"
    reason: str | None = None


class IngestResponseOut(Schema):
    accepted: int
    skipped: int
    details: list[ReportResultOut]


class EmailChannelOut(Schema):
    tracking_id: str
    status: str


class SMSChannelOut(Schema):
    tracking_id: str
    status: str


class NotificationOut(Schema):
    id: int
    deliver_at: datetime
    status: str              # single aggregated status across all channels
    email: EmailChannelOut | None = None
    sms: SMSChannelOut | None = None