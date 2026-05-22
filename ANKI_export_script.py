import requests
import os
import traceback

print("SCRIPT STARTED")

ANKI_CONNECT_URL = "http://localhost:8765"

DECK_NAME = "TYKRY"
EXPORT_FOLDER = r"C:\Users\akuka\OneDrive\DATA\GitHub_Repos\Solukko"

def anki_request(action, params=None):
    print(f"Calling AnkiConnect action: {action}")

    response = requests.post(ANKI_CONNECT_URL, json={
        "action": action,
        "version": 6,
        "params": params or {}
    })

    print("HTTP status:", response.status_code)
    print("Raw response:", response.text)

    data = response.json()

    if data.get("error"):
        raise Exception(data["error"])

    return data["result"]

def export_deck(deck_name, export_folder):
    os.makedirs(export_folder, exist_ok=True)

    export_path = os.path.join(export_folder, f"{deck_name}.apkg")

    print("Export path:")
    print(export_path)

    anki_request("version")

    anki_request("exportPackage", {
        "deck": deck_name,
        "path": export_path,
        "includeSched": False
    })

    print("DONE!")
    print("Exported to:")
    print(export_path)

if __name__ == "__main__":
    try:
        export_deck(DECK_NAME, EXPORT_FOLDER)
    except Exception:
        print("\nERROR:")
        traceback.print_exc()

    input("\nPress Enter to close...")