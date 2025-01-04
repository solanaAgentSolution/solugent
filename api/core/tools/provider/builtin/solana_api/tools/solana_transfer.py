import logging
import math
from typing import Any, Optional

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.pubkey import Pubkey  # type: ignore
from solders.keypair import Keypair
from solders.transaction import Transaction  # type: ignore
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address, transfer_checked

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool
LAMPORTS_PER_SOL = 1e9

logger = logging.getLogger(__name__)


class SolanaTransferTool(BuiltinTool):
    """
    Tool for transferring SOL or SPL tokens from one account to another on the Solana blockchain.
    """

    async def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> ToolInvokeMessage:
        to_account = tool_parameters.get("to_account")
        amount = tool_parameters.get("amount")
        mint = tool_parameters.get("mint", None)
        private_key = tool_parameters.get("private_key")
        solana_rpc_url = self.runtime.credentials["solana_rpc_url"]

        client = AsyncClient(solana_rpc_url)
        wallet = Keypair.from_base58_string(private_key)
        wallet_address = wallet.pubkey()

        try:
            if mint:
                signature = await self.transfer_spl_tokens(client, wallet, wallet_address, Pubkey.from_string(to_account), Pubkey.from_string(mint), amount)
                token_identifier = str(mint)
            else:
                signature = await self.transfer_native_sol(client, wallet, wallet_address, Pubkey.from_string(to_account), amount)
                token_identifier = "SOL"

            await self.confirm_transaction(client, signature)

            result = {
                "signature": signature,
                "from_address": str(wallet_address),
                "to_address": str(to_account),
                "amount": amount,
                "token": token_identifier
            }

            return self.create_text_message(text=f"Transfer successful: {result}")
        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            return self.create_text_message(text=f"Transfer failed: {str(e)}")

    @staticmethod
    async def transfer_native_sol(client: AsyncClient, wallet: Keypair, from_address: Pubkey, to: Pubkey, amount: float) -> str:
        transaction = Transaction()
        transaction.add(
            Transaction(
                from_pubkey=from_address,
                to_pubkey=to,
                lamports=int(amount * LAMPORTS_PER_SOL)
            )
        )

        result = await client.send_transaction(
            transaction,
            [wallet],
            opts={
                "skip_preflight": False,
                "preflight_commitment": Confirmed,
                "max_retries": 3
            }
        )

        return result.value.signature

    @staticmethod
    async def transfer_spl_tokens(client: AsyncClient, wallet: Keypair, from_address: Pubkey, recipient: Pubkey, spl_token: Pubkey, amount: float) -> str:
        spl_client = AsyncToken(client, spl_token, TOKEN_PROGRAM_ID, from_address)

        mint = await spl_client.get_mint_info()
        if not mint.is_initialized:
            raise ValueError("Token mint is not initialized.")

        token_decimals = mint.decimals
        if amount < 10 ** -token_decimals:
            raise ValueError("Invalid amount of decimals for the token.")

        tokens = math.floor(amount * (10 ** token_decimals))

        payer_ata = get_associated_token_address(from_address, spl_token)
        recipient_ata = get_associated_token_address(recipient, spl_token)

        payer_account_info = await spl_client.get_account_info(payer_ata)
        if not payer_account_info.is_initialized:
            raise ValueError("Payer's associated token account is not initialized.")
        if tokens > payer_account_info.amount:
            raise ValueError("Insufficient funds in payer's token account.")

        recipient_account_info = await spl_client.get_account_info(recipient_ata)
        if not recipient_account_info.is_initialized:
            raise ValueError("Recipient's associated token account is not initialized.")

        transfer_instruction = transfer_checked(
            amount=tokens,
            decimals=token_decimals,
            program_id=TOKEN_PROGRAM_ID,
            owner=from_address,
            source=payer_ata,
            dest=recipient_ata,
            mint=spl_token,
        )

        transaction = Transaction().add(transfer_instruction)
        response = await client.send_transaction(
            transaction,
            [wallet],
            opts={
                "skip_preflight": False,
                "preflight_commitment": Confirmed,
                "max_retries": 3
            }
        )
        return response["result"]

    @staticmethod
    async def confirm_transaction(client: AsyncClient, signature: str) -> None:
        await client.confirm_transaction(signature, commitment=Confirmed)
