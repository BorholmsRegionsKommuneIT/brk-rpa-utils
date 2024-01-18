from brk_rpa_utils import get_credentials
from loguru import logger


def start_ri(pam_path, robot_name, ri_url, Playwright) -> None:
    """
    Starts s browser pointed to ri_url (fx https://portal.kmd.dk/irj/portal)
    and logs into Rollebaseret Indgang (RI) using  and credentials from PAM.

    load_dotenv()
    ri_url = os.getenv("RI_PATH")

    from playwright.sync_api import Playwright

    The robot_name.json file should have the structure:

    {
    "ad": { "username": "robot_name", "password": "x" },
    "opus": { "username": "robot_name", "password": "x" },
    "rollebaseretindgang": { "username": "robot_name", "password": "x" }
    }
    """

    username, password = get_credentials(pam_path, robot_name, fagsystem="rollebaseretindgang")

    if not username or not password:
        logger.error("Failed to retrieve credentials for robot", exc_info=True)
        return None

    try:
        browser = Playwright.chromium.launch(headless=False)
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

    except Exception:
        logger.error("An error occurred while logging into the portal", exc_info=True)
        return None
