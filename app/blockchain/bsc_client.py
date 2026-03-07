import json
import os
from web3 import Web3

SLH_CONTRACT = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"
ABI_PATH = "app/blockchain/slh_abi.json"

# ????? ABI
with open(ABI_PATH, "r") as f:
    data = json.load(f)
    SLH_ABI = data.get("abi", [])

# ????? ?-BSC
BSC_RPC = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")
w3 = Web3(Web3.HTTPProvider(BSC_RPC))

contract = w3.eth.contract(address=SLH_CONTRACT, abi=SLH_ABI)

def get_slh_balance(address: str) -> float:
    if not address:
        return 0.0
    try:
        raw = contract.functions.balanceOf(address).call()
        return raw / (10 ** 18)
    except Exception:
        return 0.0



