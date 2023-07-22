import json
import csv
import os
from enum import Enum
# from json import JSONEncoder
from sqlalchemy import Column, ForeignKey, Date, Integer, String, SmallInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base

from internal.db_manager import engine_db

Base = declarative_base()


class SwapDirection(Enum):
    NO_DIRECTION = 0
    FROM_ETH_TO_SIBR = 1
    FROM_SIBR_TO_ETH = 2


class Issue(Base):
    __tablename__ = 'issue'

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Boolean, default=False)
    num_signs = Column(Integer, default=0)
    address = Column(String(32), default="")
    direct = Column(Integer, default=0)
    amount = Column(Integer, default=0)
    providing = Column(Boolean, default=False)
    id_in_contract = Column(Integer, default=0)

    def __init__(self, _status=False, _ns=0, _adr="0x0", _amount=0,  _dir=SwapDirection.NO_DIRECTION, _id_in_contract=0):
        self.status: bool = _status
        self.num_signs = _ns
        self.address: str = _adr
        self.direct: int = _dir.value
        self.amount = _amount
        self.providing = False
        self.id_in_contract = _id_in_contract

    def to_json(self):
        return json.dumps(self.__dict__)

    def as_array(self):
        return [self.status, self.num_signs, self.address, self.amount, self.direct]

    def as_dict(self):
        return self.__dict__

    def to_json(self):
        return {'status': self.status,
                'num_signs': self.num_signs,
                'address': self.address,
                'amount': self.amount,
                'direction': self.direct}

    def to_csv(self, filename):
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.as_array())


class SwapTransaction(Base):
    __tablename__ = 'swap'

    id = Column(Integer, primary_key=True, autoincrement=True)
    trx_init_hash = Column(String(64), unique=True, default="")
    hash_from = Column(String(64), default="")
    hash_to = Column(String(64), default="")
    issue_id = Column(Integer, ForeignKey("issue.id"))

    def __init__(self, _trx_init_hash="", _hash_from="", _hash_to="", _issue=Issue()):
        self.hash_from = _hash_from
        self.hash_to = _hash_to
        self.trx_init_hash = _trx_init_hash
        self.issue: Issue = _issue
        self.issue_id: int = _issue.id

    def as_array(self):
        return [self.id, self.hash_from, self.hash_to]

    def to_csv(self, filename):
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            row_data = self.as_array() + self.issue.as_array()
            writer.writerow(row_data)

    @classmethod
    def from_csv(cls, csv_string, delimiter=';'):
        row = csv_string.strip().split(delimiter)
        m_dir = SwapDirection(int(row[0]))
        issue = Issue(_status=bool(int(row[4])),
                      _ns=int(row[5]),
                      _adr=str(row[6]).strip('"'),
                      _amount=int(row[7]),
                      _dir=m_dir,
                      _id_in_contract=int(row[8]))
        return cls(_issue=issue,
                   _hash_from=str(row[1]).strip('"'),
                   _trx_init_hash=str(row[2]).strip('"'),
                   _hash_to=str(row[3]).strip('"'))

    def to_json(self):
        as_dict = {'id': self.id,
                   'hash_to': self.hash_to,
                   'hash_from': self.hash_from}
        as_dict.update(self.issue.to_json())
        return as_dict


Base.metadata.create_all(engine_db)
