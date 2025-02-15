import pytest
from typing import List, Callable
from urllib.parse import urljoin

from playwright.sync_api import Page, expect


def test_services_are_enabled(page: Page, ophub_services: List[str], ophub_login_to_hub_home: Callable[[Page], None]):
    ophub_login_to_hub_home(page)

    if len(ophub_services) == 0:
        expect(page.locator('//*[@data-toggle="dropdown" and text()="Services"]')).to_have_count(0)
        return

    page.locator('//*[@data-toggle="dropdown" and text()="Services"]').click()

    for service in ophub_services:
        expect(page.locator(f'//a[text()="{service}"]')).to_have_attribute('href', f'/services/{service}/')
