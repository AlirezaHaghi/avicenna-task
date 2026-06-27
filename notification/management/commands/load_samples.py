# load_samples.py
import json
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from notification.models import EmailChannel, Notification, SMSChannel

# I saw the tracking number is generated somewhere else out of notification
# But for loading the sample data, we need to use the same tracking number as in the state_reports.json
# so i had to create a map between id in tracking number
# defenetly not the best way to do it, but it works for loading the sample data
TRACKING_MAP = {
    # (notification_id, channel): tracking_id
    (1, "email"): "em_a1f0c97d2b3e",
    (1, "sms"): "sm_77b3e0148aa2",
    (2, "email"): "em_5c2d81f4a019",
    (3, "sms"): "sm_0e9a4f6c7d55",
}


class Command(BaseCommand):
    help = "Load samples/notifications.json into the database"

    def handle(self, *args, **options):
        print("Loading sample notifications...")
        samples_dir = Path("samples")
        notifications = json.loads((samples_dir / "notifications.json").read_text())
        loaded_sample_cnt = 0
        for n in notifications:
            user, _ = User.objects.get_or_create(username=n["user"])
            notif, _ = Notification.objects.get_or_create(
                id=n["id"],
                defaults={"user": user, "deliver_at": n["deliver_at"]},
            )

            for name, detail in n["channels"].items():
                if name == "email":
                    ec, is_created = EmailChannel.objects.get_or_create(
                        tracking_id=TRACKING_MAP[(n["id"], "email")],
                        defaults={
                            "notification": notif,
                            "to_email": detail["to"],
                            "title": detail["title"],
                            "body": detail["body"],
                        },
                    )
                    print(ec)
                    print(f"Loaded sample notification {n['id']} for user {n['user']}")
                    if is_created:
                        loaded_sample_cnt += 1

                elif name == "sms":
                    sms, is_created = SMSChannel.objects.get_or_create(
                        tracking_id=TRACKING_MAP[(n["id"], "sms")],
                        defaults={
                            "notification": notif,
                            "to_phone": detail["to"],
                            "text": detail["text"],
                        },
                    )
                    print(sms)
                    print(f"Loaded sample notification {n['id']} for user {n['user']}")
                    if is_created:
                        loaded_sample_cnt += 1
                else:
                    print("InvalidChannel")

        print(f"Loaded {loaded_sample_cnt} sample notifications.")
