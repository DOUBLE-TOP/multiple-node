from web3 import Web3

from src.utils.file_manager import read_account


class Account:
    def __init__(self, private_key, proxy):
        super().__init__()
        self.private_key = private_key
        self.public_key = Web3().eth.account.from_key(self.private_key.replace('0x', '')).address
        self.proxy = proxy
        self.token = None
        self.user_agent = None
        self.running_time = None

    async def get_detailed_dict_for_account(self):
        data = await read_account(self.public_key)
        if len(data) > 0:
            self.private_key = data.get("Private_key") or None
            self.public_key = data.get("Public_key") or None
            self.proxy = data.get("Proxy") or None
            self.token = data.get("Token") or None
            self.user_agent = data.get("User_Agent") or None
            self.running_time = data.get("Running_Time") or None

    async def account_to_dict(self) -> dict:
        return {
            "Private_key": self.private_key,
            "Public_key": self.public_key,
            "Proxy": self.proxy,
            "Token": self.token,
            "User_Agent": self.user_agent,
            "Running_Time": self.running_time
        }


async def default_dict_to_account(data) -> Account:
    return Account(private_key=data.get('Private_key'), proxy=data.get('Proxy'))
