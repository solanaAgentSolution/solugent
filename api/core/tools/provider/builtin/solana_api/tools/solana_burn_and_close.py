import logging
from typing import Any, List

from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price  # type: ignore
from solders.pubkey import Pubkey  # type: ignore
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import BurnParams, CloseAccountParams, burn, close_account

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool

logger = logging.getLogger(__name__)


class BurnAndCloseTool(BuiltinTool):
    """
    Tool for burning tokens and closing a specified Solana token account.
    """

    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> ToolInvokeMessage:
        token_account = tool_parameters.get("token_account")
        private_key = tool_parameters.get("private_key")
        solana_rpc_url = self.runtime.credentials["solana_rpc_url"]

        try:
            client = Client(solana_rpc_url)
            wallet = Keypair.from_base58_string(private_key)
            wallet_address = wallet.pubkey()

            token_account_pubkey = Pubkey.from_string(token_account)
            token_balance = int(client.get_token_account_balance(token_account_pubkey).value.amount)
            logger.info(f"Token Balance for {token_account}: {token_balance}")

            owner = wallet_address
            recent_blockhash = client.get_latest_blockhash().value.blockhash

            transaction = Transaction()
            transaction.fee_payer = owner
            transaction.recent_blockhash = recent_blockhash

            if token_balance > 0:
                mint_str = client.get_account_info_json_parsed(token_account_pubkey).value.data.parsed['info']['mint']
                mint = Pubkey.from_string(mint_str)
                burn_instruction = burn(
                    BurnParams(
                        program_id=TOKEN_PROGRAM_ID,
                        account=token_account_pubkey,
                        mint=mint,
                        owner=owner,
                        amount=token_balance
                    )
                )
                transaction.add(burn_instruction)

            close_account_instruction = close_account(
                CloseAccountParams(
                    program_id=TOKEN_PROGRAM_ID,
                    account=token_account_pubkey,
                    dest=owner,
                    owner=owner
                )
            )
            transaction.add(set_compute_unit_price(100_000))
            transaction.add(set_compute_unit_limit(100_000))
            transaction.add(close_account_instruction)

            transaction.sign(wallet)
            txn_sig = client.send_transaction(transaction, wallet, opts=TxOpts(skip_preflight=True)).value
            logger.info(f"Transaction Signature for {token_account}: {txn_sig}")

            return self.create_text_message(text=f"Transaction successful: {txn_sig}")
        except Exception as e:
            logger.error(f"Error processing token account {token_account}: {e}")
            return self.create_text_message(text=f"Error processing token account {token_account}: {str(e)}")

    @staticmethod
    def process_multiple_accounts(agent, token_accounts: List[str]) -> None:
        """
        Processes multiple token accounts by burning and closing each one.

        Parameters:
        agent: The agent instance containing wallet and RPC configuration.
        token_accounts: List of token account public keys as strings.
        """
        for token_account in token_accounts:
            try:
                BurnAndCloseTool.burn_and_close_account(agent, token_account)
            except Exception as e:
                logger.error(f"Error processing token account {token_account}: {e}")