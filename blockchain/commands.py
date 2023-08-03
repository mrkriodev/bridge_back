from web3 import Web3
from blockchain.info import first_adr, first_adr_pk, provider_of_sc, abi_of_sc
from web3.types import LogReceipt, HexBytes, TxReceipt


def standard_trx_build_for_sc_call_with_gas(base_adr, provider_url: str) -> dict:
    if base_adr is None:
        return None
    web3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs={'timeout': 60}))

    # build_trx_config = {
    #     'chainId': web3.eth.chain_id,
    #     'from': base_adr,
    #     'gasPrice': web3.eth.gas_price,
    #     'nonce': web3.eth.get_transaction_count(base_adr)
    # }
    # gas_eddition = 50000
    # if not provider_url.index("infura"):
    #     gas_eddition = 100000
    # gas = web3.eth.estimate_gas(build_trx_config) + gas_eddition
    # build_trx_config['gas'] = gas + int(gas * 0.2)
    # build_trx_config['gasPrice'] += int(build_trx_config['gasPrice'] * 0.2)

    build_trx_config = {
        'chainId': web3.eth.chain_id,
        'from': base_adr,
        'nonce': web3.eth.get_transaction_count(base_adr),
        # 'gasPrice': web3.eth.gas_price,
        #'maxFeePerGas': max_fee,  # 30000000000,
        #'maxPriorityFeePerGas': priority_fee  # 3000000000,
    }

    if provider_url.find("infura") != -1:
        base_fee = web3.eth.get_block('latest').baseFeePerGas
        priority_fee = web3.eth.max_priority_fee
        max_fee = priority_fee + 2 * base_fee

        build_trx_config['maxFeePerGas'] = max_fee
        build_trx_config['maxPriorityFeePerGas'] = priority_fee
    else:
        build_trx_config['gasPrice'] = web3.eth.gas_price

    gas_eddition = 1000
    #if provider_url.find("infura") != -1:
    #    gas_eddition = 1000
    gas = web3.eth.estimate_gas(build_trx_config) + gas_eddition
    build_trx_config['gas'] = gas + int(gas * 0.1)

    return build_trx_config


def init_issue_in_msw(guardian_adr=first_adr,
                      guardian_adr_pk=first_adr_pk,
                      recepient_adr: str=first_adr,
                      amount_wei: int = 10000,
                      sc_address=None) -> str:
    if sc_address is None:
        return
    provider_url = provider_of_sc.get(sc_address, '')
    sc_abi = abi_of_sc.get(sc_address, '[]')

    web3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs={'timeout': 60}))
    contract = web3.eth.contract(address=web3.to_checksum_address(sc_address), abi=sc_abi)
    build_trx_config = standard_trx_build_for_sc_call_with_gas(guardian_adr, provider_url)
    build_trx_config['gas'] *= 2

    f = contract.functions.initIssue(web3.to_checksum_address(recepient_adr), amount_wei)
    unsigned_tx = f.build_transaction(build_trx_config)
    signed_tx = web3.eth.account.sign_transaction(unsigned_tx, guardian_adr_pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()
    # Wait for the transaction to be mined, and get the transaction receipt
    #tx_receipt: TxReceipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    #print(tx_receipt)
    #return tx_receipt.get("transactionHash").hex()


def get_issue_signs_in_blockchain(sc_address, issue_index):
    if sc_address is None:
        return
    provider_url = provider_of_sc[sc_address]
    sc_abi = abi_of_sc[sc_address]

    web3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs={'timeout': 60}))
    contract = web3.eth.contract(address=web3.to_checksum_address(sc_address), abi=sc_abi)

    issue_info = contract.functions.getIssue(issue_index).call()
    return int(issue_info[3])


def provide_issue_in_msw(provider_adr=first_adr,
                         provider_adr_pk=first_adr_pk,
                         sc_address=None,
                         issue_index=0):
    if sc_address is None:
        return
    provider_url = provider_of_sc[sc_address]
    sc_abi = abi_of_sc[sc_address]

    web3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs={'timeout': 60}))
    contract = web3.eth.contract(address=web3.to_checksum_address(sc_address), abi=sc_abi)
    build_trx_config = standard_trx_build_for_sc_call_with_gas(provider_adr, provider_url)
    build_trx_config['gas'] *= 2

    f = contract.functions.provideIssue(issue_index)
    unsigned_tx = f.build_transaction(build_trx_config)
    signed_tx = web3.eth.account.sign_transaction(unsigned_tx, provider_adr_pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()
    # Wait for the transaction to be mined, and get the transaction receipt
    #tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    #print(tx_receipt)


def mintWrapCoins(provider_adr=first_adr,
                  provider_adr_pk=first_adr_pk,
                  recepient_adr: str=first_adr,
                  amount_wei: int=10000,
                  sc_address=None,
                  issue_index=0):
    if sc_address is None:
        return
    provider_url = provider_of_sc[sc_address]
    sc_abi = abi_of_sc[sc_address]

    web3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs={'timeout': 60}))
    contract = web3.eth.contract(address=web3.to_checksum_address(sc_address), abi=sc_abi)
    build_trx_config = standard_trx_build_for_sc_call_with_gas(provider_adr, provider_url)
    build_trx_config['gas'] *= 2

    f = contract.functions.mintAndTransferIssue(web3.to_checksum_address(recepient_adr), amount_wei, issue_index)
    unsigned_tx = f.build_transaction(build_trx_config)
    signed_tx = web3.eth.account.sign_transaction(unsigned_tx, provider_adr_pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()
    # Wait for the transaction to be mined, and get the transaction receipt
    #tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    #print(tx_receipt)


def handle_contract_event(event, message_queue):
    print(f"handled event={event}")
    event_log_receipt: LogReceipt = event
    event_type = event_log_receipt.get('event', '')
    address_of_sc = event_log_receipt.get('address', None)
    if event_type == 'Deposit':
        #sender = event_log_receipt.get('args').get('sender')
        amount_wei = event_log_receipt.get('args').get('amount')
        tx_hash = event_log_receipt.get('transactionHash', HexBytes('0x0000')).hex()
        message_queue.put(
            {'type': 'handle_deposit',
             'sc_address': address_of_sc,
             'tx_desposit_hash': tx_hash,
             'recepient':  event_log_receipt.get('args').get('sender'),
             'amount': amount_wei})
    elif event_type == 'IssueInited':
        to_address = event_log_receipt.get('args').get('to')
        value_wei = event_log_receipt.get('args').get('value')
        issue_index = event_log_receipt.get('args').get('issueIndex')
        trx_hash = event_log_receipt.get('transactionHash', HexBytes('0x0000')).hex()
        message_queue.put(
            {'type': 'handle_issue_inited',
             'sc_address': address_of_sc,
             'tx_init_hash': trx_hash,
             'to_address': to_address,
             'value': value_wei,
             'issue_index': issue_index})
    elif event_type == 'IssueSigned':
        issue_index = event_log_receipt.get('args').get('issueIndex')
        message_queue.put(
            {'type': 'handle_issue_sign',
             'sc_address': address_of_sc,
             'issue_index': issue_index})
    elif event_type == 'IssueProvided':
        issue_index = event_log_receipt.get('args').get('issueIndex')
        message_queue.put(
            {'type': 'handle_issue_provided',
             'sc_address': address_of_sc,
             'issue_index': issue_index})
    elif event_type == 'Minted':
        issue_index = event_log_receipt.get('args').get('issueIndex')
        message_queue.put(
            {'type': 'handle_weth_minted',
             'sc_address': address_of_sc,
             'tx_mint_hash': HexBytes(event_log_receipt.get('transactionHash', '0x0000')).hex(),
             'issue_index': issue_index})
