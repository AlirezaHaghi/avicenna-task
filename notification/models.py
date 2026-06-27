from django.db import models


class Notification(models.Model):
    """A single logical message to one user (see CHALLENGE.md, Task 1)."""

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    deliver_at = models.DateTimeField(help_text="When this notification should be delivered")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification #{self.pk} for {self.user_id}"


class EmailStatus(models.TextChoices):
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    OPENED = "opened", "Opened"
    BOUNCED = "bounced", "Bounced"


class SMSStatus(models.TextChoices):
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"
    UNDELIVERED = "undelivered", "Undelivered"


class AbstractChannel(models.Model):
    """A single channel (email, sms, etc.) for a notification."""

    tracking_id = models.CharField(
        primary_key=True,
        max_length=255,
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )
    occurred_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    received_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the provider sent the webhook (for observability only)",
    )

    class Meta:
        abstract = True
        # indexes = [models.Index(fields=["tracking_id", "occurred_at"], include=["status"])]


class EmailChannel(AbstractChannel):
    """A single email channel for a notification."""

    to_email = models.EmailField()
    title = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=EmailStatus.choices,
        default=EmailStatus.SENT,
    )

    def __str__(self):
        return f"Email {self.tracking_id} [{self.status}]"


class SMSChannel(AbstractChannel):
    """A single SMS channel for a notification."""

    to_phone = models.CharField(max_length=20)
    text = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=SMSStatus.choices,
        default=SMSStatus.SENT,
    )

    def __str__(self):
        return f"SMS {self.tracking_id} [{self.status}]"
