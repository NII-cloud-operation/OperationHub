from urllib.parse import urljoin

from playwright.sync_api import Page, expect


def test_needs_login(page: Page, ophub_url: str):
    page.goto(ophub_url)

    expect(page.locator('#login_submit')).to_be_visible()

    login_url = urljoin(ophub_url, 'hub/login?next=%2Fhub%2F')
    assert login_url == page.url

def test_login_to_hub_home(page: Page, ophub_url: str, ophub_username: str, ophub_password: str):
    hub_home_url = urljoin(ophub_url, 'hub/home')
    page.goto(hub_home_url)

    expect(page.locator('#login_submit')).to_be_visible()

    page.locator('#username_input').fill(ophub_username)
    page.locator('#password_input').fill(ophub_password)
    page.click('#login_submit')

    expect(page.locator('#start')).to_be_enabled()
