from web3 import Web3
import asyncio
import queue
from blockchain.info import sibr_net_url, sibr_ms_sc_adr, sibr_ms_sc_abi, \
    sibr_weths_sc_adr, sibr_weths_sc_abi
from blockchain.commands import handle_contract_event

sibr_web3 = Web3(Web3.HTTPProvider(sibr_net_url, request_kwargs={'timeout': 60}))
sibr_ms_contract = sibr_web3.eth.contract(address=sibr_ms_sc_adr, abi=sibr_ms_sc_abi)
sibr_weth_contract = sibr_web3.eth.contract(address=sibr_weths_sc_adr, abi=sibr_weths_sc_abi)

sibr_event_filters = (sibr_ms_contract.events.Deposit.create_filter(fromBlock='latest'),
                      sibr_ms_contract.events.IssueInited.create_filter(fromBlock='latest'),
                      sibr_ms_contract.events.IssueSigned.create_filter(fromBlock='latest'),
                      sibr_ms_contract.events.IssueProvided.create_filter(fromBlock='latest'),
                      sibr_weth_contract.events.Minted.create_filter(fromBlock='latest')
                      )  #

sibr_message_queue = queue.Queue()


def handle_sibr_event(event):
    handle_contract_event(event, sibr_message_queue)
