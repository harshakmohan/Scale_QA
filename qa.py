import enum
import scaleapi

API_KEY = "live_b1c5a645ea7e418a969b42b134e2d2d6"

class Result(enum.Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"

class QA:
    def __init__(self, task_id: str):
        self.client = scaleapi.ScaleClient(API_KEY)
        self.task_id = task_id

        self.data = self.client.get_task(task_id).as_dict()
        self.img_url = self.data["params"]["attachment"]
        self.annotations = self.data["response"].get("annotations", [])
        
        self.result_state = Result.PASS # Default to pass
        self.qa_results = {} # Dict to store result of every quality check

        print(f'Task ID: {self.task_id}')
        print(f'Image URL: {self.img_url}')
        # print(f"Annotations: {self.annotations}")

        self._run_qa()

    def _update_result_state(self, qa_result_output: Result):
        '''
        Updates result_state depending on output of individual quality check.
        Rules:
        - Any FAIL makes overall result FAIL
        - If no FAIL, and at least 1 WARN, overall result is WARN
        - Else, overall result is PASS
        '''
        if self.result_state == Result.FAIL:
            return
        if qa_result_output == Result.FAIL:
            self.result_state = Result.FAIL
        elif qa_result_output == Result.WARN and self.result_state == Result.PASS:
            self.result_state = Result.WARN

    def _run_qa(self):
        if not self._is_completed():
            # If task is not completed, do something useful
            print(f"Task not completed. Skipping...")
            pass

        if self._is_annotations():
            # If we have non-zero number of annotations, run the QA checks.
            print(f"Running QA Checks...")
            _ = self.traffic_light_background_color()
            print(f'Completed QA Checks: {self.result_state.value}')
            print(self.qa_results)
        else:
            # If we have zero annotations, run separate stage of qa checks specifically for images that have no annotations
            pass

    def _is_completed(self) -> bool:
        return self.data["status"] == "completed"

    def _is_annotations(self) -> bool:
        if self.annotations and len(self.annotations) > 0:
            return True
        else:
            return False

    ### Obvious Checks (low-hanging fruit) ###
    def traffic_light_background_color(self, aspect_ratio = 1.5):
        '''
        Background color of traffic lights should be "Other"
        - We get the `traffic_control_sign` field, but this also includes other things.
        - So let's first find all `traffic_control_sign`, then filter by aspect ratio (traffic lights are generally long and narrow)
        - Then check if background color is "other"
        '''
        # Get all traffic_control_sign annotations for this image
        traffic_control_signs = [annotation for annotation in self.annotations if annotation["label"] == "traffic_control_sign"]

        # We are interested in traffic lights specifically. Traffic lights are long and narrow, and (in the USA) they are almost always oriented vertically and perpendicularly to the ground
        # traffic_control_signs include traffic lights, stop signs, yield signs, merge signs, etc...
        # Filter out traffic lights from traffic_control_signs list by some heuristic aspect ratio
        traffic_lights = []
        for annotation in traffic_control_signs:
            width = annotation.get("width", 0)
            height = annotation.get("height", 0)
            if width == 0 or height == 0:
                # We should never have 1D bounding boxes
                self._update_result_state(Result.FAIL)
                return Result.FAIL
            ratio = height/width # aspect ratio of current bbox
            if ratio >= aspect_ratio:
                traffic_lights.append(annotation)
        # Now check background color for the filtered annotations
        qa_result = Result.PASS # Default to pass. This gets set to FAIL conditionally below
        for annotation in traffic_lights:
            bg_color = annotation.get("attributes", {}).get("background_color", "").lower()
            if bg_color != "other":
                # Return FAIL
                qa_result = Result.FAIL
                self.qa_results["traffic_light_background_color"] = qa_result.value
                self._update_result_state(Result.FAIL)
                return qa_result
        self.qa_results["traffic_light_background_color"] = qa_result.value
        return qa_result
