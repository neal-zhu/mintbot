from loguru import logger
from .storage import backend
import requests
from web3 import Web3
import json
from opensea import OpenseaAPI


class ContractVerifier(object):

    def __init__(self, etherscan_api_key, opensea_api_key, w3: Web3):
        self._etherscan_api_key = etherscan_api_key
        self._opensea_api = OpenseaAPI(apikey=opensea_api_key)
        self._w3 = w3

    def get_verify_info(self, contract):
        name, abi = self.verify_etherscan(contract)
        if not abi:
            return {}
        image_url, slug, external_url = self.verify_opensesa(contract)
        return {
            "verified": 1,
            "image_url": image_url,
            "opensea_url": f"https://opensea.io/collection/{slug}",
            "abi": abi,
            "name": name,
            "external_url": external_url,
            "etherscan_url": f"https://etherscan.io/address/{contract}",
        }

    def verify_etherscan(self, contract):
        abi = self._get_abi_for_contract(contract)
        if not abi:
            return "", ""

        name = self._fetch_contract_info(contract, abi)
        return name, json.dumps(abi)

    def verify_opensesa(self, contract):
        try:
            collection = self._opensea_api.contract(
                asset_contract_address=contract)['collection']
            return collection['image_url'] or "", collection[
                'slug'], collection['external_url'] or ""
        except Exception as e:
            logger.error(f"Failed to fetch collection of {contract} error {e}")
            return "", "", ""

    def _get_abi_for_contract(self, contract):
        try:
            respone = requests.get('https://api.etherscan.io/api',
                                   params={
                                       'module': 'contract',
                                       'action': 'getabi',
                                       'address': contract,
                                       'api_key': self._etherscan_api_key,
                                   }).json()
            return json.loads(respone['result'])

        except Exception as e:
            logger.error(
                f"Failed to fetch abi for {contract}, response {respone} error {e}"
            )
            return None

    def _fetch_contract_info(self, contract, abi):
        try:
            # use abi to fecth name
            contract = self._w3.eth.contract(
                address=self._w3.toChecksumAddress(contract), abi=abi)
            name = contract.functions.name().call()
            return name
        except Exception as e:
            logger.error(f"Failed to call name of {contract}, error {e}")
            return ""
