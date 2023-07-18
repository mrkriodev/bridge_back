import asyncio
import threading
import time
from datetime import datetime
from blockchain.eth_event_handler import eth_event_filters, handle_eth_event, eth_message_queue
from blockchain.sibr_event_handler import sibr_event_filters, handle_sibr_event, sibr_message_queue
from blockchain.commands import init_issue_in_msw, provide_issue_in_msw, get_issue_signs
from internal.swap_loader import load_exist_trxs
from internal.db_manager import get_db_session
from sqlalchemy.orm import Session
from internal.crud import get_swap_trx_info, total_swaps, add_new_issue, add_new_swap, \
    set_issue_providing, is_issue_providing, set_issue_signs, set_issue_status
from internal.swap_model import SwapDirection

from fastapi import FastAPI, Depends, HTTPException
import uvicorn

app = FastAPI()
swap_trxs = {}


def read_queue_messages(message_queue):
    while True:
        # Retrieve and log message from the queue
        message = message_queue.get()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Received message: {message} (Timestamp: {timestamp})")
        m_type = message.get('type', '')
        m_sc_address = message.get('sc_address', '')
        trx_hash = message.get('tx_hash', '')
        session = next(get_db_session())
        try:
            if m_type == 'handle_deposit':
                init_issue_in_msw(sc_address=m_sc_address,
                                 recepient_adr=message.get('recepient'),
                                 amount_wei=int(message.get('amount')))
                direction = SwapDirection.FROM_ETH_TO_SIBR if message_queue == eth_message_queue \
                    else SwapDirection.FROM_SIBR_TO_ETH
                issue_id = add_new_issue(session, message.get('recepient'), int(message.get('amount')))
                add_new_swap(session, issue_id, direction, trx_hash)
            elif m_type == 'handle_issue_sign':
                m_issue_id = int(message.get('issue_id', -1))
                if m_issue_id != -1:
                    issue_signs = get_issue_signs(sc_address=m_sc_address, issue_id=m_issue_id)
                    set_issue_signs(session, issue_signs)
                    if issue_signs >= 2 and not is_issue_providing(session, m_issue_id):
                        provide_issue_in_msw(sc_address=m_sc_address,
                                             issue_id=m_issue_id)
                        set_issue_providing(m_issue_id, True)
            elif m_type == 'handle_issue_provided':
                m_issue_id = int(message.get('issue_id', -1))
                set_issue_status(session, m_issue_id, True)
                print(f"providing issue_id = {m_issue_id}")
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
    asyncio.create_task(eth_events_handler(eth_event_filters, 1))
    asyncio.create_task(sibr_events_handler(sibr_event_filters, 1))

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
    # return {"id": swap_tx_info.get('id'),
    #         "status": swap_tx_info.get('status'),
    #         "signs": int(swap_tx_info.get('num_signs')),
    #         "direction": int(swap_tx_info.get('direction')),
    #         "amount": int(swap_tx_info.get('amount')),
    #         "address": swap_tx_info.get('address'),
    #         "hash_to": swap_tx_info.get('hash_to'),
    #         "hash_from": swap_tx_info.get('hash_from')}


@app.get("/api/total")
async def get_total_swaps(session: Session = Depends(get_db_session)):
    swap_txs_ids = total_swaps(session)
    if swap_txs_ids is None:
        raise HTTPException(status_code=404, detail="error")
    return {"count": len(swap_txs_ids),
            "ids": swap_txs_ids}


@app.get("/api/swaps/")
async def get_swaps(start: int = 0, limit: int = 20, session: Session = Depends(get_db_session)):
    swap_txs_ids = total_swaps(session)
    if swap_txs_ids is None:
        raise HTTPException(status_code=404, detail="error")
    result = []
    for swap_tx_id in swap_txs_ids[start: start+limit]:
        swap_tx_info = get_swap_trx_info(session, swap_tx_id)
        result.append(swap_tx_info)
    return result


def main():
    load_exist_trxs(swap_trxs)
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
