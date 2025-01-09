import copy
import random
import asyncio

from src.multiple_node import MultipleNode
from src.models.exceptions import TokenException
from src.utils.logger import Logger


from src.models.account import Account, default_dict_to_account
from src.utils.file_manager import read_accounts, update_variables_in_file


class Runner(Logger):

    @staticmethod
    async def get_accounts() -> list[Account]:
        accounts = []
        accounts_data = await read_accounts()
        for account in accounts_data:
            accounts.append(await default_dict_to_account(account))

        return accounts

    async def custom_sleep(self, account: Account):
        duration = random.randint(540, 660)
        self.logger_msg(account, f"💤 Sleeping for {duration} seconds", 'success')
        await asyncio.sleep(duration)

    async def run_account(self, accounts: list[Account], index):
        self.logger_msg(accounts[index],
                        f"Task for account {accounts[index].public_key} was started.", 'success')
        account = copy.deepcopy(accounts[index])
        await account.get_detailed_dict_for_account()
        await update_variables_in_file(self, account, await account.account_to_dict())
        self.logger_msg(account, f"Account details - {await account.account_to_dict()}", 'success')

        node = MultipleNode(account)
        await node.login()
        await update_variables_in_file(self, account, await account.account_to_dict())
        while True:
            try:
                await node.keep_alive()
                running_time_hours = await node.get_total_running_time()
                self.logger_msg(account,
                                f"Total running time in hours - {running_time_hours}", 'success')
                await self.custom_sleep(account)
            except TokenException as e:
                self.logger_msg(account, f"Token is incorrect. Error - {e}", 'warning')
                await node.login(force=True)
                await update_variables_in_file(self, account, await account.account_to_dict())

    async def run_accounts(self):
        self.logger_msg(None, "Collect accounts data", 'success')
        accounts = await self.get_accounts()
        tasks = []

        self.logger_msg(None, "Create tasks for accounts", 'success')
        for index, account in enumerate(accounts):
            tasks.append(asyncio.create_task(self.run_account(accounts, index)))

        self.logger_msg(None, "Execute tasks for accounts", 'success')
        await asyncio.gather(*tasks, return_exceptions=True)
