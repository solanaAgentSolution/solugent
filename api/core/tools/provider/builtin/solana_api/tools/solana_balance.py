from typing import Any
from solana.rpc.api import Client
from solders.pubkey import Pubkey  # type: ignore
from solana.rpc.types import TokenAccountOpts
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class SolanaBalanceTool(BuiltinTool):
    """
    Tool for checking the balance of a specified Solana account.
    """

    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> ToolInvokeMessage:
        account = tool_parameters.get("account")
        token_address = tool_parameters.get("token_address", None)
        commitment = tool_parameters.get("commitment", "confirmed")

        solana_rpc_url = self.runtime.credentials["solana_rpc_url"]

        account = Pubkey.from_string(account)
        client = Client(solana_rpc_url)
        try:
            if token_address:
                opts = TokenAccountOpts(mint=Pubkey.from_string(token_address))
                balance = client.get_token_accounts_by_owner_json_parsed(owner=account, opts=opts, commitment=commitment)
                balance_value = balance.value[0].account.data.parsed['info']['tokenAmount']['uiAmount']
            else:
                balance = client.get_balance(account, commitment=commitment)
                balance_value = balance.value / 10**9
            return self.create_text_message(text=f"Balance for {account}: {balance_value} SOL")
        except Exception as e:
            return self.create_text_message(text=f"Error fetching balance: {str(e)}")
