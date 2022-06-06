from collections import namedtuple


MintInfo = namedtuple('MintInfo', [
    'num', 'gas_price', 'value', 'mint_to', 'contract', 'input', 'tx_hash',
    'block_number', 'from_address'
])
