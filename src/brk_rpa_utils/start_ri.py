from loguru import logger

from brk_rpa_utils import get_credentials


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
