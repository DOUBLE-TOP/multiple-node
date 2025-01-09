import asyncio
import re
import ssl
from abc import ABC
from random import randint

from asyncio.exceptions import TimeoutError as AsyncioTimeoutError
import aiohttp
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector

from src.models.account import Account
from src.models.exceptions import SoftwareException, TokenException
from src.models.user_agents import USER_AGENTS
from src.utils.logger import Logger


class BaseClient(ABC):
    def __init__(self, account: Account):
        self.account = account
        self.session = ClientSession(timeout=aiohttp.ClientTimeout(total=60),
                                     connector=ProxyConnector.from_url(f'{account.proxy}',
                                                                       ssl=ssl.create_default_context(),
                                                                       verify_ssl=True))

    async def make_request(self, method: str = 'GET', url: str = None, params: dict = None, headers: dict = None,
                           data: str = None, json: dict = None, module_name: str = 'Request'):

        total_time = 0
        timeout = 360
        while True:
            try:
                async with self.session.request(
                        method=method, url=url, headers=headers,
                        data=data, params=params, json=json) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        if data['success']:
                            return data
                        else:
                            raise SoftwareException(
                                f"Bad request to {self.__class__.__name__}({module_name}) API: {response}")
                    elif response.status in [400, 401]:
                        raise TokenException(
                            f"Bad request to {self.__class__.__name__}({module_name}) API: {response}")
            except aiohttp.client_exceptions.ServerDisconnectedError as error:
                total_time += 15
                await asyncio.sleep(15)
                if total_time > timeout:
                    raise SoftwareException(
                        f"Bad request to {self.__class__.__name__}({module_name}) Error: {error}")
                self.logger_msg(self.account, f"Request failed due to timeout. Retrying one more time", 'warning')
                continue
            except TokenException as error:
                raise TokenException(f"Bad request to {self.__class__.__name__}({module_name}) Error: {error}")
            except SoftwareException as error:
                raise SoftwareException(f"Bad request to {self.__class__.__name__}({module_name}) Error: {error}")
            except Exception as error:
                if isinstance(error, AsyncioTimeoutError):
                    total_time += 15
                    await asyncio.sleep(15)
                    if total_time > timeout:
                        raise SoftwareException(
                            f"Bad request to {self.__class__.__name__}({module_name}) Error: {error}")
                    self.logger_msg(self.account, f"Request failed due to timeout. Retrying one more time", 'warning')
                    continue
                else:
                    raise SoftwareException(
                        f"{self.__class__.__name__}({module_name}). "
                        f"Request failed due to timeout. Retrying one more time")

    async def generate_headers(self):
        if 'None' in str(self.account.user_agent):
            self.account.user_agent = USER_AGENTS[randint(0, len(USER_AGENTS) - 1)]

        ua_pattern = re.compile(
            r'Mozilla/5.0 \(([^)]+)\) AppleWebKit/([\d.]+) \(KHTML, like Gecko\) Chrome/([\d.]+) Safari/([\d.]+)'
        )
        # Match the User-Agent string
        match = ua_pattern.match(self.account.user_agent)

        # If not matched, raise an exception
        if not match:
            raise ValueError("User-Agent format not recognized")

        # Extract platform and version information
        platform = match.group(1).strip()
        chrome_version = match.group(3).split('.')[0]

        # Calculate platform
        sec_ua_platform = ""
        sec_ch_ua = ""
        if "Windows" in platform:
            sec_ua_platform = "Windows"
            sec_ch_ua = f'"Not/A)Brand";v="8", "Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}"'
        if "Linux" in platform:
            sec_ua_platform = "Linux"
            sec_ch_ua = f'"Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}", "Not-A.Brand";v="99"'
        if "Macintosh" in platform:
            sec_ua_platform = "macOS"
            sec_ch_ua = f'"Not_A Brand";v="8", "Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}"'

        return sec_ch_ua, sec_ua_platform
