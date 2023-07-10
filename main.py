from web3 import Web3
from web3.types import LogReceipt
import asyncio
import threading
import queue
import time
from datetime import datetime
from internal.swap_data import SwapTransaction
from blockchain.eth_event_handler import event_filters, handle_event

from fastapi import FastAPI
import uvicorn

message_queue = queue.Queue()
swap_trxs = {}

app = FastAPI()


# Additional loop and touch event handling
async def touch_event_loop(ef):
    while True:
        for event_filter in ef:
            for SomeEventArrived in event_filter.get_new_entries():
                handle_event(SomeEventArrived)
            await asyncio.sleep(1)
        # Simulating touch event and pushing message with current timestamp to the queue
        # current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # message = f"Touch event occurred at {current_time}"
        # message_queue.put(message)
        #
        # await asyncio.sleep(5)  # Example: 0.1 second interval between touch events


def load_exist_trxs():
    trxs_data_file_name = "c:\\Develop\\ts\\bridge_back\\data_trx.csv"
    with open(trxs_data_file_name, 'r') as file:
        for line in file:
            st: SwapTransaction = SwapTransaction.from_csv(csv_string=line, delimiter=';')
            swap_trxs[st.id] = st.to_json()
            print(st.to_json())


@app.on_event("startup")
async def startup_event():
    # Start the touch event loop in a separate task
    asyncio.create_task(touch_event_loop(event_filters))

    # Start a separate thread to read messages from the queue
    queue_thread = threading.Thread(target=read_queue_messages, args=(message_queue,))
    queue_thread.start()


def read_queue_messages(message_queue):
    while True:
        # Retrieve and log message from the queue
        message = message_queue.get()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Received message: {message} (Timestamp: {timestamp})")


# API endpoint for /api/status
@app.get("/api/status/{item_id}")
async def get_status(item_id: int = None):
    if item_id:
        return [item for item in swap_trxs if item['id'] == item_id]
        time.sleep(7)
    return 'not'


def main():
    load_exist_trxs()
    #uvicorn.run(app, host="0.0.0.0", port=8080)


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
