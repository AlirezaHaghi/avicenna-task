from datetime import datetime

from django.db import transaction

from .models import EmailChannel, EmailStatus, Notification, SMSChannel, SMSStatus
from .schemas import (
    EmailChannelOut,
    IngestResponseOut,
    NotificationOut,
    ReportResultOut,
    SMSChannelOut,
    StateReportIn,
)

_STATUS_RANK: dict[str, int] = {
    "bounced": -1, "failed": -1, "undelivered": -1,
    "sent": 0, "delivered": 1, "opened": 2,
}

_RANK_TO_STATUS = {-1: "failed", 0: "sent", 1: "delivered", 2: "opened"}


def aggregate_status(email: EmailChannel | None, sms: SMSChannel | None) -> str:
    ranks = [_STATUS_RANK[ch.status] for ch in (email, sms) if ch is not None]
    return _RANK_TO_STATUS[min(ranks)] if ranks else "unknown"


def _build_notification_out(n: Notification) -> NotificationOut:
    email = next(iter(n.emailchannels.all()), None)
    sms = next(iter(n.smschannels.all()), None)
    return NotificationOut(
        id=n.pk,
        deliver_at=n.deliver_at,
        status=aggregate_status(email, sms),
        email=EmailChannelOut(tracking_id=email.tracking_id, status=email.status) if email else None,
        sms=SMSChannelOut(tracking_id=sms.tracking_id, status=sms.status) if sms else None,
    )


def get_all_notifications(
    limit: int = 10,
    offset: int = 0,
    deliver_after: datetime | None = None,
    deliver_before: datetime | None = None,
) -> list[NotificationOut]:
    qs = (
        Notification.objects
        .prefetch_related("emailchannels", "smschannels")
        .order_by("-deliver_at")
    )
    if deliver_after is not None:
        qs = qs.filter(deliver_at__gte=deliver_after)
    if deliver_before is not None:
        qs = qs.filter(deliver_at__lte=deliver_before)
    return [_build_notification_out(n) for n in qs[offset:offset + limit]]


def _fetch_channels(reports: list[StateReportIn]) -> dict[str, EmailChannel | SMSChannel]:

    email_ids = [r.tracking_id for r in reports if r.tracking_id.startswith("em_")]
    sms_ids = [r.tracking_id for r in reports if r.tracking_id.startswith("sm_")]
    return {
        **{c.tracking_id: c for c in EmailChannel.objects.filter(tracking_id__in=email_ids)},
        **{c.tracking_id: c for c in SMSChannel.objects.filter(tracking_id__in=sms_ids)},
    }


def _process_report(
    report: StateReportIn,
    channel: EmailChannel | SMSChannel | None,
) -> tuple[EmailChannel | SMSChannel | None, ReportResultOut]:
    tid = report.tracking_id

    def skip(reason: str) -> tuple[None, ReportResultOut]:
        return None, ReportResultOut(tracking_id=tid, result="skipped", reason=reason)

    if not tid.startswith(("em_", "sm_")):
        return skip("unknown tracking_id prefix")
    if channel is None:
        return skip("tracking_id not found")

    valid = EmailStatus.values if isinstance(channel, EmailChannel) else SMSStatus.values
    if report.status not in valid:
        return skip(f"invalid status '{report.status}' for this channel type")

    if channel.occurred_at is not None and report.occurred_at <= channel.occurred_at:
        return skip("stale report")

    channel.status = report.status
    channel.occurred_at = report.occurred_at
    channel.received_at = report.received_at
    return channel, ReportResultOut(tracking_id=tid, result="accepted")


def _bulk_save(channels: list[EmailChannel | SMSChannel]) -> None:
    fields = ["status", "occurred_at", "received_at"]
    with transaction.atomic():
        emails = [c for c in channels if isinstance(c, EmailChannel)]
        smses = [c for c in channels if isinstance(c, SMSChannel)]
        if emails:
            EmailChannel.objects.bulk_update(emails, fields)
        if smses:
            SMSChannel.objects.bulk_update(smses, fields)


def ingest_state_reports(reports: list[StateReportIn]) -> IngestResponseOut:
    channels = _fetch_channels(reports)
    to_update: list[EmailChannel | SMSChannel] = []
    results: list[ReportResultOut] = []

    for report in reports:
        channel, result = _process_report(report, channels.get(report.tracking_id))
        results.append(result)
        if channel is not None:
            to_update.append(channel)

    _bulk_save(to_update)
    accepted = sum(1 for r in results if r.result == "accepted")
    return IngestResponseOut(accepted=accepted, skipped=len(results) - accepted, details=results)