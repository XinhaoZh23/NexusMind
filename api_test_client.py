import uuid

import requests

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"
UPLOAD_URL = f"{BASE_URL}/upload"
CHAT_URL = f"{BASE_URL}/chat"
TEST_FILE = "test.txt"


def run_test():
    """
    Runs a sequence of API calls to test the upload and chat functionality.
    """
    # 1. Generate a unique brain_id for this test run
    brain_id = str(uuid.uuid4())
    print(f"--- Starting test with Brain ID: {brain_id} ---\n")

    # 2. Test the /upload endpoint
    print("--- Testing POST /upload ---")
    try:
        with open(TEST_FILE, "rb") as f:
            files = {"file": (TEST_FILE, f, "text/plain")}
            data = {"brain_id": brain_id}

            response = requests.post(UPLOAD_URL, files=files, data=data)

            print(f"Status Code: {response.status_code}")
            print(f"Response JSON: {response.json()}")
            response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during upload: {e}")
        return

    print("\n--- Upload test successful ---\n")

    # 3. Test the /chat endpoint
    print("--- Testing POST /chat ---")
    try:
        chat_payload = {
            "question": "What is the meaning of life?",
            "brain_id": brain_id,
        }
        response = requests.post(CHAT_URL, json=chat_payload)

        print(f"Status Code: {response.status_code}")
        print(f"Response JSON: {response.json()}")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during chat: {e}")
        return

    print("\n--- Chat test successful ---")
    print("\n--- End-to-end test finished ---")


if __name__ == "__main__":
    run_test()
