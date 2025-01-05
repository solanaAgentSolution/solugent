import logging
from typing import Any, Dict, Optional
import aiohttp
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair  # type: ignore
from solders.transaction import VersionedTransaction  # type: ignore

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool

logger = logging.getLogger(__name__)


class LaunchPumpTool(BuiltinTool):
    """
    Tool for launching a new token on Pump.fun.
    """

    async def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> ToolInvokeMessage:
        token_name = tool_parameters.get("token_name")
        token_ticker = tool_parameters.get("token_ticker")
        description = tool_parameters.get("description")
        image_url = tool_parameters.get("image_url")
        private_key = tool_parameters.get("private_key")
        solana_rpc_url = self.runtime.credentials["solana_rpc_url"]

        try:
            client = AsyncClient(solana_rpc_url)
            wallet = Keypair.from_base58_string(private_key)
            # wallet_address = wallet.pubkey()

            options = {
                "initial_liquidity_sol": tool_parameters.get("initial_liquidity_sol", 1.0),
                "slippage_bps": tool_parameters.get("slippage_bps", 500),
                "priority_fee": tool_parameters.get("priority_fee", 0),
                "twitter": tool_parameters.get("twitter"),
                "telegram": tool_parameters.get("telegram"),
                "website": tool_parameters.get("website")
            }

            result = await self.launch_pumpfun_token(client, wallet, token_name, token_ticker, description, image_url, options)
            return self.create_text_message(text=f"Token launch successful: {result}")
        except Exception as e:
            logger.error(f"Error during token launch: {e}")
            return self.create_text_message(text=f"Error during token launch: {str(e)}")

    @staticmethod
    async def _upload_metadata(
        session: aiohttp.ClientSession,
        token_name: str,
        token_ticker: str,
        description: str,
        image_url: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.debug("Preparing form data for IPFS upload...")
        form_data = aiohttp.FormData()
        form_data.add_field("name", token_name)
        form_data.add_field("symbol", token_ticker)
        form_data.add_field("description", description)
        form_data.add_field("showName", "true")

        if options.get("twitter"):
            form_data.add_field("twitter", options["twitter"])
        if options.get("telegram"):
            form_data.add_field("telegram", options["telegram"])
        if options.get("website"):
            form_data.add_field("website", options["website"])

        logger.debug(f"Downloading image from {image_url}...")
        async with session.get(image_url) as image_response:
            if image_response.status != 200:
                raise ValueError(f"Failed to download image from {image_url} (status {image_response.status})")
            image_data = await image_response.read()

        form_data.add_field(
            "file",
            image_data,
            filename="token_image.png",
            content_type="image/png"
        )

        logger.debug("Uploading metadata to Pump.fun IPFS endpoint...")
        async with session.post("https://pump.fun/api/ipfs", data=form_data) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Metadata upload failed (status {response.status}): {error_text}")

            return await response.json()

    @staticmethod
    async def _create_token_transaction(
        session: aiohttp.ClientSession,
        wallet: Keypair,
        metadata_response: Dict[str, Any],
        options: Dict[str, Any]
    ) -> bytes:
        payload = {
            "publicKey": str(wallet.pubkey()),
            "action": "create",
            "tokenMetadata": {
                "name": metadata_response["metadata"]["name"],
                "symbol": metadata_response["metadata"]["symbol"],
                "uri": metadata_response["metadataUri"],
            },
            "mint": str(wallet.pubkey()),
            "denominatedInSol": "true",
            "amount": options["initial_liquidity_sol"],
            "slippage": options["slippage_bps"],
            "priorityFee": options["priority_fee"],
            "pool": "pump"
        }

        logger.debug("Requesting token transaction from Pump.fun...")
        async with session.post("https://pumpportal.fun/api/trade-local", json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Transaction creation failed (status {response.status}): {error_text}")

            tx_data = await response.read()
            return tx_data

    @staticmethod
    async def launch_pumpfun_token(
        client: AsyncClient,
        wallet: Keypair,
        token_name: str,
        token_ticker: str,
        description: str,
        image_url: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info("Starting token launch process...")
        mint_keypair = Keypair()
        logger.info(f"Mint public key: {mint_keypair.pubkey()}")

        try:
            async with aiohttp.ClientSession() as session:
                logger.info("Uploading metadata to IPFS...")
                metadata_response = await LaunchPumpTool._upload_metadata(
                    session,
                    token_name,
                    token_ticker,
                    description,
                    image_url,
                    options
                )
                logger.debug(f"Metadata response: {metadata_response}")

                logger.info("Creating token transaction...")
                tx_data = await LaunchPumpTool._create_token_transaction(
                    session,
                    wallet,
                    metadata_response,
                    options
                )
                logger.debug("Deserializing transaction...")
                tx = VersionedTransaction.deserialize(tx_data)

            logger.info("Signing and sending transaction to the Solana network...")
            signature = await LaunchPumpTool.sign_and_send_transaction(client, tx, mint_keypair, wallet)

            logger.info("Token launch successful!")
            return {
                "signature": signature,
                "mint": str(mint_keypair.pubkey()),
                "metadata_uri": metadata_response["metadataUri"]
            }

        except Exception as error:
            logger.error(f"Error in launch_pumpfun_token: {error}")
            raise

    @staticmethod
    async def sign_and_send_transaction(
        client: AsyncClient,
        tx: VersionedTransaction,
        mint_keypair: Keypair,
        wallet: Keypair
    ) -> str:
        """
        Sign and send transaction with proper error handling.

        Args:
            client: AsyncClient instance
            tx: Transaction to send
            mint_keypair: Keypair for the token mint
            wallet: Keypair for the wallet

        Returns:
            Transaction signature
        """
        try:
            recent_blockhash = await client.get_latest_blockhash()
            tx.message.recent_blockhash = recent_blockhash.value.blockhash
            tx.sign([mint_keypair, wallet])

            signature = await client.send_transaction(
                tx,
                [wallet, mint_keypair],
                opts={
                    "skip_preflight": False,
                    "preflight_commitment": Confirmed,
                    "max_retries": 5
                }
            )

            confirmation = await client.confirm_transaction(
                signature.value,
                commitment=Confirmed
            )

            if confirmation.value.err:
                raise Exception(f"Transaction failed: {confirmation.value.err}")

            return str(signature.value)

        except Exception as error:
            logger.error(f"Transaction error: {error}")
            raise
