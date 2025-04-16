import requests
from requests.auth import HTTPBasicAuth
from qa import QA

API_KEY = "live_b1c5a645ea7e418a969b42b134e2d2d6"
PROJECT_NAME = "Traffic Sign Detection"
BASE_URL = "https://api.scale.com/v1/tasks"
LIMIT = 100


tasks = []
start_token = None
while True:
    params = {
        "project": PROJECT_NAME,
        "limit": LIMIT
    }
    if start_token:
        params["start"] = start_token

    response = requests.get(BASE_URL, auth=HTTPBasicAuth(API_KEY, ''), params=params)
    data = response.json()

    tasks.extend(data.get("docs", []))
    start_token = data.get("next")

    if not start_token:
        break

print(f"Total Tasks: {len(tasks)}")
print("Running QA on available tasks..")
for task in tasks:
    task_id = task["task_id"]
    qa = QA(task_id)

