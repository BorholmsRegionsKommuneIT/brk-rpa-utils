import json
from pathlib import Path

from loguru import logger


def get_credentials(pam_path, user, fagsystem) -> None:
    """
    Internal function to retrieve credentials.

    pam_path = os.getenv("PAM_PATH")

    Define pam_path in an .env file in the root of your project. Add paths like so:
    SAPSHCUT_PATH=C:/Program Files (x86)/SAP/FrontEnd/SAPgui/sapshcut.exe

    user = getpass.getuser()

    Under the pam_path uri der should be a user.json file with the structure:

    {
    "ad": { "username": "robot00X", "password": "x" },
    "opus": { "username": "jrrobot00X", "password": "x" },
    "rollebaseretindgang": { "username": "jrrobot00X", "password": "x" }
    }
    """
    pass_file = Path(pam_path) / user / f"{user}.json"

    try:
        with open(pass_file) as file:
            json_string = json.load(file)

        username = json_string[fagsystem]["username"]
        password = json_string[fagsystem]["password"]

        return username, password

    except FileNotFoundError:
        logger.error("File not found", exc_info=True)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in file", exc_info=True)
    except Exception:
        logger.error("An error occurred:", exc_info=True)

    return None
