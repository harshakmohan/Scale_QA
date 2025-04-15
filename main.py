'''
Types of checks:
- If a bb takes up entire image or a large portion of the image, it's probably wrong.
- If there are multiple duplicates within a close area, it's probably wrong. How many duplicate traffic signs do you see in the world?
- If the bounding box is too small, be suspicious.
- If bboxes are overlapping, flag it.
- can i do some consistency check for size of labels across the dataset? how do i account for image scale?
To Do: Look at the data directly and see if there are any other checks that could be done.

  "params": {
    "attachment": "https://observesign.s3-us-west-2.amazonaws.com/traffic_sign_5.jpg",
    "attachment_type": "image",
    "objects_to_annotate": [
      "traffic_control_sign",
      "construction_sign",
      "information_sign",
      "policy_sign",
      "non_visible_face"
    ],
    So, we know the objects that we want to annotate in this image.
'''

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
for task in tasks:
    print(task["task_id"])


### Test Bed ###
task_id = tasks[3]["task_id"]
qa_test = QA(task_id)
