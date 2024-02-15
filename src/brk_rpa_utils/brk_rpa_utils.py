import io
import json
import re
import secrets
import shutil
import string
import subprocess
import time
from pathlib import Path

import pandas as pd
import pendulum
import win32com.client  # pywin32
from bs4 import BeautifulSoup  # BeautifulSoup4
from loguru import logger


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


def generate_new_password(char_count: int):
    alphabet = string.ascii_letters + string.digits
    password = []

    # Ensure at least one letter and one digit
    password.append(secrets.choice(string.ascii_letters))
    password.append(secrets.choice(string.digits))

    # Fill the rest of the length with random characters
    for _ in range(char_count - 2):
        password.append(secrets.choice(alphabet))

    # Shuffle the password to mix letters and digits
    secrets.SystemRandom().shuffle(password)

    return "".join(password)


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


def parse_ri_html_report_to_dataframe(mhtml_path) -> None:
    """
    Parses an mhtml file downloaded from Rollobaseret Indgang.
    The default download calls the file xls, but it is a kind of html file.

    ## Usage
    mhtml_path = Path(folder_data_session / 'test.html')

    df_mhtml = parse_ri_html_report_to_dataframe(mhtml_path)
    """
    try:
        # Read MHTML file
        with open(mhtml_path, encoding="utf-8") as file:
            content = file.read()

        # Find the HTML part of the file
        match = re.search(r"<html.*<\/html>", content, re.DOTALL)
        if not match:
            msg = "No HTML content found in the file"
            raise ValueError(msg)
        html_content = match.group(0)

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all tables within the parsed HTML
        tables = soup.find_all("table")
        if not tables:
            msg = "No tables found in the HTML content"
            raise ValueError(msg)

        # Select the largest table based on character count
        largest_table = max(tables, key=lambda table: len(str(table)))

        # Convert the largest HTML table to a pandas DataFrame
        df_mhtml = pd.read_html(io.StringIO(str(largest_table)), decimal=",", thousands=".", header=None)
        if not df_mhtml:
            msg = "Failed to parse the largest table into a DataFrame"
            raise ValueError(msg)

        df_mhtml = df_mhtml[0]
        df_mhtml.columns = df_mhtml.iloc[0]
        df_mhtml = df_mhtml.drop(0)
        df_mhtml.reset_index(drop=True, inplace=True)
        df_mhtml.rename(columns={"Slut F-periode": "date", "Lønart": "lonart", "Antal": "antal"}, inplace=True)

        # Convert 'date' column to datetime
        df_mhtml["date"] = pd.to_datetime(df_mhtml["date"], format="%d%m%Y")
        df_mhtml["antal"] = pd.to_numeric(df_mhtml["antal"])
        return df_mhtml

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None


def start_opus(pam_path, user, sapshcut_path) -> None:
    """
    Unpack like so:
    username, password = get_credentials(pam_path, user, fagsystem="opus")

    Starts Opus using sapshcut.exe and credentials from PAM.

    load_dotenv()
    sapshcut_path = Path(os.getenv("SAPSHCUT_PATH"))

    The <user>.json file should have the structure:

    {
    "ad": { "username": "x", "password": "x" },
    "opus": { "username": "x", "password": "x" },
    "rollebaseretindgang": { "username": "x", "password": "x" }
    }
    """

    # unpacking
    username, password = get_credentials(pam_path, user, fagsystem="opus")

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


def start_ri(pam_path, user, ri_url, playwright) -> None:
    """
    Starts s browser pointed to ri_url (fx https://portal.kmd.dk/irj/portal)
    and logs into Rollebaseret Indgang (RI) using  and credentials from PAM.

    load_dotenv()
    ri_url = os.getenv("RI_PATH")

    from playwright.sync_api import Playwright

    The <user>.json file should have the structure:

    {
    "ad": { "username": "x", "password": "x" },
    "opus": { "username": "x", "password": "x" },
    "rollebaseretindgang": { "username": "x", "password": "x" }
    }
    """

    username, password = get_credentials(pam_path, user, fagsystem="rollebaseretindgang")

    if not username or not password:
        logger.error("Failed to retrieve credentials for robot", exc_info=True)
        return None

    try:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 2560, "height": 1440})
        page = context.new_page()
        page.goto(ri_url)
        page.get_by_placeholder("Brugernavn").click()
        page.get_by_placeholder("Brugernavn").fill(username)
        page.get_by_placeholder("Brugernavn").press("Tab")
        page.get_by_placeholder("Password").click()
        page.get_by_placeholder("Password").fill(password)
        page.get_by_role("button", name="Log på").click()
        page.get_by_text("Lønsagsbehandling").click()

        return page, context, browser

    except Exception as e:
        msg = f"An error occurred while logging into the portal: {e}"
        logger.error(msg, exc_info=True)
        return None
