import base64
import os
import logging
from typing import Any

from solana.rpc.api import Client
from solana.rpc.commitment import Processed, Confirmed
from solana.rpc.types import TokenAccountOpts, TxOpts, MemcmpOpts
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price  # type: ignore
from solders.message import MessageV0  # type: ignore
from solders.pubkey import Pubkey  # type: ignore
from solders.keypair import Keypair
from solders.system_program import CreateAccountWithSeedParams, create_account_with_seed
from solders.transaction import VersionedTransaction  # type: ignore
from spl.token.client import Token
from spl.token.instructions import CloseAccountParams, InitializeAccountParams, close_account, create_associated_token_account, get_associated_token_address, initialize_account

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool

from dataclasses import dataclass

from solders.pubkey import Pubkey as PublicKey  # type: ignore
from construct import (BitsInteger, BitsSwapped, BitStruct, Bytes,
                       BytesInteger, Const, Flag, Int8ul, Int32ul, Int64ul,
                       Padding)
from construct import Struct as cStruct

import json
import struct
import time
from typing import Optional

import requests
from solana.rpc.async_api import AsyncClient
from solders.instruction import Instruction  # type: ignore
from solders.signature import Signature  # type: ignore


logger = logging.getLogger(__name__)

WSOL = Pubkey.from_string("So11111111111111111111111111111111111111112")
RAY_V4 = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")
RAY_AUTHORITY_V4 = Pubkey.from_string("5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1")
OPEN_BOOK_PROGRAM = Pubkey.from_string("srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX")
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
SOL_DECIMAL = 1e9
UNIT_BUDGET = 100_000
UNIT_PRICE = 1_000_000

# NOT MY WORK, THANK YOU TO WHOEVER FIGURED THIS OUT X2 (I agree with you father)

LIQUIDITY_STATE_LAYOUT_V4 = cStruct(
    "status" / Int64ul,
    "nonce" / Int64ul,
    "orderNum" / Int64ul,
    "depth" / Int64ul,
    "coinDecimals" / Int64ul,
    "pcDecimals" / Int64ul,
    "state" / Int64ul,
    "resetFlag" / Int64ul,
    "minSize" / Int64ul,
    "volMaxCutRatio" / Int64ul,
    "amountWaveRatio" / Int64ul,
    "coinLotSize" / Int64ul,
    "pcLotSize" / Int64ul,
    "minPriceMultiplier" / Int64ul,
    "maxPriceMultiplier" / Int64ul,
    "systemDecimalsValue" / Int64ul,
    "minSeparateNumerator" / Int64ul,
    "minSeparateDenominator" / Int64ul,
    "tradeFeeNumerator" / Int64ul,
    "tradeFeeDenominator" / Int64ul,
    "pnlNumerator" / Int64ul,
    "pnlDenominator" / Int64ul,
    "swapFeeNumerator" / Int64ul,
    "swapFeeDenominator" / Int64ul,
    "needTakePnlCoin" / Int64ul,
    "needTakePnlPc" / Int64ul,
    "totalPnlPc" / Int64ul,
    "totalPnlCoin" / Int64ul,
    "poolOpenTime" / Int64ul,
    "punishPcAmount" / Int64ul,
    "punishCoinAmount" / Int64ul,
    "orderbookToInitTime" / Int64ul,
    "swapCoinInAmount" / BytesInteger(16, signed=False, swapped=True),
    "swapPcOutAmount" / BytesInteger(16, signed=False, swapped=True),
    "swapCoin2PcFee" / Int64ul,
    "swapPcInAmount" / BytesInteger(16, signed=False, swapped=True),
    "swapCoinOutAmount" / BytesInteger(16, signed=False, swapped=True),
    "swapPc2CoinFee" / Int64ul,
    "poolCoinTokenAccount" / Bytes(32),
    "poolPcTokenAccount" / Bytes(32),
    "coinMintAddress" / Bytes(32),
    "pcMintAddress" / Bytes(32),
    "lpMintAddress" / Bytes(32),
    "ammOpenOrders" / Bytes(32),
    "serumMarket" / Bytes(32),
    "serumProgramId" / Bytes(32),
    "ammTargetOrders" / Bytes(32),
    "poolWithdrawQueue" / Bytes(32),
    "poolTempLpTokenAccount" / Bytes(32),
    "ammOwner" / Bytes(32),
    "pnlOwner" / Bytes(32),
)

ACCOUNT_FLAGS_LAYOUT = BitsSwapped(
    BitStruct(
        "initialized" / Flag,
        "market" / Flag,
        "open_orders" / Flag,
        "request_queue" / Flag,
        "event_queue" / Flag,
        "bids" / Flag,
        "asks" / Flag,
        Const(0, BitsInteger(57)),
    )
)

MARKET_STATE_LAYOUT_V3 = cStruct(
    Padding(5),
    "account_flags" / ACCOUNT_FLAGS_LAYOUT,
    "own_address" / Bytes(32),
    "vault_signer_nonce" / Int64ul,
    "base_mint" / Bytes(32),
    "quote_mint" / Bytes(32),
    "base_vault" / Bytes(32),
    "base_deposits_total" / Int64ul,
    "base_fees_accrued" / Int64ul,
    "quote_vault" / Bytes(32),
    "quote_deposits_total" / Int64ul,
    "quote_fees_accrued" / Int64ul,
    "quote_dust_threshold" / Int64ul,
    "request_queue" / Bytes(32),
    "event_queue" / Bytes(32),
    "bids" / Bytes(32),
    "asks" / Bytes(32),
    "base_lot_size" / Int64ul,
    "quote_lot_size" / Int64ul,
    "fee_rate_bps" / Int64ul,
    "referrer_rebate_accrued" / Int64ul,
    Padding(7),
)

OPEN_ORDERS_LAYOUT = cStruct(
    Padding(5),
    "account_flags" / ACCOUNT_FLAGS_LAYOUT,
    "market" / Bytes(32),
    "owner" / Bytes(32),
    "base_token_free" / Int64ul,
    "base_token_total" / Int64ul,
    "quote_token_free" / Int64ul,
    "quote_token_total" / Int64ul,
    "free_slot_bits" / Bytes(16),
    "is_bid_bits" / Bytes(16),
    "orders" / Bytes(16)[128],
    "client_ids" / Int64ul[128],
    "referrer_rebate_accrued" / Int64ul,
    Padding(7),
)

SWAP_LAYOUT = cStruct(
    "instruction" / Int8ul, "amount_in" / Int64ul, "min_amount_out" / Int64ul
)

PUBLIC_KEY_LAYOUT = Bytes(32)

ACCOUNT_LAYOUT = cStruct(
    "mint" / PUBLIC_KEY_LAYOUT,
    "owner" / PUBLIC_KEY_LAYOUT,
    "amount" / Int64ul,
    "delegate_option" / Int32ul,
    "delegate" / PUBLIC_KEY_LAYOUT,
    "state" / Int8ul,
    "is_native_option" / Int32ul,
    "is_native" / Int64ul,
    "delegated_amount" / Int64ul,
    "close_authority_option" / Int32ul,
    "close_authority" / PUBLIC_KEY_LAYOUT,
)


@dataclass
class AccountMeta:
    public_key: PublicKey | str
    is_signer: bool
    is_writable: bool


@dataclass
class PoolKeys:
    amm_id: PublicKey
    base_mint: PublicKey
    quote_mint: PublicKey
    base_decimals: int
    quote_decimals: int
    open_orders: PublicKey
    target_orders: PublicKey
    base_vault: PublicKey
    quote_vault: PublicKey
    market_id: PublicKey
    market_authority: PublicKey
    market_base_vault: PublicKey
    market_quote_vault: PublicKey
    bids: PublicKey
    asks: PublicKey
    event_queue: PublicKey


def fetch_pool_keys(client: AsyncClient, pair_address: str) -> Optional[PoolKeys]:
    try:
        amm_id = PublicKey.from_string(pair_address)
        amm_data = client.get_account_info_json_parsed(amm_id, commitment=Processed)
        amm_data_decoded = LIQUIDITY_STATE_LAYOUT_V4.parse(amm_data)
        marketId = PublicKey.from_bytes(amm_data_decoded.serumMarket)
        marketInfo = client.get_account_info_json_parsed(marketId, commitment=Processed)
        market_decoded = MARKET_STATE_LAYOUT_V3.parse(marketInfo)
        vault_signer_nonce = market_decoded.vault_signer_nonce

        pool_keys = PoolKeys(
            amm_id=amm_id,
            base_mint=PublicKey.from_bytes(market_decoded.base_mint),
            quote_mint=PublicKey.from_bytes(market_decoded.quote_mint),
            base_decimals=amm_data_decoded.coinDecimals,
            quote_decimals=amm_data_decoded.pcDecimals,
            open_orders=PublicKey.from_bytes(amm_data_decoded.ammOpenOrders),
            target_orders=PublicKey.from_bytes(amm_data_decoded.ammTargetOrders),
            base_vault=PublicKey.from_bytes(amm_data_decoded.poolCoinTokenAccount),
            quote_vault=PublicKey.from_bytes(amm_data_decoded.poolPcTokenAccount),
            market_id=marketId,
            market_authority=PublicKey.create_program_address(
                [bytes(marketId), bytes_of(vault_signer_nonce)],
                OPEN_BOOK_PROGRAM,
            ),
            market_base_vault=PublicKey.from_bytes(market_decoded.base_vault),
            market_quote_vault=PublicKey.from_bytes(market_decoded.quote_vault),
            bids=PublicKey.from_bytes(market_decoded.bids),
            asks=PublicKey.from_bytes(market_decoded.asks),
            event_queue=PublicKey.from_bytes(market_decoded.event_queue),
        )

        return pool_keys
    except Exception as e:
        print(f"Error fetching pool keys: {e}")
        return None


def bytes_of(value):
    if not (0 <= value < 2**64):
        raise ValueError("Value must be in the range of a u64 (0 to 2^64 - 1).")
    return struct.pack('<Q', value)


def get_pair_address_from_api(mint):
    url = f"https://api-v3.raydium.io/pools/info/mint?mint1={mint}&poolType=all&poolSortField=default&sortType=desc&pageSize=1&page=1"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        pools = data.get('data', {}).get('data', [])
        if not pools:
            return None

        pool = pools[0]
        program_id = pool.get('programId')
        if program_id == "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8":  # AMM v4 Program
            pair_address = pool.get('id')
            return pair_address

        return None
    except Exception as e:
        print(f"Error fetching pair address: {e}")
        return None


def get_pair_address_from_rpc(client: AsyncClient, token_address: str) -> str:
    print("Getting pair address from RPC...")
    BASE_OFFSET = 400
    QUOTE_OFFSET = 432
    DATA_LENGTH_FILTER = 752
    QUOTE_MINT = "So11111111111111111111111111111111111111112"
    RAYDIUM_PROGRAM_ID = PublicKey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")

    def fetch_amm_id(base_mint: str, quote_mint: str) -> str:
        memcmp_filter_base = MemcmpOpts(offset=BASE_OFFSET, bytes=base_mint)
        memcmp_filter_quote = MemcmpOpts(offset=QUOTE_OFFSET, bytes=quote_mint)
        try:
            response = client.get_program_accounts(
                RAYDIUM_PROGRAM_ID,
                commitment=Processed,
                filters=[DATA_LENGTH_FILTER, memcmp_filter_base, memcmp_filter_quote]
            )
            accounts = response.value
            if accounts:
                return str(accounts[0].pubkey)
        except Exception as e:
            print(f"Error fetching AMM ID: {e}")
        return None

    pair_address = fetch_amm_id(token_address, QUOTE_MINT)

    if not pair_address:
        pair_address = fetch_amm_id(QUOTE_MINT, token_address)

    return pair_address


def make_swap_instruction(
        amount_in: int,
        minimum_amount_out: int,
        token_account_in: PublicKey,
        token_account_out: PublicKey,
        accounts: PoolKeys,
        owner: Keypair
) -> Instruction:
    try:
        keys = [
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts.amm_id, is_signer=False, is_writable=True),
            AccountMeta(pubkey=RAY_AUTHORITY_V4, is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts.open_orders, is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts.target_orders, is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts.base_vault, is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts.quote_vault, is_signer=False, is_writable=True),
            AccountMeta(pubkey=OPEN_BOOK_PROGRAM, is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts.market_id, is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts.bids, is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts.asks, is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts.event_queue, is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts.market_base_vault, is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts.market_quote_vault, is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts.market_authority, is_signer=False, is_writable=False),
            AccountMeta(pubkey=token_account_in, is_signer=False, is_writable=True),
            AccountMeta(pubkey=token_account_out, is_signer=False, is_writable=True),
            AccountMeta(pubkey=owner.pubkey(), is_signer=True, is_writable=False)
        ]
        data = SWAP_LAYOUT.build(
            dict(
                instruction=9,
                amount_in=amount_in,
                min_amount_out=minimum_amount_out
            )
        )
        return Instruction(RAY_V4, data, keys)
    except Exception as e:
        print(f"Error occurred: {e}")
        return None


def get_token_balance(mint_str: str, account_pubkey: Pubkey, client: Client) -> float | None:
    try:
        mint = PublicKey.from_string(mint_str)
        opts = TokenAccountOpts(mint)
        balance = client.get_token_accounts_by_owner_json_parsed(owner=account_pubkey, opts=opts, commitment=Processed)
        balance_value = balance.value[0].account.data.parsed['info']['tokenAmount']['uiAmount']
        return balance_value
    except Exception as e:
        print(f"Error fetching balance: {e}")
        return None


def confirm_txn(client: AsyncClient, txn_sig: Signature, max_retries: int = 20, retry_interval: int = 3) -> bool:
    retries = 1

    while retries < max_retries:
        try:
            txn_res = client.get_transaction(txn_sig, encoding="json", commitment=Confirmed, max_supported_transaction_version=0)
            txn_json = json.loads(txn_res.value.transaction.meta.to_json())

            if txn_json['err'] is None:
                print("Transaction confirmed... try count:", retries)
                return True

            print("Error: Transaction not confirmed. Retrying...")
            if txn_json['err']:
                print("Transaction failed.")
                return False
        except Exception as e:
            print(e)
            print("Awaiting confirmation... try count:", retries)
            retries += 1
            time.sleep(retry_interval)

    print("Max retries reached. Transaction confirmation failed.")
    return None


def get_token_reserves(client: AsyncClient, pool_keys: PoolKeys) -> tuple:
    try:
        base_vault = pool_keys.base_vault
        quote_vault = pool_keys.quote_vault
        base_decimal = pool_keys.base_decimals
        quote_decimal = pool_keys.quote_decimals
        base_mint = pool_keys.base_mint
        quote_mint = pool_keys.quote_mint

        balances_response = client.get_multiple_accounts_json_parsed(
            [base_vault, quote_vault],
            Processed
        )
        balances = balances_response.value

        token_account = balances[0]
        sol_account = balances[1]

        token_account_balance = token_account.data.parsed['info']['tokenAmount']['uiAmount']
        sol_account_balance = sol_account.data.parsed['info']['tokenAmount']['uiAmount']

        if token_account_balance is None or sol_account_balance is None:
            return None, None

        # Determine the assignment of base and quote reserves based on the base mint
        if base_mint == WSOL:
            base_reserve = sol_account_balance
            quote_reserve = token_account_balance
            token_decimal = quote_decimal
        else:
            base_reserve = token_account_balance
            quote_reserve = sol_account_balance
            token_decimal = base_decimal

        print(f"Base Mint: {base_mint} | Quote Mint: {quote_mint}")
        print(f"Base Reserve: {base_reserve} | Quote Reserve: {quote_reserve} | Token Decimal: {token_decimal}")
        return base_reserve, quote_reserve, token_decimal

    except Exception as e:
        print(f"Error occurred: {e}")
        return None, None, None


def sol_for_tokens(spend_sol_amount, base_vault_balance, quote_vault_balance, swap_fee=0.25):
    effective_sol_used = spend_sol_amount - (spend_sol_amount * (swap_fee / 100))
    constant_product = base_vault_balance * quote_vault_balance
    updated_base_vault_balance = constant_product / (quote_vault_balance + effective_sol_used)
    tokens_received = base_vault_balance - updated_base_vault_balance
    return round(tokens_received, 9)


def tokens_for_sol(sell_token_amount, base_vault_balance, quote_vault_balance, swap_fee=0.25):
    effective_tokens_sold = sell_token_amount * (1 - (swap_fee / 100))
    constant_product = base_vault_balance * quote_vault_balance
    updated_quote_vault_balance = constant_product / (base_vault_balance + effective_tokens_sold)
    sol_received = quote_vault_balance - updated_quote_vault_balance
    return round(sol_received, 9)


class RaydiumTradeTool(BuiltinTool):
    """
    Tool for performing buy and sell operations on Raydium liquidity pools.
    """

    async def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> ToolInvokeMessage:
        action = tool_parameters.get("action")
        pair_address = tool_parameters.get("pair_address")
        amount = tool_parameters.get("amount")
        slippage = tool_parameters.get("slippage", 5)
        private_key = tool_parameters.get("private_key")
        solana_rpc_url = self.runtime.credentials["solana_rpc_url"]

        try:
            client = Client(solana_rpc_url)
            wallet = Keypair.from_base58_string(private_key)
            wallet_address = wallet.pubkey()

            if action == "buy":
                success = self.buy_with_raydium(client, wallet, wallet_address, pair_address, amount, slippage)
            elif action == "sell":
                success = self.sell_with_raydium(client, wallet, wallet_address, pair_address, amount, slippage)
            else:
                return self.create_text_message(text="Invalid action specified. Use 'buy' or 'sell'.")

            if success:
                return self.create_text_message(text=f"{action.capitalize()} transaction successful.")
            else:
                return self.create_text_message(text=f"{action.capitalize()} transaction failed.")
        except Exception as e:
            logger.error(f"Error during {action} transaction: {e}")
            return self.create_text_message(text=f"Error during {action} transaction: {str(e)}")

    @staticmethod
    def buy_with_raydium(client: Client, wallet: Keypair, wallet_address: Pubkey, pair_address: str, sol_in: float, slippage: int) -> bool:
        try:
            pool_keys = fetch_pool_keys(pair_address)
            if pool_keys is None:
                return False

            mint = pool_keys.base_mint if pool_keys.base_mint != WSOL else pool_keys.quote_mint
            amount_in = int(sol_in * SOL_DECIMAL)
            base_reserve, quote_reserve, token_decimal = get_token_reserves(pool_keys)
            amount_out = sol_for_tokens(sol_in, base_reserve, quote_reserve)
            slippage_adjustment = 1 - (slippage / 100)
            minimum_amount_out = int(amount_out * slippage_adjustment * 10**token_decimal)

            token_account_check = client.get_token_accounts_by_owner(wallet_address, TokenAccountOpts(mint), Processed)
            if token_account_check.value:
                token_account = token_account_check.value[0].pubkey
                token_account_instr = None
            else:
                token_account = get_associated_token_address(wallet_address, mint)
                token_account_instr = create_associated_token_account(wallet_address, wallet_address, mint)

            seed = base64.urlsafe_b64encode(os.urandom(24)).decode('utf-8')
            wsol_token_account = Pubkey.create_with_seed(wallet_address, seed, TOKEN_PROGRAM_ID)
            balance_needed = Token.get_min_balance_rent_for_exempt_for_account(client)

            create_wsol_account_instr = create_account_with_seed(
                CreateAccountWithSeedParams(
                    from_pubkey=wallet_address,
                    to_pubkey=wsol_token_account,
                    base=wallet_address,
                    seed=seed,
                    lamports=int(balance_needed + amount_in),
                    space=ACCOUNT_LAYOUT.sizeof(),
                    owner=TOKEN_PROGRAM_ID
                )
            )

            init_wsol_account_instr = initialize_account(
                InitializeAccountParams(
                    program_id=TOKEN_PROGRAM_ID,
                    account=wsol_token_account,
                    mint=WSOL,
                    owner=wallet_address
                )
            )

            swap_instructions = make_swap_instruction(
                amount_in=amount_in,
                minimum_amount_out=minimum_amount_out,
                token_account_in=wsol_token_account,
                token_account_out=token_account,
                accounts=pool_keys,
                owner=wallet
            )

            close_wsol_account_instr = close_account(
                CloseAccountParams(
                    program_id=TOKEN_PROGRAM_ID,
                    account=wsol_token_account,
                    dest=wallet_address,
                    owner=wallet_address
                )
            )

            instructions = [
                set_compute_unit_limit(UNIT_BUDGET),
                set_compute_unit_price(UNIT_PRICE),
                create_wsol_account_instr,
                init_wsol_account_instr
            ]

            if token_account_instr:
                instructions.append(token_account_instr)

            instructions.extend([swap_instructions, close_wsol_account_instr])

            compiled_message = MessageV0.try_compile(
                wallet_address,
                instructions,
                [],
                client.get_latest_blockhash().value.blockhash,
            )

            txn_sig = client.send_transaction(
                txn=VersionedTransaction(compiled_message, [wallet]),
                opts=TxOpts(skip_preflight=True)
            ).value

            return confirm_txn(txn_sig)

        except Exception as e:
            logger.error("Error during buy transaction:", e)
            return False

    @staticmethod
    def sell_with_raydium(client: Client, wallet: Keypair, wallet_address: Pubkey, pair_address: str, percentage: int, slippage: int) -> bool:
        try:
            if not (1 <= percentage <= 100):
                logger.error("Percentage must be between 1 and 100.")
                return False

            pool_keys = fetch_pool_keys(pair_address)
            if pool_keys is None:
                return False

            mint = pool_keys.base_mint if pool_keys.base_mint != WSOL else pool_keys.quote_mint
            token_balance = get_token_balance(str(mint), wallet_address, client)
            if token_balance == 0 or token_balance is None:
                return False

            token_balance = token_balance * (percentage / 100)
            base_reserve, quote_reserve, token_decimal = get_token_reserves(pool_keys)
            amount_out = tokens_for_sol(token_balance, base_reserve, quote_reserve)
            slippage_adjustment = 1 - (slippage / 100)
            minimum_amount_out = int(amount_out * slippage_adjustment * SOL_DECIMAL)
            amount_in = int(token_balance * 10**token_decimal)
            token_account = get_associated_token_address(wallet_address, mint)

            seed = base64.urlsafe_b64encode(os.urandom(24)).decode('utf-8')
            wsol_token_account = Pubkey.create_with_seed(wallet_address, seed, TOKEN_PROGRAM_ID)
            balance_needed = Token.get_min_balance_rent_for_exempt_for_account(client)

            create_wsol_account_instr = create_account_with_seed(
                CreateAccountWithSeedParams(
                    from_pubkey=wallet_address,
                    to_pubkey=wsol_token_account,
                    base=wallet_address,
                    seed=seed,
                    lamports=int(balance_needed),
                    space=ACCOUNT_LAYOUT.sizeof(),
                    owner=TOKEN_PROGRAM_ID
                )
            )

            init_wsol_account_instr = initialize_account(
                InitializeAccountParams(
                    program_id=TOKEN_PROGRAM_ID,
                    account=wsol_token_account,
                    mint=WSOL,
                    owner=wallet_address
                )
            )

            swap_instructions = make_swap_instruction(amount_in, minimum_amount_out, token_account, wsol_token_account, pool_keys, wallet)

            close_wsol_account_instr = close_account(
                CloseAccountParams(
                    program_id=TOKEN_PROGRAM_ID,
                    account=wsol_token_account,
                    dest=wallet_address,
                    owner=wallet_address
                )
            )

            instructions = [
                set_compute_unit_limit(UNIT_BUDGET),
                set_compute_unit_price(UNIT_PRICE),
                create_wsol_account_instr,
                init_wsol_account_instr,
                swap_instructions,
                close_wsol_account_instr
            ]

            if percentage == 100:
                close_token_account_instr = close_account(
                    CloseAccountParams(TOKEN_PROGRAM_ID, token_account, wallet_address, wallet_address)
                )
                instructions.append(close_token_account_instr)

            compiled_message = MessageV0.try_compile(
                wallet_address,
                instructions,
                [],
                client.get_latest_blockhash().value.blockhash,
            )

            txn_sig = client.send_transaction(
                txn=VersionedTransaction(compiled_message, [wallet]),
                opts=TxOpts(skip_preflight=True)
            ).value

            return confirm_txn(txn_sig)

        except Exception as e:
            logger.error("Error during sell transaction:", e)
            return False
