import os
import pytest
from typing import Callable, Dict, List
from urllib.parse import urljoin

from playwright.sync_api import Page, expect


@pytest.fixture
def ophub_url() -> str:
    url = os.environ.get('OPHUB_URL', None)
    if url is None:
        raise ValueError('OPHUB_URL environment variable is not set')
    return url

@pytest.fixture
def ophub_username() -> str:
    username = os.environ.get('OPHUB_USERNAME', None)
    if username is None:
        raise ValueError('OPHUB_USERNAME environment variable is not set')
    return username

@pytest.fixture
def ophub_password() -> str:
    password = os.environ.get('OPHUB_PASSWORD', None)
    if password is None:
        raise ValueError('OPHUB_PASSWORD environment variable is not set')
    return password

@pytest.fixture
def ophub_user_is_admin() -> bool:
    return os.environ.get('OPHUB_USER_IS_ADMIN', '0') == '1'

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args) -> Dict:
    ignore_https_errors = os.environ.get('OPHUB_IGNORE_HTTPS_ERRORS', '0') == '1'
    return {
        **browser_context_args,
        "ignore_https_errors": ignore_https_errors
    }

@pytest.fixture
def ophub_has_ep_weave() -> bool:
    return os.environ.get('OPHUB_SERVICE_EP_WEAVE', '') in ('1', 'yes', 'true')

@pytest.fixture
def ophub_has_nbsearch() -> bool:
    return os.environ.get('OPHUB_SERVICE_NBSEARCH', '') in ('1', 'yes', 'true')

@pytest.fixture
def ophub_has_jenkins() -> bool:
    return os.environ.get('OPHUB_SERVICE_JENKINS', '') in ('1', 'yes', 'true')

@pytest.fixture
def ophub_login_to_hub_home(ophub_url, ophub_username, ophub_password) -> Callable[[Page], None]:
    def login(page: Page):
        hub_home_url = urljoin(ophub_url, 'hub/home')
        page.goto(hub_home_url)

        expect(page.locator('#login_submit')).to_be_visible()

        page.locator('#username_input').fill(ophub_username)
        page.locator('#password_input').fill(ophub_password)
        page.click('#login_submit')

        expect(page.locator('#start')).to_be_enabled()
    return login

@pytest.fixture
def ophub_services(ophub_has_ep_weave, ophub_has_nbsearch, ophub_has_jenkins) -> List[str]:
    services = []
    if ophub_has_ep_weave:
        services.append('ep_weave')
    if ophub_has_nbsearch:
        services.append('solr')
    if ophub_has_jenkins:
        services.append('jenkins')
    return services
