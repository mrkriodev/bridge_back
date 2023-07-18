from web3 import Web3
from blockchain.info import first_adr, first_adr_pk, provider_of_sc, abi_of_sc
from web3.types import LogReceipt, HexBytes


def standard_trx_build_for_sc_call_with_gas(base_adr, provider_url: str) -> dict:
    if base_adr is None:
        return None
    web3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs={'timeout': 60}))

    build_trx_config = {
        'chainId': web3.eth.chain_id,
        'from': base_adr,
        'gasPrice': web3.eth.gas_price,
        'nonce': web3.eth.get_transaction_count(base_adr)
    }
    gas_eddition = 50000
    if not provider_url.index("infura"):
        gas_eddition = 100000
    gas = web3.eth.estimate_gas(build_trx_config) + gas_eddition
    build_trx_config['gas'] = gas + int(gas * 0.2)
    build_trx_config['gasPrice'] += int(build_trx_config['gasPrice'] * 0.2)

    return build_trx_config


def init_issue_in_msw(guardian_adr=first_adr,
                      guardian_adr_pk=first_adr_pk,
                      recepient_adr=first_adr,
                      amount_wei=10000,
                      sc_address=None):
    if sc_address is None:
        return
    provider_url = provider_of_sc.get(sc_address, '')
    sc_abi = abi_of_sc.get(sc_address, '[]')

    web3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs={'timeout': 60}))
    contract = web3.eth.contract(address=web3.to_checksum_address(sc_address), abi=sc_abi)
    build_trx_config = standard_trx_build_for_sc_call_with_gas(guardian_adr, provider_url)

    f = contract.functions.initIssue(recepient_adr, amount_wei)
    unsigned_tx = f.build_transaction(build_trx_config)
    signed_tx = web3.eth.account.sign_transaction(unsigned_tx, guardian_adr_pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    # Wait for the transaction to be mined, and get the transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(tx_receipt)


def get_issue_signs(issue_id, sc_address):
    if sc_address is None:
        return
    provider_url = provider_of_sc[sc_address]
    sc_abi = abi_of_sc[sc_address]

    web3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs={'timeout': 60}))
    contract = web3.eth.contract(address=web3.to_checksum_address(sc_address), abi=sc_abi)

    issue_info = contract.functions.getIssue(issue_id).call()
    return int(issue_info[3])


def provide_issue_in_msw(guardian_adr=first_adr,
                         guardian_adr_pk=first_adr_pk,
                         sc_address=None,
                         issue_id=0):
    if sc_address is None:
        return
    provider_url = provider_of_sc[sc_address]
    sc_abi = abi_of_sc[sc_address]

    web3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs={'timeout': 60}))
    contract = web3.eth.contract(address=web3.to_checksum_address(sc_address), abi=sc_abi)
    build_trx_config = standard_trx_build_for_sc_call_with_gas(guardian_adr, provider_url)

    f = contract.functions.provideIssue(issue_id)
    unsigned_tx = f.build_transaction(build_trx_config)
    signed_tx = web3.eth.account.sign_transaction(unsigned_tx, guardian_adr_pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    # Wait for the transaction to be mined, and get the transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(tx_receipt)


def handle_contract_event(event, message_queue):
    print(f"handled event={event}")
    event_log_receipt: LogReceipt = event
    event_type = event_log_receipt.get('event', '')
    address_of_sc = event_log_receipt.get('address', None)
    if event_type == 'Deposit':
        sender = event_log_receipt.get('args').get('sender')
        amount_wei = event_log_receipt.get('args').get('amount')
        message_queue.put(
            {'type': 'handle_deposit',
             'sc_address': address_of_sc,
             'tx_hash': HexBytes(event_log_receipt.get('transactionHash', HexBytes('0x0000'))).hex(),
             'recepient': sender,
             'amount': amount_wei})
    elif event_type == 'IssueSigned':
        # _to = event_log_receipt.get('args').get('to')
        # _value_wei = event_log_receipt.get('args').get('value')
        issue_id = event_log_receipt.get('args').get('issueIndex')
        message_queue.put(
            {'type': 'handle_issue_sign',
             'sc_address': address_of_sc,
             'issue_id': issue_id})
    elif event_type == 'IssueProvided':
        issue_id = event_log_receipt.get('args').get('issueIndex')
        message_queue.put(
            {'type': 'handle_issue_provided',
             'sc_address': address_of_sc,
             'issue_id': issue_id})
