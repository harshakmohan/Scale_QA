import requests
from requests.auth import HTTPBasicAuth
import scaleapi

API_KEY = "live_b1c5a645ea7e418a969b42b134e2d2d6"
PROJECT_NAME = "Traffic Sign Detection"
BASE_URL = "https://api.scale.com/v1/tasks"
LIMIT = 100

client = scaleapi.ScaleClient(API_KEY)

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
for task in tasks:
    print(task["task_id"])
    # Now here, let's injest the task data so we can view it locally and write some quality checks for it
    task_data = client.get_task(task["task_id"])


'''
Types of checks:
- If a bb takes up entire image or a large portion of the image, it's probably wrong.
- If there are multiple duplicates within a close area, it's probably wrong. How many duplicate traffic signs do you see in the world?
- If the bounding box is too small, be suspicious.


'''


