import requests
from datetime import datetime, timezone, time as dtime
from dateutil import parser
import os

API_KEY = os.getenv("PD_API_KEY")
USER_EMAIL = os.getenv("PD_USER_EMAIL")

HEADERS = {
    "Authorization": f"Token token={API_KEY}",
    "Accept": "application/vnd.pagerduty+json;version=2",
    "Content-Type": "application/json",
    "From": USER_EMAIL
}

BASE_URL = "https://api.pagerduty.com"

START = dtime(7, 0)
END = dtime(19, 0)

def within_shift():
    now = datetime.now().time()
    return START <= now <= END


def get_triggered_incidents():
    url = f"{BASE_URL}/incidents"
    params = {
        "statuses[]": "triggered",
        "limit": 25
    }

    r = requests.get(url, headers=HEADERS, params=params)
    return r.json().get("incidents", [])


def acknowledge_incident(incident_id):
    url = f"{BASE_URL}/incidents/{incident_id}"
    data = {
        "incident": {
            "type": "incident_reference",
            "status": "acknowledged"
        }
    }

    r = requests.put(url, headers=HEADERS, json=data)
    print(f"Ack {incident_id}: {r.status_code}")


def main():
    if not within_shift():
        print("Outside shift hours")
        return

    incidents = get_triggered_incidents()
    now = datetime.now(timezone.utc)

    for incident in incidents:
        created_at = parser.parse(incident["created_at"])
        diff_minutes = (now - created_at).total_seconds() / 60

        if diff_minutes >= 6:
            acknowledge_incident(incident["id"])


if __name__ == "__main__":
    main()
