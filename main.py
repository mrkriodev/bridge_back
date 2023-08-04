import asyncio
import threading
import time
from datetime import datetime
from blockchain.eth_event_handler import eth_event_filters, handle_eth_event, eth_message_queue
from blockchain.sibr_event_handler import sibr_event_filters, handle_sibr_event, sibr_message_queue
from blockchain.commands import init_issue_in_msw, provide_issue_in_msw, get_issue_signs_in_blockchain, mintWrapCoins, \
    submitRevertTransaction, get_trx_confirms_in_blockchain, execute_trx_in_msw, send_faucet_coins, \
    simple_send_coins_in_eth
from internal.swap_loader import load_exist_trxs
from internal.db_manager import get_db_session
from sqlalchemy.orm import Session
from internal.crud import get_swap_trx_info, total_swaps, add_new_issue, add_new_swap, \
    set_issue_providing, is_issue_providing, set_issue_signs, set_issue_status, set_swap_issue, get_issue_adr_amount, \
    set_swap_hash_to
from internal.swap_model import SwapDirection
from blockchain.info import goerli_ms_sc_adr, sibr_ms_sc_adr, sibr_weths_sc_adr, goerli_wsibr_adr, \
    goerl_fuacet_guids, sibr_fuacet_guids, goerli_faucet_adr, sibr_faucet_adr

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app = FastAPI()
swap_trxs = {}

deposit_net_opposite_ms_issuer_sc = {
    SwapDirection.FROM_ETH_TO_SIBR: sibr_ms_sc_adr,
    SwapDirection.FROM_SIBR_TO_ETH: goerli_ms_sc_adr
}

wrap_coins_opposite_ms_issuer_sc_network = {
    SwapDirection.FROM_ETH_TO_SIBR: sibr_weths_sc_adr,
    SwapDirection.FROM_SIBR_TO_ETH: goerli_wsibr_adr
}


def read_queue_messages(message_queue):
    while True:
        # Retrieve and log message from the queue
        message = message_queue.get()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Received message: {message} (Timestamp: {timestamp})")
        session = next(get_db_session())
        try:
            m_type = message.get('type', '')
            m_sc_address = str(message.get('sc_address', ''))
            m_direction = SwapDirection.FROM_ETH_TO_SIBR if message_queue == eth_message_queue \
                else SwapDirection.FROM_SIBR_TO_ETH
            if m_type == 'handle_deposit':
                trx_deposit_hash = message.get('tx_desposit_hash', '')
                while True:
                    try:
                        trx_init_hash = init_issue_in_msw(sc_address=m_sc_address,
                                                          # sc_address=deposit_net_opposite_ms_issuer_sc[m_direction],
                                                          recepient_adr=str(message.get('recepient')),
                                                          amount_wei=int(message.get('amount')))
                        add_new_swap(session, issue_trx_hash=trx_init_hash, hash_from=trx_deposit_hash)
                        break
                    except ValueError as excp:
                        if isinstance(excp, dict):
                            resp_code = excp.get("code")
                            print(f"error={resp_code}")
                            if resp_code == -32000:
                                message = excp.get("message", "")
                                if message == 'replacement transaction underpriced':
                                    time.sleep(3)
                                    continue
            elif m_type == 'handle_issue_inited':
                trx_init_hash = message.get('tx_init_hash', '')
                m_issue_id = add_new_issue(session,
                                           address=message.get('to_address'),
                                           amount=int(message.get('value')),
                                           direction=m_direction,
                                           id_in_contract=int(message.get('issue_index')))
                set_swap_issue(session, issue_trx_hash=trx_init_hash, issue_id=m_issue_id)
            elif m_type == 'handle_issue_sign':
                m_id_in_contract = int(message.get('issue_index'))

                issue_signs = get_issue_signs_in_blockchain(sc_address=m_sc_address,
                                                            issue_index=m_id_in_contract)
                set_issue_signs(session,
                                signs=issue_signs,
                                issue_index=m_id_in_contract,
                                direction=m_direction)

                if issue_signs >= 2 and not is_issue_providing(session,
                                                               issue_index=m_id_in_contract,
                                                               direction=m_direction):
                    while True:
                        try:
                            provide_issue_in_msw(sc_address=m_sc_address,
                                                 issue_index=m_id_in_contract)
                            set_issue_providing(session,
                                                issue_index=m_id_in_contract,
                                                direction=m_direction,
                                                providing_status=True)
                            break
                        except ValueError as excp:
                            if isinstance(excp, dict):
                                resp_code = excp.get("code")
                                print(f"error={resp_code}")
                                if resp_code == -32000:
                                    message = excp.get("message", "")
                                    if message == 'replacement transaction underpriced':
                                        time.sleep(3)
                                        continue
            elif m_type == 'handle_issue_provided':
                m_id_in_contract = int(message.get('issue_index'))

                set_issue_status(session, issue_index=m_id_in_contract, direction=m_direction, status=True)
                print(f"issue_id provided = {m_id_in_contract}")
                m_recepient, m_amount_wei = get_issue_adr_amount(session,
                                                                 issue_index=m_id_in_contract, direction=m_direction)
                # start to mint coins in opposite network
                # coins should mint only in opposite network.
                m_trx_mint_hash = mintWrapCoins(sc_address=wrap_coins_opposite_ms_issuer_sc_network[m_direction],
                                              recepient_adr=m_recepient,
                                              amount_wei=m_amount_wei,
                                              issue_index=m_id_in_contract)
                set_swap_hash_to(session,
                                 issue_index=m_id_in_contract,
                                 direction=m_direction,
                                 hash_to=m_trx_mint_hash)
            elif m_type == 'handle_wrap_coin_minted':
                m_id_in_contract = int(message.get('issue_index', -1))
                m_trx_mint_hash = message.get('tx_mint_hash', '')
                # coins should mint only in opposite network.
                opposite_direction = SwapDirection.FROM_ETH_TO_SIBR if m_direction == SwapDirection.FROM_SIBR_TO_ETH \
                    else SwapDirection.FROM_SIBR_TO_ETH
                print(f"coins minted {m_id_in_contract} in {m_direction.value}")
            elif m_type == 'handle_wrap_coins_reverted':
                # start to mint coins in opposite network
                # coins should mint only in opposite network.
                m_recepient = message.get('recepient')
                m_amount_wei = message.get('amount')
                submitRevertTransaction(sc_address=deposit_net_opposite_ms_issuer_sc[m_direction],
                                        recepient_adr=m_recepient,
                                        amount_wei=m_amount_wei)
            elif m_type == 'handle_transaction_confirm':
                m_trx_id_in_contract = int(message.get('trx_index'))
                trx_confirms = get_trx_confirms_in_blockchain(sc_address=m_sc_address,
                                                              trx_index=m_trx_id_in_contract)
                if trx_confirms >= 2:
                    while True:
                        try:
                            execute_trx_in_msw(sc_address=m_sc_address,
                                               trx_index=m_id_in_contract)
                            break
                        except ValueError as excp:
                            if isinstance(excp, dict):
                                resp_code = excp.get("code")
                                print(f"error={resp_code}")
                                if resp_code == -32000:
                                    message = excp.get("message", "")
                                    if message == 'replacement transaction underpriced':
                                        time.sleep(3)
                                        continue
        finally:
            session.close()


async def eth_events_handler(event_filters, poll_interval):
    while True:
        for event_filter in event_filters:
            for SomeEventArrived in event_filter.get_new_entries():
                handle_eth_event(SomeEventArrived)
            await asyncio.sleep(poll_interval)


async def sibr_events_handler(event_filters, poll_interval):
    while True:
        for event_filter in event_filters:
            for SomeEventArrived in event_filter.get_new_entries():
                handle_sibr_event(SomeEventArrived)
            await asyncio.sleep(poll_interval)


def test_eth():
    eth_message_queue.put({
        'type': 'handle_deposit',
        'sc_address': "0x00001",
        'tx_hash': "0x0000",
        'recepient': "0xasdf",
        'amount': 112345678}
    )


@app.on_event("startup")
async def startup_event():
    # Start the touch event loop in a separate task
    asyncio.create_task(eth_events_handler(eth_event_filters, 3))
    asyncio.create_task(sibr_events_handler(sibr_event_filters, 3))

    # Start a separate thread to read messages from the queue
    queue_thread = threading.Thread(target=read_queue_messages, args=(eth_message_queue,))
    queue_thread.start()
    queue_thread = threading.Thread(target=read_queue_messages, args=(sibr_message_queue,))
    queue_thread.start()


# API endpoint for /api/status
@app.get("/api/status/{swap_tx_id}")
async def get_status(swap_tx_id: int = None, session: Session = Depends(get_db_session)):
    if not swap_tx_id:
        raise HTTPException(status_code=404, detail="tx_id not set")
    swap_tx_info = get_swap_trx_info(session, swap_tx_id)
    if swap_tx_info is None:
        raise HTTPException(status_code=404, detail="TX not found")
    return swap_tx_info


@app.get("/api/total")
async def get_total_swaps(session: Session = Depends(get_db_session)):
    swap_txs_ids = total_swaps(session)
    if swap_txs_ids is None:
        raise HTTPException(status_code=404, detail="error")
    return {"count": len(swap_txs_ids),
            "ids": swap_txs_ids}


@app.get("/api/swaps")
async def get_swaps(start: int = 0, limit: int = 20, session: Session = Depends(get_db_session)):
    swap_txs_ids = total_swaps(session)
    if swap_txs_ids is None:
        raise HTTPException(status_code=404, detail="error")
    result = []
    for swap_tx_id in swap_txs_ids[start: start+limit]:
        swap_tx_info = get_swap_trx_info(session, swap_tx_id)
        result.append(swap_tx_info)
    return result


# Pydantic model to validate the JSON schema
class FaucetRequest(BaseModel):
    address: str
    guid: str


@app.post("/api/getcoins")
async def to_faucet_coins(request_data: FaucetRequest):
    m_guid = request_data.guid
    trx_hash = "0x1"
    if m_guid is None:
        raise HTTPException(status_code=404, detail="error")
    if m_guid in sibr_fuacet_guids:
        send_faucet_coins(sibr_faucet_adr, request_data.address)
    elif m_guid in goerl_fuacet_guids:
        #send_faucet_coins(goerli_faucet_adr, request_data.address)
        trx_hash = simple_send_coins_in_eth(request_data.address)
    return {'sended': trx_hash}


def main():
    #load_exist_trxs(swap_trxs)
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()

# def run():
#     main()
#
# def main():
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
#
# if __name__ == "__main__":
#     asyncio.run(run())
