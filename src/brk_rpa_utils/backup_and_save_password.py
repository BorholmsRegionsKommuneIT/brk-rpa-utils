import json
import shutil
from pathlib import Path

import pendulum


def backup_and_save_password(password: str, pam_path: Path, user: str, fagsystem: str) -> None:
    # Path to the user's pam json file
    user_pam_json_path = Path(pam_path / user / f"{user}.json")

    # Backup the existing JSON file
    backup_filename = f"{user} - backup {pendulum.now().strftime('%Y-%m-%d-%H-%M-%S')}.json"

    backup_path = user_pam_json_path.parent / backup_filename
    shutil.copy(user_pam_json_path, backup_path)

    # Update the password in the JSON file
    if user_pam_json_path.exists():
        with open(user_pam_json_path) as file:
            data = json.load(file)

        if fagsystem in data:
            data[fagsystem]["password"] = password

        with open(user_pam_json_path, "w") as file:
            json.dump(data, file, indent=4)
    else:
        msg = f"The file {user_pam_json_path} does not exist."
        raise FileNotFoundError(msg)
        return None
