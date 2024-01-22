from brk_rpa_utils import get_credentials
import subprocess
import time
from loguru import logger
import win32com.client  # pywin32


def start_opus(pam_path, robot_name, sapshcut_path) -> None:
    """
    Unpack like so:
    username, password = get_credentials(pam_path, robot_name, fagsystem="opus")

    Starts Opus using sapshcut.exe and credentials from PAM.

    load_dotenv()
    sapshcut_path = Path(os.getenv("SAPSHCUT_PATH"))

    The robot_name.json file should have the structure:

    {
    "ad": { "username": "robot_name", "password": "x" },
    "opus": { "username": "robot_name", "password": "x" },
    "rollebaseretindgang": { "username": "robot_name", "password": "x" }
    }
    """

    # unpacking
    username, password = get_credentials(pam_path, robot_name, fagsystem="opus")

    if not username or not password:
        logger.error("Failed to retrieve credentials for robot", exc_info=True)
        return None

    command_args = [
        str(sapshcut_path),
        "-system=P02",
        "-client=400",
        f"-user={username}",
        f"-pw={password}",
    ]

    subprocess.run(command_args, check=False)  # noqa: S603
    time.sleep(3)

    try:
        sap = win32com.client.GetObject("SAPGUI")
        app = sap.GetScriptingEngine
        connection = app.Connections(0)
        session = connection.sessions(0)
        return session

    except Exception:
        logger.error("Failed to start SAP session", exc_info=True)
        return None
