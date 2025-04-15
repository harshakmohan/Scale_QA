import scaleapi

API_KEY = "live_b1c5a645ea7e418a969b42b134e2d2d6"

class QA:
    def __init__(self, task_id: str):
        self.client = scaleapi.ScaleClient(API_KEY)
        self.task_id = task_id

        self.data = self.client.get_task(task_id).as_dict()
        self.img_url = self.data["params"]["attachment"]
        self.annotations = self.data["response"] # TODO: Check if annotations is empty
