import os
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
import requests
from decimal import *
import time
import csv
from datetime import datetime

# Load environment variables
load_dotenv()
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")

# Connect to the Alchemy node
w3 = Web3(Web3.HTTPProvider(f"https://eth-mainnet.alchemyapi.io/v2/{ALCHEMY_API_KEY}"))

# Add middleware for POA network
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Set account to use for transactions
account = w3.eth.account.from_key(WALLET_PRIVATE_KEY)
w3.eth.default_account = account.address

# Define the endpoint for the Ethereum price API
endpoint = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum,rocket-pool-eth,wrapped-steth,frax-ether&vs_currencies=usd"

# Hold all contracts
contracts = {}

# Hold exchange rates
exchange_rates = {}

# Hold prices
expected_prices = {}
actual_prices = {}

# Diviation from peg
deviations = {}


def set_up():
    ######################################### rETH #########################################

    # Define contract address and ABI
    rETH_address = "0xae78736Cd615f374D3085123A210448E74Fc6393"
    rETH_abi = [
        {
            "inputs": [
                {
                    "internalType": "contract RocketStorageInterface",
                    "name": "_rocketStorageAddress",
                    "type": "address",
                }
            ],
            "stateMutability": "nonpayable",
            "type": "constructor",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "owner",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "spender",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "value",
                    "type": "uint256",
                },
            ],
            "name": "Approval",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "from",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "time",
                    "type": "uint256",
                },
            ],
            "name": "EtherDeposited",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "from",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "ethAmount",
                    "type": "uint256",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "time",
                    "type": "uint256",
                },
            ],
            "name": "TokensBurned",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "to",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "ethAmount",
                    "type": "uint256",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "time",
                    "type": "uint256",
                },
            ],
            "name": "TokensMinted",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "from",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "to",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "value",
                    "type": "uint256",
                },
            ],
            "name": "Transfer",
            "type": "event",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "owner", "type": "address"},
                {"internalType": "address", "name": "spender", "type": "address"},
            ],
            "name": "allowance",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
            ],
            "name": "approve",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "account", "type": "address"}
            ],
            "name": "balanceOf",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "_rethAmount", "type": "uint256"}
            ],
            "name": "burn",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "decimals",
            "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {
                    "internalType": "uint256",
                    "name": "subtractedValue",
                    "type": "uint256",
                },
            ],
            "name": "decreaseAllowance",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "depositExcess",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "depositExcessCollateral",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "getCollateralRate",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "_rethAmount", "type": "uint256"}
            ],
            "name": "getEthValue",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "getExchangeRate",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "_ethAmount", "type": "uint256"}
            ],
            "name": "getRethValue",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "getTotalCollateral",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "addedValue", "type": "uint256"},
            ],
            "name": "increaseAllowance",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "_ethAmount", "type": "uint256"},
                {"internalType": "address", "name": "_to", "type": "address"},
            ],
            "name": "mint",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "name",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "symbol",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "recipient", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "sender", "type": "address"},
                {"internalType": "address", "name": "recipient", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
            ],
            "name": "transferFrom",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "version",
            "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
            "stateMutability": "view",
            "type": "function",
        },
        {"stateMutability": "payable", "type": "receive"},
    ]

    # Instantiate the contract
    contract = w3.eth.contract(address=rETH_address, abi=rETH_abi)
    contracts["rocket-pool-eth"] = contract

    ######################################### wstETH #########################################

    # Define contract address and ABI
    wstETH_address = "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"
    wstETH_abi = [
        {
            "inputs": [
                {"internalType": "contract IStETH", "name": "_stETH", "type": "address"}
            ],
            "stateMutability": "nonpayable",
            "type": "constructor",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "owner",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "spender",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "value",
                    "type": "uint256",
                },
            ],
            "name": "Approval",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "from",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "to",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "value",
                    "type": "uint256",
                },
            ],
            "name": "Transfer",
            "type": "event",
        },
        {
            "inputs": [],
            "name": "DOMAIN_SEPARATOR",
            "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "owner", "type": "address"},
                {"internalType": "address", "name": "spender", "type": "address"},
            ],
            "name": "allowance",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
            ],
            "name": "approve",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "account", "type": "address"}
            ],
            "name": "balanceOf",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "decimals",
            "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {
                    "internalType": "uint256",
                    "name": "subtractedValue",
                    "type": "uint256",
                },
            ],
            "name": "decreaseAllowance",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "_wstETHAmount", "type": "uint256"}
            ],
            "name": "getStETHByWstETH",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "_stETHAmount", "type": "uint256"}
            ],
            "name": "getWstETHByStETH",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "addedValue", "type": "uint256"},
            ],
            "name": "increaseAllowance",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "name",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
            "name": "nonces",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "owner", "type": "address"},
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "value", "type": "uint256"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                {"internalType": "uint8", "name": "v", "type": "uint8"},
                {"internalType": "bytes32", "name": "r", "type": "bytes32"},
                {"internalType": "bytes32", "name": "s", "type": "bytes32"},
            ],
            "name": "permit",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "stETH",
            "outputs": [
                {"internalType": "contract IStETH", "name": "", "type": "address"}
            ],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "stEthPerToken",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "symbol",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "tokensPerStEth",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "recipient", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "sender", "type": "address"},
                {"internalType": "address", "name": "recipient", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
            ],
            "name": "transferFrom",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "_wstETHAmount", "type": "uint256"}
            ],
            "name": "unwrap",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "_stETHAmount", "type": "uint256"}
            ],
            "name": "wrap",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {"stateMutability": "payable", "type": "receive"},
    ]

    # Instantiate the contract
    contract = w3.eth.contract(address=wstETH_address, abi=wstETH_abi)
    contracts["wrapped-steth"] = contract

    ######################################### cbETH #########################################

    # Define contract address and ABI
    cbETH_address = "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"
    cbETH_abi = [
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "owner",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "spender",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "value",
                    "type": "uint256",
                },
            ],
            "name": "Approval",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "authorizer",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "bytes32",
                    "name": "nonce",
                    "type": "bytes32",
                },
            ],
            "name": "AuthorizationCanceled",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "authorizer",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "bytes32",
                    "name": "nonce",
                    "type": "bytes32",
                },
            ],
            "name": "AuthorizationUsed",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "_account",
                    "type": "address",
                }
            ],
            "name": "Blacklisted",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "newBlacklister",
                    "type": "address",
                }
            ],
            "name": "BlacklisterChanged",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "burner",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256",
                },
            ],
            "name": "Burn",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "oracle",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "newExchangeRate",
                    "type": "uint256",
                },
            ],
            "name": "ExchangeRateUpdated",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "newMasterMinter",
                    "type": "address",
                }
            ],
            "name": "MasterMinterChanged",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "minter",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "to",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256",
                },
            ],
            "name": "Mint",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "minter",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "minterAllowedAmount",
                    "type": "uint256",
                },
            ],
            "name": "MinterConfigured",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "oldMinter",
                    "type": "address",
                }
            ],
            "name": "MinterRemoved",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "newOracle",
                    "type": "address",
                }
            ],
            "name": "OracleUpdated",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": False,
                    "internalType": "address",
                    "name": "previousOwner",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "address",
                    "name": "newOwner",
                    "type": "address",
                },
            ],
            "name": "OwnershipTransferred",
            "type": "event",
        },
        {"anonymous": False, "inputs": [], "name": "Pause", "type": "event"},
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "newAddress",
                    "type": "address",
                }
            ],
            "name": "PauserChanged",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "newRescuer",
                    "type": "address",
                }
            ],
            "name": "RescuerChanged",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "from",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "to",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "value",
                    "type": "uint256",
                },
            ],
            "name": "Transfer",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "_account",
                    "type": "address",
                }
            ],
            "name": "UnBlacklisted",
            "type": "event",
        },
        {"anonymous": False, "inputs": [], "name": "Unpause", "type": "event"},
        {
            "inputs": [],
            "name": "CANCEL_AUTHORIZATION_TYPEHASH",
            "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "DOMAIN_SEPARATOR",
            "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "PERMIT_TYPEHASH",
            "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "RECEIVE_WITH_AUTHORIZATION_TYPEHASH",
            "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "TRANSFER_WITH_AUTHORIZATION_TYPEHASH",
            "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "owner", "type": "address"},
                {"internalType": "address", "name": "spender", "type": "address"},
            ],
            "name": "allowance",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "value", "type": "uint256"},
            ],
            "name": "approve",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "authorizer", "type": "address"},
                {"internalType": "bytes32", "name": "nonce", "type": "bytes32"},
            ],
            "name": "authorizationState",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "account", "type": "address"}
            ],
            "name": "balanceOf",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "_account", "type": "address"}
            ],
            "name": "blacklist",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "blacklister",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "_amount", "type": "uint256"}
            ],
            "name": "burn",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "authorizer", "type": "address"},
                {"internalType": "bytes32", "name": "nonce", "type": "bytes32"},
                {"internalType": "uint8", "name": "v", "type": "uint8"},
                {"internalType": "bytes32", "name": "r", "type": "bytes32"},
                {"internalType": "bytes32", "name": "s", "type": "bytes32"},
            ],
            "name": "cancelAuthorization",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "minter", "type": "address"},
                {
                    "internalType": "uint256",
                    "name": "minterAllowedAmount",
                    "type": "uint256",
                },
            ],
            "name": "configureMinter",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "currency",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "decimals",
            "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "decrement", "type": "uint256"},
            ],
            "name": "decreaseAllowance",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "exchangeRate",
            "outputs": [
                {"internalType": "uint256", "name": "_exchangeRate", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "increment", "type": "uint256"},
            ],
            "name": "increaseAllowance",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "string", "name": "tokenName", "type": "string"},
                {"internalType": "string", "name": "tokenSymbol", "type": "string"},
                {"internalType": "string", "name": "tokenCurrency", "type": "string"},
                {"internalType": "uint8", "name": "tokenDecimals", "type": "uint8"},
                {
                    "internalType": "address",
                    "name": "newMasterMinter",
                    "type": "address",
                },
                {"internalType": "address", "name": "newPauser", "type": "address"},
                {
                    "internalType": "address",
                    "name": "newBlacklister",
                    "type": "address",
                },
                {"internalType": "address", "name": "newOwner", "type": "address"},
            ],
            "name": "initialize",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "string", "name": "newName", "type": "string"}],
            "name": "initializeV2",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "lostAndFound", "type": "address"}
            ],
            "name": "initializeV2_1",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "_account", "type": "address"}
            ],
            "name": "isBlacklisted",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "account", "type": "address"}
            ],
            "name": "isMinter",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "masterMinter",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "_to", "type": "address"},
                {"internalType": "uint256", "name": "_amount", "type": "uint256"},
            ],
            "name": "mint",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "minter", "type": "address"}
            ],
            "name": "minterAllowance",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "name",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
            "name": "nonces",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "oracle",
            "outputs": [
                {"internalType": "address", "name": "_oracle", "type": "address"}
            ],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "owner",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "pause",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "paused",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "pauser",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "owner", "type": "address"},
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "value", "type": "uint256"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                {"internalType": "uint8", "name": "v", "type": "uint8"},
                {"internalType": "bytes32", "name": "r", "type": "bytes32"},
                {"internalType": "bytes32", "name": "s", "type": "bytes32"},
            ],
            "name": "permit",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "from", "type": "address"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "value", "type": "uint256"},
                {"internalType": "uint256", "name": "validAfter", "type": "uint256"},
                {"internalType": "uint256", "name": "validBefore", "type": "uint256"},
                {"internalType": "bytes32", "name": "nonce", "type": "bytes32"},
                {"internalType": "uint8", "name": "v", "type": "uint8"},
                {"internalType": "bytes32", "name": "r", "type": "bytes32"},
                {"internalType": "bytes32", "name": "s", "type": "bytes32"},
            ],
            "name": "receiveWithAuthorization",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "minter", "type": "address"}
            ],
            "name": "removeMinter",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {
                    "internalType": "contract IERC20",
                    "name": "tokenContract",
                    "type": "address",
                },
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
            ],
            "name": "rescueERC20",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "rescuer",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "symbol",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "value", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "from", "type": "address"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "value", "type": "uint256"},
            ],
            "name": "transferFrom",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "newOwner", "type": "address"}
            ],
            "name": "transferOwnership",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "from", "type": "address"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "value", "type": "uint256"},
                {"internalType": "uint256", "name": "validAfter", "type": "uint256"},
                {"internalType": "uint256", "name": "validBefore", "type": "uint256"},
                {"internalType": "bytes32", "name": "nonce", "type": "bytes32"},
                {"internalType": "uint8", "name": "v", "type": "uint8"},
                {"internalType": "bytes32", "name": "r", "type": "bytes32"},
                {"internalType": "bytes32", "name": "s", "type": "bytes32"},
            ],
            "name": "transferWithAuthorization",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "_account", "type": "address"}
            ],
            "name": "unBlacklist",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "unpause",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "_newBlacklister",
                    "type": "address",
                }
            ],
            "name": "updateBlacklister",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "newExchangeRate",
                    "type": "uint256",
                }
            ],
            "name": "updateExchangeRate",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "_newMasterMinter",
                    "type": "address",
                }
            ],
            "name": "updateMasterMinter",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "newOracle", "type": "address"}
            ],
            "name": "updateOracle",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "_newPauser", "type": "address"}
            ],
            "name": "updatePauser",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "newRescuer", "type": "address"}
            ],
            "name": "updateRescuer",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "version",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function",
        },
    ]

    # # Instantiate the contract
    # contract = w3.eth.contract(address=cbETH_address, abi=cbETH_abi)
    # contracts["cbETH"] = contract

    # Call the getValue function
    # cbETH_exchange_rate = contracts["cbETH"].functions.exchangeRate().call()
    # prices["cbETH"].append(cbETH_exchange_rate)

    ######################################### frxETH #########################################

    # Define contract address and ABI
    frxETH_address = "0xac3E018457B222d93114458476f3E3416Abbe38F"
    frxETH_abi = [
        {
            "inputs": [
                {
                    "internalType": "contract ERC20",
                    "name": "_underlying",
                    "type": "address",
                },
                {
                    "internalType": "uint32",
                    "name": "_rewardsCycleLength",
                    "type": "uint32",
                },
            ],
            "stateMutability": "nonpayable",
            "type": "constructor",
        },
        {"inputs": [], "name": "SyncError", "type": "error"},
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "owner",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "spender",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256",
                },
            ],
            "name": "Approval",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "caller",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "owner",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "assets",
                    "type": "uint256",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "shares",
                    "type": "uint256",
                },
            ],
            "name": "Deposit",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "uint32",
                    "name": "cycleEnd",
                    "type": "uint32",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "rewardAmount",
                    "type": "uint256",
                },
            ],
            "name": "NewRewardsCycle",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "from",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "to",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256",
                },
            ],
            "name": "Transfer",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "caller",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "receiver",
                    "type": "address",
                },
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "owner",
                    "type": "address",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "assets",
                    "type": "uint256",
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "shares",
                    "type": "uint256",
                },
            ],
            "name": "Withdraw",
            "type": "event",
        },
        {
            "inputs": [],
            "name": "DOMAIN_SEPARATOR",
            "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "", "type": "address"},
                {"internalType": "address", "name": "", "type": "address"},
            ],
            "name": "allowance",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
            ],
            "name": "approve",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "asset",
            "outputs": [
                {"internalType": "contract ERC20", "name": "", "type": "address"}
            ],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "address", "name": "", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "shares", "type": "uint256"}
            ],
            "name": "convertToAssets",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "assets", "type": "uint256"}
            ],
            "name": "convertToShares",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "decimals",
            "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "assets", "type": "uint256"},
                {"internalType": "address", "name": "receiver", "type": "address"},
            ],
            "name": "deposit",
            "outputs": [
                {"internalType": "uint256", "name": "shares", "type": "uint256"}
            ],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "assets", "type": "uint256"},
                {"internalType": "address", "name": "receiver", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                {"internalType": "bool", "name": "approveMax", "type": "bool"},
                {"internalType": "uint8", "name": "v", "type": "uint8"},
                {"internalType": "bytes32", "name": "r", "type": "bytes32"},
                {"internalType": "bytes32", "name": "s", "type": "bytes32"},
            ],
            "name": "depositWithSignature",
            "outputs": [
                {"internalType": "uint256", "name": "shares", "type": "uint256"}
            ],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "lastRewardAmount",
            "outputs": [{"internalType": "uint192", "name": "", "type": "uint192"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "lastSync",
            "outputs": [{"internalType": "uint32", "name": "", "type": "uint32"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "address", "name": "", "type": "address"}],
            "name": "maxDeposit",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "address", "name": "", "type": "address"}],
            "name": "maxMint",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
            "name": "maxRedeem",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
            "name": "maxWithdraw",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "shares", "type": "uint256"},
                {"internalType": "address", "name": "receiver", "type": "address"},
            ],
            "name": "mint",
            "outputs": [
                {"internalType": "uint256", "name": "assets", "type": "uint256"}
            ],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "name",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "address", "name": "", "type": "address"}],
            "name": "nonces",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "owner", "type": "address"},
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "value", "type": "uint256"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                {"internalType": "uint8", "name": "v", "type": "uint8"},
                {"internalType": "bytes32", "name": "r", "type": "bytes32"},
                {"internalType": "bytes32", "name": "s", "type": "bytes32"},
            ],
            "name": "permit",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "assets", "type": "uint256"}
            ],
            "name": "previewDeposit",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "shares", "type": "uint256"}
            ],
            "name": "previewMint",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "shares", "type": "uint256"}
            ],
            "name": "previewRedeem",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "assets", "type": "uint256"}
            ],
            "name": "previewWithdraw",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "pricePerShare",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "shares", "type": "uint256"},
                {"internalType": "address", "name": "receiver", "type": "address"},
                {"internalType": "address", "name": "owner", "type": "address"},
            ],
            "name": "redeem",
            "outputs": [
                {"internalType": "uint256", "name": "assets", "type": "uint256"}
            ],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "rewardsCycleEnd",
            "outputs": [{"internalType": "uint32", "name": "", "type": "uint32"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "rewardsCycleLength",
            "outputs": [{"internalType": "uint32", "name": "", "type": "uint32"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "symbol",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "syncRewards",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "totalAssets",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "from", "type": "address"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
            ],
            "name": "transferFrom",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "assets", "type": "uint256"},
                {"internalType": "address", "name": "receiver", "type": "address"},
                {"internalType": "address", "name": "owner", "type": "address"},
            ],
            "name": "withdraw",
            "outputs": [
                {"internalType": "uint256", "name": "shares", "type": "uint256"}
            ],
            "stateMutability": "nonpayable",
            "type": "function",
        },
    ]

    # Instantiate the contract
    contract = w3.eth.contract(address=frxETH_address, abi=frxETH_abi)
    contracts["frax-ether"] = contract


def update_prices():
    # Call the getValue function
    rETH_exchange_rate = contracts["rocket-pool-eth"].functions.getExchangeRate().call()
    exchange_rates["rocket-pool-eth"] = Web3.fromWei(rETH_exchange_rate, "ether")

    # Call the stEthPerToken function
    wstETH_exchange_rate = contracts["wrapped-steth"].functions.stEthPerToken().call()
    exchange_rates["wrapped-steth"] = Web3.fromWei(wstETH_exchange_rate, "ether")

    # Call the convertToAssets function
    frxETH_exchange_rate = (
        contracts["frax-ether"].functions.convertToAssets(1000000000000000000).call()
    )
    exchange_rates["frax-ether"] = Web3.fromWei(frxETH_exchange_rate, "ether")

    # Send a GET request to the endpoint
    response = requests.get(endpoint)

    # Parse the JSON response
    data = response.json()

    # Extract the Ethereum price from the data
    actual_prices["ethereum"] = Decimal(data["ethereum"]["usd"])
    actual_prices["rocket-pool-eth"] = Decimal(data["rocket-pool-eth"]["usd"])
    actual_prices["wrapped-steth"] = Decimal(data["wrapped-steth"]["usd"])
    actual_prices["frax-ether"] = Decimal(data["frax-ether"]["usd"])

    expected_prices["rocket-pool-eth"] = exchange_rates["rocket-pool-eth"] * Decimal(
        data["ethereum"]["usd"]
    )
    expected_prices["wrapped-steth"] = exchange_rates["wrapped-steth"] * Decimal(
        data["ethereum"]["usd"]
    )
    expected_prices["frax-ether"] = exchange_rates["frax-ether"] * Decimal(
        data["ethereum"]["usd"]
    )

    deviations["rocket-pool-eth"] = (
        (actual_prices["rocket-pool-eth"] - expected_prices["rocket-pool-eth"])
        / actual_prices["rocket-pool-eth"]
        * 100
    )
    deviations["wrapped-steth"] = (
        (actual_prices["wrapped-steth"] - expected_prices["wrapped-steth"])
        / actual_prices["wrapped-steth"]
        * 100
    )
    deviations["frax-ether"] = (
        (actual_prices["frax-ether"] - expected_prices["frax-ether"])
        / actual_prices["frax-ether"]
        * 100
    )


def append_to_csv():
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    data = [timestamp, actual_prices["ethereum"]]
    for token in exchange_rates.keys():
        data.append(exchange_rates[token])
        data.append(expected_prices[token])
        data.append(actual_prices[token])
        data.append(deviations[token])

    # Append the data to the CSV file
    with open("lsd-data.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data)


######################################### Output #########################################
def display_prices():
    # Send a GET request to the endpoint
    response = requests.get(endpoint)

    # Parse the JSON response
    data = response.json()

    # Extract the Ethereum price from the data
    ethereum_price = data["ethereum"]["usd"]
    rETH_price = data["rocket-pool-eth"]["usd"]
    rETH_price = data["wrapped-steth"]["usd"]

    print("Token \t\t | Exchange \t | Expected \t | Price \t | % Diff")
    print("---------------------------------------------------------------------------")
    for token in exchange_rates.keys():
        print(
            f"{token}\t | "
            + f"{exchange_rates[token]:.4f} \t | "
            + f"${expected_prices[token]:.2f} \t | "
            + f"${actual_prices[token]:.2f} \t | "
            + f"{deviations[token]:.4f}%"
        )
    print(f"Ethereum's price ${ethereum_price}")


set_up()
while True:
    update_prices()
    append_to_csv()
    display_prices()
    time.sleep(60)
