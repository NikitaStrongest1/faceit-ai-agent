
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from services.demo_download import download_demo


BASE_DIR = Path(__file__).resolve().parent.parent
BROWSER_PROFILE = BASE_DIR / "faceit_browser_profile"

FACEIT_URL = "https://www.faceit.com"
DOWNLOAD_ENDPOINT = (
    "https://www.faceit.com/api/download/v2/demos/download-url"
)


def get_faceit_auth_cookie(context):
    cookies = context.cookies(FACEIT_URL)

    for cookie in cookies:
        if cookie["name"] == "__Host-FaceitGatewayAuthorization":
            return cookie["value"]

    return None


def get_signed_demo_url(match_id, resource_url):

    with sync_playwright() as playwright:

        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE),
            headless=False
        )

        try:
            page = context.pages[0] if context.pages else context.new_page()

            page.goto(FACEIT_URL, wait_until="domcontentloaded")

            print("\nПроверяем авторизацию FACEIT...")

            auth_cookie = None

            # Ждём появления авторизационной сессии
            for attempt in range(90):
                auth_cookie = get_faceit_auth_cookie(context)

                if auth_cookie:
                    break

                time.sleep(2)

            if not auth_cookie:
                raise Exception(
                    "FACEIT session not found. "
                    "Log in to FACEIT in the opened browser."
                )

            print("FACEIT session found!")

            # Запрос выполняется внутри вкладки FACEIT
            result = page.evaluate(
                """
                async ({ endpoint, auth, matchId, resourceUrl }) => {

                    const requests = [
                        { match_id: matchId },
                        { resource_url: resourceUrl },
                        {
                            match_id: matchId,
                            resource_url: resourceUrl
                        }
                    ];

                    let lastError = "";

                    for (const body of requests) {

                        const response = await fetch(endpoint, {
                            method: "POST",
                            headers: {
                                "Authorization": auth,
                                "Content-Type": "application/json",
                                "Accept": "application/json"
                            },
                            credentials: "include",
                            body: JSON.stringify(body)
                        });

                        const responseText = await response.text();

                        if (response.ok) {
                            try {
                                return JSON.parse(responseText);
                            } catch {
                                throw new Error(
                                    "FACEIT returned invalid JSON"
                                );
                            }
                        }

                        lastError =
                            "HTTP " + response.status + ": " + responseText;

                        if (
                            response.status !== 400 &&
                            response.status !== 422
                        ) {
                            break;
                        }
                    }

                    throw new Error(lastError);
                }
                """,
                {
                    "endpoint": DOWNLOAD_ENDPOINT,
                    "auth": auth_cookie,
                    "matchId": match_id,
                    "resourceUrl": resource_url
                }
            )

            payload = result.get("payload", {})
            signed_url = payload.get("download_url")

            if not signed_url:
                signed_url = result.get("download_url")

            if not signed_url:
                raise Exception(
                    "FACEIT did not return a signed demo URL: "
                    + str(result)
                )

            return signed_url

        finally:
            context.close()


def download_faceit_demo(match_id, resource_url):

    print("\n===== AUTOMATIC FACEIT DEMO DOWNLOAD =====")

    signed_url = get_signed_demo_url(
        match_id,
        resource_url
    )

    print("Signed demo URL received!")
    print("Downloading demo...")

    demo_path = download_demo(
        signed_url,
        match_id
    )

    return demo_path
