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
        self.qa_results = {} # Map check names to list of (Result, msg str)

        print(f'Task ID: {self.task_id}')
        print(f'Image URL: {self.img_url}')
        # print(f"Annotations: {self.annotations}")

        self._run_qa()

    def _add_qa_result(self, qa_test_key: str, result: Result, msg: str):
        if qa_test_key not in self.qa_results:
            self.qa_results[qa_test_key] = []
        self.qa_results[qa_test_key].append((result, msg))

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
            return

        if self._is_annotations():
            # If we have non-zero number of annotations, run the QA checks.
            print(f"Running QA Checks...")
            self.traffic_light_background_color()
            self.check_truncation()
            print(f'Completed QA Checks: {self.result_state.value}')
            print(self.qa_results)
        else:
            print(f"No annotations. Skipping...")
            # If we have zero annotations, run separate stage of qa checks specifically for images that have no annotations
            return

    def _is_completed(self) -> bool:
        return self.data["status"] == "completed"

    def _is_annotations(self) -> bool:
        return bool(self.annotations)

    ### QA Checks ###
    def traffic_light_background_color(self, aspect_ratio = 1.5):
        '''
        Background color of traffic lights should be "other"
        - We get the `traffic_control_sign` field, but this also includes other things.
        - So let's first find all `traffic_control_sign`, then filter by aspect ratio (traffic lights are generally long and narrow)
        - Then check if background color is "other"
        '''
        # Get all traffic_control_sign annotations for this image
        traffic_control_signs = [annotation for annotation in self.annotations if annotation["label"] == "traffic_control_sign"]

        # We are interested in traffic lights specifically. Traffic lights are long and narrow, and (in the USA) they are almost always oriented vertically and perpendicularly to the ground.
        # traffic_control_signs include traffic lights, stop signs, yield signs, merge signs, etc...
        # Filter out traffic lights from traffic_control_signs list by some heuristic aspect ratio.
        traffic_lights = []
        for annotation in traffic_control_signs:
            width = annotation.get("width", 0)
            height = annotation.get("height", 0)
            if width == 0 or height == 0:
                # We should never have 1D bounding boxes.
                self._update_result_state(Result.FAIL)
                self._add_qa_result("traffic_light_background_color", Result.FAIL, "1d bbox error: width or height is zero")
                # Loop through remaining traffic_control_signs
                continue

            ratio = height / width  # aspect ratio of current bbox
            if ratio >= aspect_ratio:
                traffic_lights.append(annotation)

        # Check background color
        for annotation in traffic_lights:
            bg_color = annotation.get("attributes", {}).get("background_color", "").lower()
            if bg_color != "other":
                self._update_result_state(Result.WARN)
                self._add_qa_result(
                    "traffic_light_background_color",
                    Result.WARN,
                    f"background color is '{bg_color}' instead of 'other'"
                )
        # If no failures or warnings for "traffic_light_background_color", record as pass
        if ("traffic_light_background_color" not in self.qa_results or 
            len(self.qa_results["traffic_light_background_color"]) == 0):
            self._add_qa_result(
                "traffic_light_background_color",
                Result.PASS,
                ""
            )

    def check_truncation(self):
        '''
        Check if truncation values are consistent with bounding box position:
        - If bbox is not touching image borders, truncation should be 0%
        - If truncation is marked but box isn't at border, flag as error
        '''
        for annotation in self.annotations:
            # Get bbox coordinates and image dimensions
            x = annotation.get("left", 0)
            y = annotation.get("top", 0)
            width = annotation.get("width", 0)
            height = annotation.get("height", 0)
            img_width = self.data["params"].get("width", 0)
            img_height = self.data["params"].get("height", 0)
            
            # Get truncation value
            truncation = annotation.get("attributes", {}).get("truncation", "0%")
            truncation_value = int(truncation.strip('%'))
            
            # Check if bbox touches any image border
            touches_border = (
                abs(x) <= 1 or  # Left border
                abs(y) <= 1 or  # Top border
                abs(x + width - img_width) <= 1 or  # Right border
                abs(y + height - img_height) <= 1    # Bottom border
            )
            
            if not touches_border and truncation_value > 0:
                self._update_result_state(Result.FAIL)
                self._add_qa_result(
                    "truncation_check",
                    Result.FAIL,
                    f"Annotation has {truncation_value}% truncation but doesn't touch image border"
                )
            elif touches_border and truncation_value == 0:
                self._update_result_state(Result.WARN)
                self._add_qa_result(
                    "truncation_check",
                    Result.WARN,
                    f"Annotation touches image border but has 0% truncation"
                )
                
        # If no failures or warnings, record as pass
        if ("truncation_check" not in self.qa_results or 
            len(self.qa_results["truncation_check"]) == 0):
            self._add_qa_result(
                "truncation_check",
                Result.PASS,
                ""
            )
