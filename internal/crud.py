from typing import List

from internal.swap_model import SwapTransaction, Issue, SwapDirection
from sqlalchemy import select, and_
import sqlalchemy.exc


def get_swap_trx_info(session, txid) -> dict:
    stmt = select(SwapTransaction).where(SwapTransaction.id == txid)
    result: SwapTransaction = session.execute(stmt).scalar()
    stmt = select(Issue).where(Issue.id == result.issue_id)
    result.issue = session.execute(stmt).scalar()
    print(result.to_json())
    return result.to_json()


def total_swaps(session) -> List[int]:
    stmt = select(SwapTransaction.id).order_by(SwapTransaction.id.desc())
    swap_trx_ids = session.execute(stmt).scalars().all()
    return swap_trx_ids


def add_new_issue(session, address="", amount=0, direction=SwapDirection.NO_DIRECTION, id_in_contract=0) -> int:
    issue = Issue(_adr=address, _amount=amount, _dir=direction, _id_in_contract=id_in_contract)
    session.add(issue)
    session.flush()
    return issue.id


def add_new_swap(session, issue_trx_hash="", hash_from=""):
    st = SwapTransaction(_trx_init_hash=issue_trx_hash, _hash_from=hash_from)
    try:
        session.add(st)
        session.commit()  # сохраняем изменения
    except sqlalchemy.exc as serr:
        print(f"in add_new_swap error={serr}")
        session.rollback()


def set_swap_issue(session, issue_trx_hash="", issue_id=0):
    stmt = select(SwapTransaction).where(SwapTransaction.trx_init_hash == issue_trx_hash)
    st: SwapTransaction = session.execute(stmt).scalar()

    try:
        st.issue_id = issue_id
        session.commit()  # сохраняем изменения
    except sqlalchemy.exc as serr:
        print(f"in set_swap_issue error={serr}")
        session.rollback()


def set_swap_hash_to(session, issue_index=0, direction=SwapDirection.NO_DIRECTION, hash_to=""):
    stmt = select(Issue).where(and_(Issue.id_in_contract == issue_index,
                                    Issue.direct == direction.value))
    issue: Issue = session.execute(stmt).scalar()

    stmt = select(SwapTransaction).where(SwapTransaction.issue_id == issue.id)
    st: SwapTransaction = session.execute(stmt).scalar()
    try:
        st.hash_to = hash_to
        session.commit()  # сохраняем изменения
    except sqlalchemy.exc as serr:
        print(f"in set_swap_hash_to error={serr}")
        session.rollback()


def set_issue_signs(session, signs=0, issue_index=0, direction=SwapDirection.NO_DIRECTION):
    stmt = select(Issue).where(and_(Issue.id_in_contract == issue_index,
                                    Issue.direct == direction.value))
    issue: Issue = session.execute(stmt).scalar()
    try:
        issue.num_signs = signs
        session.commit()  # сохраняем изменения
    except sqlalchemy.exc as serr:
        print(f"in set_issue_signs error={serr}")
        session.rollback()


def set_issue_status(session, issue_index=-1, direction=SwapDirection.NO_DIRECTION, status=False):
    if issue_index == -1:
        return
    stmt = select(Issue).where(and_(Issue.id_in_contract == issue_index,
                                    Issue.direct == direction.value))
    issue: Issue = session.execute(stmt).scalar()
    try:
        issue.status = status
        session.commit()  # сохраняем изменения
    except sqlalchemy.exc as serr:
        print(f"in set_issue_status error={serr}")
        session.rollback()


def get_issue_adr_amount(session, issue_index=-1, direction=SwapDirection.NO_DIRECTION, status=False):
    if issue_index == -1:
        return
    stmt = select(Issue).where(and_(Issue.id_in_contract == issue_index,
                                    Issue.direct == direction.value))
    issue: Issue = session.execute(stmt).scalar()
    return issue.address, issue.amount


def set_issue_providing(session, issue_index=0, direction=SwapDirection.NO_DIRECTION, providing_status=False):
    stmt = select(Issue).where(and_(Issue.id_in_contract == issue_index,
                                    Issue.direct == direction.value))
    issue: Issue = session.execute(stmt).scalar()
    try:
        issue.providing = providing_status
        session.commit()  # сохраняем изменения
    except sqlalchemy.exc as serr:
        print(f"in set_issue_providing error={serr}")
        session.rollback()


def is_issue_providing(session, issue_index=0, direction=SwapDirection.NO_DIRECTION):
    result = False
    stmt = select(Issue).where(and_(Issue.id_in_contract == issue_index,
                                    Issue.direct == direction.value))
    issue: Issue = session.execute(stmt).scalar()
    if issue:
        result = issue.providing
    return result