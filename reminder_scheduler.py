"""Schedule one learner reminder and publish its concrete message."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import os

from infrai_client import InfraiClient


@dataclass(frozen=True)
class Deadline:
    course_id: str
    learner_id: str
    title: str
    due_on: date
    completed: bool = False


def reminder_for(deadline: Deadline, today: date) -> dict[str, str] | None:
    if deadline.completed or deadline.due_on < today:
        return None
    return {
        "course_id": deadline.course_id,
        "learner_id": deadline.learner_id,
        "title": deadline.title,
        "due_on": deadline.due_on.isoformat(),
    }


def register_reminder(deadline: Deadline, webhook: str, client: InfraiClient) -> str:
    job = client.create_cron(
        cron_expr="0 8 * * *",
        task=webhook,
        request_id=f"deadline:{deadline.course_id}:{deadline.learner_id}",
    )
    return str(job["job_id"])


def publish_reminder(deadline: Deadline, today: date, client: InfraiClient) -> dict[str, str] | None:
    payload = reminder_for(deadline, today)
    if payload is None:
        return None
    client.publish(payload, request_id=f"reminder:{deadline.course_id}:{deadline.learner_id}:{payload['due_on']}")
    return payload


if __name__ == "__main__":
    client = InfraiClient()
    item = Deadline("math-101", "learner-42", "Final project", date.today())
    webhook = os.environ["REMINDER_WEBHOOK_URL"]
    print(register_reminder(item, webhook, client))
