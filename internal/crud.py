from typing import List

from internal.swap_model import SwapTransaction, Issue, SwapDirection
from sqlalchemy import select
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


def add_new_issue(session, address="", amount=0) -> int:
    issue = Issue(_adr=address, _amount=amount)
    session.add(issue)
    session.flush()
    return issue.id


def add_new_swap(session, issue_id=0, direction=SwapDirection.NO_DIRECTION, hash_from="", hash_to=""):
    stmt = select(Issue).where(Issue.id == issue_id)
    issue: Issue = session.execute(stmt).scalar()
    st = SwapTransaction(_dir=direction, _issue=issue, _hash_from=hash_from, _hash_to=hash_to)
    try:
        session.add(st)
        session.commit()  # сохраняем изменения
    except sqlalchemy.exc as serr:
        print(f"in add_new_swap error={serr}")
        session.rollback()


def set_issue_signs(session, issue_id=0, signs=0):
    stmt = select(Issue).where(Issue.id == issue_id)
    issue: Issue = session.execute(stmt).scalar()
    try:
        issue.num_signs = signs
        session.commit()  # сохраняем изменения
    except sqlalchemy.exc as serr:
        print(f"in set_issue_providing error={serr}")
        session.rollback()


def set_issue_status(session, issue_id, status=False):
    stmt = select(Issue).where(Issue.id == issue_id)
    issue: Issue = session.execute(stmt).scalar()
    try:
        issue.status = status
        session.commit()  # сохраняем изменения
    except sqlalchemy.exc as serr:
        print(f"in set_issue_providing error={serr}")
        session.rollback()


def set_issue_providing(session, issue_id=0, providing_status=False):
    stmt = select(Issue).where(Issue.id == issue_id)
    issue: Issue = session.execute(stmt).scalar()
    try:
        issue.providing = providing_status
        session.commit()  # сохраняем изменения
    except sqlalchemy.exc as serr:
        print(f"in set_issue_providing error={serr}")
        session.rollback()


def is_issue_providing(session, issue_id=0):
    result = False
    stmt = select(Issue).where(Issue.id == issue_id)
    issue: Issue = session.execute(stmt).scalar()
    if issue:
        result = issue.providing
    return result
