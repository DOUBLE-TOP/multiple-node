import time
import random

from eth_account.messages import encode_defunct
from web3 import AsyncWeb3

from src.base_client import BaseClient
from src.models.account import Account
from src.models.exceptions import SoftwareException, TokenException
from src.utils.logger import Logger


class MultipleNode(Logger, BaseClient):

    def __init__(self, account: Account):
        Logger.__init__(self)
        BaseClient.__init__(self, account)
        self.account = account

    async def generate_signature(self) -> (str, str):
        w3 = AsyncWeb3()
        date_string, nonce = await self.generate_timestamp_nonce()
        message = f"www.multiple.cc wants you to sign in with your Ethereum account: {self.account.public_key}\n\t     \nmessage:\nwebsite: www.multiple.cc\nwalletaddress: {self.account.public_key}\ntimestamp: {date_string}\nNonce: {nonce}"
        text_hex = "0x" + message.encode('utf-8').hex()
        text_encoded = encode_defunct(hexstr=text_hex)

        signed_message = w3.eth.account.sign_message(text_encoded, private_key=self.account.private_key)

        return message, signed_message.signature.hex()

    @staticmethod
    async def generate_timestamp_nonce():
        current_time = int(time.time())

        date_string = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))
        nonce = current_time * 1000 + random.randint(1000, 9999)

        return date_string, nonce

    async def login(self, force=False):
        if 'None' in self.account.token or force:
            self.logger_msg(self.account, f"User is not logged in or token was expired.", 'success')
            web_token = await self.wallet_login()
            await self.extension_login(web_token)

    async def wallet_login(self):
        url = 'https://api.app.multiple.cc/WalletLogin'

        sec_ch_ua, sec_ua_platform = await self.generate_headers()
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.8',
            'authorization': 'Bearer',
            'content-type': 'application/json',
            'origin': 'https://www.app.multiple.cc',
            'priority': 'u=1, i',
            'referer': 'https://www.app.multiple.cc/',
            'sec-ch-ua': f'{sec_ch_ua}',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': f'"{sec_ua_platform}"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'sec-gpc': '1',
            'user-agent': self.account.user_agent
        }

        message, signature = await self.generate_signature()
        payload = {
            "walletAddr": self.account.public_key,
            "message": message,
            "signature": signature
        }

        try:
            response = await self.make_request(method="POST", url=url, headers=headers,
                                               json=payload, module_name='Login on Web')

            self.logger_msg(self.account, f"User logged in successfully on Web.", 'success')
            return f"Bearer {response['data']['token']}"
        except SoftwareException as e:
            self.logger_msg(self.account,
                            f"User was not logged in on Web. Error - {e}", 'error')
            await self.session.close()
            exit(1)

    async def extension_login(self, web_token):
        url = "https://api.app.multiple.cc/ChromePlugin/Login"

        sec_ch_ua, sec_ua_platform = await self.generate_headers()
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': f'{web_token}',
            'content-type': 'application/json',
            'origin': 'chrome-extension://ciljbjmmdhnhgbihlcohoadafmhikgib',
            'priority': 'u=1, i',
            'sec-ch-ua': sec_ch_ua,
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': sec_ua_platform,
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'none',
            'sec-gpc': '1',
            'user-agent': self.account.user_agent
        }

        try:
            response = await self.make_request(method="POST", url=url, headers=headers,
                                               module_name='Extension Login on Chrome')

            self.logger_msg(self.account, f"Extension Login on Chrome successfully.", 'success')
            self.account.token = f"Bearer {response['data']['token']}"
        except SoftwareException as e:
            self.logger_msg(self.account,
                            f"Extension Login on Chrome is not successful. Error - {e}", 'error')
            await self.session.close()
            exit(1)

    async def keep_alive(self):
        try:
            url = 'https://api.app.multiple.cc/ChromePlugin/KeepAlive'
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'en-US,en;q=0.9',
                'authorization': self.account.token,
                'content-length': '0',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'chrome-extension://ciljbjmmdhnhgbihlcohoadafmhikgib',
                'priority': 'u=1, i',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'none',
                'sec-gpc': '1',
                'user-agent': self.account.user_agent
            }
            await self.make_request(method="POST", url=url, headers=headers, module_name='Record Keep Alive')

            self.logger_msg(self.account, f"Keep alive recorded!", 'success')
        except SoftwareException as e:
            self.logger_msg(self.account,
                            f"Keep alive was not recorded by some reasons. Error - {e}", 'warning')
