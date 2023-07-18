import sqlite3
from sqlalchemy.exc import IntegrityError
from internal.swap_model import SwapTransaction, Issue
import os
from internal.db_manager import get_db_session

path_to_test_records = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_trx.csv')


def load_exist_trxs(swap_trxs: dict):
    trxs_data_file_name = path_to_test_records
    m_session = get_db_session().send(None)
    with open(trxs_data_file_name, 'r') as file:
        for line in file:
            st: SwapTransaction = SwapTransaction.from_csv(csv_string=line, delimiter=';')
            swap_trxs[st.id] = st.to_json()
            issue = st.issue
            m_session.add(issue)
            m_session.flush()
            st.issue.id = issue.id
            st.issue_id = issue.id
            try:
                m_session.add(st)
                m_session.commit()  # сохраняем изменения
            except IntegrityError as ierr:
                print(f"first={ierr}")
                m_session.rollback()
                continue
            print(st.to_json())
    m_session.close()
