import requests
from requests.auth import HTTPBasicAuth
from qa import QA
import json
from collections import defaultdict

API_KEY = "live_b1c5a645ea7e418a969b42b134e2d2d6"
PROJECT_NAME = "Traffic Sign Detection"
BASE_URL = "https://api.scale.com/v1/tasks"
LIMIT = 100

def format_qa_results(task_id: str, qa_instance: QA) -> dict:
    """Format QA results for a single task into the desired JSON structure"""
    # Initialize lists for passed and failed checks
    passed_checks = []
    failed_checks = []
    warnings = []
    
    # Sort results into appropriate lists
    for check_name, results in qa_instance.qa_results.items():
        for result, message in results:
            result_entry = {
                "check_name": check_name,
                "message": message
            }
            if result.value == "pass":
                passed_checks.append(result_entry)
            elif result.value == "fail":
                failed_checks.append(result_entry)
            else:  # warn
                warnings.append(result_entry)
    
    # Create formatted output
    return {
        "task_id": task_id,
        "attachment": qa_instance.img_url,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "warnings": warnings,
        "overall_score": qa_instance.result_state.value
    }

def main():
    # Fetch tasks
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
    print("Running QA on available tasks...")

    qa_results = []
    for task in tasks:
        task_id = task["task_id"]
        qa = QA(task_id)
        qa_results.append(format_qa_results(task_id, qa))

    total_tasks = len(qa_results)
    status_counts = defaultdict(int)
    for result in qa_results:
        status_counts[result["overall_score"]] += 1

    output = {
        "summary": {
            "total_tasks": total_tasks,
            "pass_count": status_counts["pass"],
            "warn_count": status_counts["warn"],
            "fail_count": status_counts["fail"]
        },
        "results": qa_results
    }

    with open('qa_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\nQA Complete!")
    print(f"Total tasks processed: {total_tasks}")
    print(f"Pass: {status_counts['pass']}")
    print(f"Warn: {status_counts['warn']}")
    print(f"Fail: {status_counts['fail']}")
    print("Results written to qa_results.json")

if __name__ == "__main__":
    main()

