from datetime import date

from reminder_scheduler import Deadline, publish_reminder, reminder_for


class RecordingClient:
    def __init__(self):
        self.payloads = []

    def publish(self, payload, request_id):
        self.payloads.append((payload, request_id))
        return {"message_id": "m-1"}


def test_completed_deadline_is_not_published():
    item = Deadline("bio-2", "learner-7", "Lab report", date(2026, 10, 30), completed=True)
    client = RecordingClient()

    assert reminder_for(item, date(2026, 10, 23)) is None
    assert publish_reminder(item, date(2026, 10, 23), client) is None
    assert client.payloads == []
