from redis import StrictRedis
from datetime import datetime, timedelta
from collections import defaultdict
from .types import MintInfo
import pickle


class Storage(object):

    def __init__(self):
        self._db = StrictRedis()

    def _format_key(self, *args):
        return ':'.join(args)

    def verified(self, address):
        """仅处理已经在 etherscan 开源的 erc721 合约
        """
        contract = self.get_contract(address)
        return contract and contract['verified']

    def del_contract(self, contract):
        key = self._format_key("contracts", str(contract))
        print(key)
        # contracts:0x6d3Adf9fEF24dDB3fFd0457455176dC6c437199f
        # contracts:0x6d3adf9fef24ddb3ffd0457455176dc6c437199f
        self._db.delete(key)
    
    def update_contract(self, contract, value):
        self._update_contract(contract, value)
    
    def _update_contract(self, contract, value):
        contract = contract.lower()

        key = self._format_key("contracts", contract)
        self._db.hmset(key, value)

    def get_contract(self, contract):
        contract = contract.lower()

        key = self._format_key("contracts", contract)
        value = self._db.hgetall(key)
        result = {}
        for k, v in value.items():
            result[k.decode()] = v.decode()
        return result

    def add_mint(self, mint_info: MintInfo):
        key = self._format_key("mints")
        member = pickle.dumps(mint_info)
        score = datetime.now().timestamp()
        self._db.zadd(key, {member: score})

    def get_mint_stats(self):
        # 要统计两部分数据
        # 1. 按照区块高度统计 mint tx 信息
        # 2. 按照时间统计项目的整体 mint 信息

        key = self._format_key("mints")
        # 只保存一小时的 mint 结果
        self._db.zremrangebyscore(key, 0, datetime.now().timestamp() - 3600)

        block_mints = defaultdict(list) # block_number->txs
        time_mints = defaultdict(list)

        now = datetime.now()
        for member, score in self._db.zrange(key, 0, -1, withscores=True):
            mint_time = datetime.fromtimestamp(score)
            mint_info: MintInfo = pickle.loads(member)
            # 区块 mint 信息
            block_mints[mint_info.block_number].append(mint_info)

            for delta in [3, 5, 30, 60]:
                if mint_time - now < timedelta(minutes=delta):
                    # 3min
                    time_mints[f'mint_{delta}m'].append(pickle.loads(member))

        stats = defaultdict(dict)
        for k, v in time_mints.items():
            contracts = defaultdict(lambda : [set(), 0])
            for mint_info in v:
                contract = mint_info.contract
                contracts[contract][0].add(mint_info.from_address)
                contracts[contract][1] = contracts[contract][1] + 1
            
            lst = []
            for kk, vv in contracts.items():
                contract = self.get_contract(kk)
                lst.append([contract['name'], contract['opensea_url'], contract['etherscan_url'], contract['image_url'], len(vv[0]), vv[1]])

            stats[k] = sorted(lst, key=lambda x: x[-1]) 

        return block_mints, stats

    def list_all_contracts(self):
        keys = self._db.keys(self._format_key("contracts", "*"))
        return [self._db.hgetall(key) for key in keys]

    
backend = Storage()

        