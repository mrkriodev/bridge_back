from web3 import Web3
import asyncio
import queue
from blockchain.info import infura_goerli_url, goerli_ms_sc_adr, goerli_ms_sc_adr_test, goerli_ms_sc_abi
from blockchain.commands import handle_contract_event

eth_web3 = Web3(Web3.HTTPProvider(infura_goerli_url, request_kwargs={'timeout': 60}))
eth_contract = eth_web3.eth.contract(address=goerli_ms_sc_adr_test, abi=goerli_ms_sc_abi)

eth_event_filters = (eth_contract.events.Deposit.create_filter(fromBlock='latest'),
                     eth_contract.events.IssueSigned.create_filter(fromBlock='latest'),
                     eth_contract.events.IssueProvided.create_filter(fromBlock='latest'))  #

eth_message_queue = queue.Queue()


def handle_eth_event(event):
    handle_contract_event(event, eth_message_queue)
