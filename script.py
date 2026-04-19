import requests
from datetime import datetime, timezone, timedelta, time as dtime
from dateutil import parser
import os

# ====== CONFIG ======
API_KEY = os.getenv("PD_API_KEY")
USER_EMAIL = os.getenv("PD_USER_EMAIL")
USER_ID = os.getenv("PD_USER_ID")

BASE_URL = "https://api.pagerduty.com"

HEADERS = {
    "Authorization": f"Token token={API_KEY}",
    "Accept": "application/vnd.pagerduty+json;version=2",
    "Content-Type": "application/json",
    "From": USER_EMAIL
}

# IST = UTC + 5:30
IST_OFFSET = timedelta(hours=5, minutes=30)

START = dtime(7, 0)
END = dtime(19, 0)


# ====== TIME CHECK ======
def within_shift():
    now_utc = datetime.utcnow()
    now_ist = now_utc + IST_OFFSET

    print(f"UTC time: {now_utc.strftime('%H:%M:%S')}")
    print(f"IST time: {now_ist.strftime('%H:%M:%S')}")

    return START <= now_ist.time() <= END


# ====== FETCH INCIDENTS ======
def get_my_triggered_incidents():
    url = f"{BASE_URL}/incidents"

    params = {
        "statuses[]": "triggered",
        "user_ids[]": USER_ID,
        "limit": 25
    }

    r = requests.get(url, headers=HEADERS, params=params)

    if r.status_code != 200:
        print(f"Error fetching incidents: {r.status_code} {r.text}")
        return []

    return r.json().get("incidents", [])


# ====== ACK INCIDENT ======
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


# ====== MAIN ======
def main():
    print("===== PagerDuty Auto Ack Script =====")

    if not within_shift():
        print("Outside shift hours (7 AM - 7 PM IST)")
        return

    incidents = get_my_triggered_incidents()

    if not incidents:
        print("No incidents assigned to me")
        return

    now = datetime.now(timezone.utc)

    for incident in incidents:
        incident_id = incident["id"]
        created_at = parser.parse(incident["created_at"])

        diff_minutes = (now - created_at).total_seconds() / 60

        if diff_minutes >= 6:
            print(f"Acking {incident_id} (age: {diff_minutes:.2f} mins)")
            acknowledge_incident(incident_id)
        else:
            print(f"Skipping {incident_id} (only {diff_minutes:.2f} mins old)")


if __name__ == "__main__":
    main()
