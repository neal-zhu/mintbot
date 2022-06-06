from loguru import logger
from mintbot import BlockListener
from mintbot import ContractVerifier
from mintbot import backend
import time
from web3 import Web3


def main():
    ETHERSCAN_API_KEY = ""
    OPENSEA_API_KEY = ""
    ETH_PROVIDER_URL = ""
    w3 = Web3(Web3.HTTPProvider(ETH_PROVIDER_URL))
    contract_verifier = ContractVerifier(ETHERSCAN_API_KEY, OPENSEA_API_KEY, w3)
    block_listener = BlockListener(w3, contract_verifier)
    block_listener.start()

    while True:
        block_mints, time_mints = backend.get_mint_stats()
        for block_number in sorted(block_mints.keys()):
            for mint in block_mints[block_number]:
                logger.info(f"{block_number} {mint}")

        for k, v in time_mints.items():
            for info in v:
                logger.info(f"{k} {info}")
        time.sleep(3)

    block_listener.join()


if __name__ == '__main__':
    main()
