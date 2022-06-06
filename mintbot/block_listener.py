from threading import Thread
from web3 import Web3
from web3.types import TxData, TxReceipt, LogReceipt
from .eth_contract_service import EthContractService
from .contract_verifier import ContractVerifier
from .storage import backend
from .types import MintInfo
from loguru import logger


class BlockListener(Thread):

    def __init__(self, w3: Web3, verifier: ContractVerifier):
        super().__init__()
        self._w3 = w3
        self._contract_service = EthContractService()
        self._verifier = verifier

    def parse_mint_info(self, receipt: TxReceipt, tx: TxData) -> MintInfo:
        mint_num = 0
        mint_to = False

        input = tx['input']
        logs = receipt['logs']
        for log in logs:
            # 注意并不一定所有 log 都对应了 transfer
            if not self._is_mint_log(log):
                continue

            mint_num += 1
            if self._w3.toBytes(hexstr=tx['from']) not in log['topics'][2]:
                mint_to = True

        if mint_to:
            input = input.replace(
                log['topics'][2],
                f"000000000000000000000000{tx['from'].lower()}")

        return MintInfo(mint_num, tx['gasPrice'], tx['value'], mint_to,
                        tx['to'], input, tx['hash'].hex(), tx['blockNumber'],
                        tx['from'])

    def _is_mint_log(self, log: LogReceipt):
        return log['topics'][0] == self._w3.keccak(
            text="Transfer(address,address,uint256)"
        ) and log['topics'][1].hex(
        ) == '0x0000000000000000000000000000000000000000000000000000000000000000'

    def _is_mint_tx(self, receipt: TxReceipt, tx: TxData):
        if not receipt['logs']:
            return False

        for log in receipt['logs']:
            if self._is_mint_log(log):
                # 检查是否为 erc721
                code = self._w3.eth.get_code(tx['to'])
                sighashes = self._contract_service.get_function_sighashes(
                    code.hex())
                if self._contract_service.is_erc721_contract(sighashes):
                    return True

        return False

    def handle_tx(self, tx: TxData):
        to_address = tx['to']
        if not to_address:
            return

        # 首先检查是否在 redis 中
        contract = backend.get_contract(to_address)

        receipt = self._w3.eth.get_transaction_receipt(tx['hash'])
        if not contract:
            # 忽略非 mint 交易
            if not self._is_mint_tx(receipt, tx):
                return

            logger.info(
                f"Transaction {tx['hash'].hex()} is a mint transaction.")
            info = self._verifier.get_verify_info(to_address)
            if not info:
                logger.info(f"Failed to verify contract {to_address}")
                return
            logger.info(f"Verify contract {to_address}({info['name']}).")
            backend.update_contract(to_address, info)

        mint_info = self.parse_mint_info(receipt, tx)
        logger.info(f"Transaction mint info {mint_info}")
        backend.add_mint(mint_info)

    def run(self):
        logger.info(f"BlockListener started.")
        seen = set()
        while True:
            block = self._w3.eth.get_block('latest', True)
            if block['hash'].hex() not in seen:
                logger.info(
                    f"Get latest block number {block['number']} {block['hash'].hex()} transactions num {len(block['transactions'])}."
                )
                for tx in block['transactions']:
                    self.handle_tx(tx)

            seen.add(block['hash'].hex())
