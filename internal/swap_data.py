import json
import csv
from enum import Enum
from json import JSONEncoder


class SwapDirection(Enum):
    NO_DIRECTION = 0
    FROM_ETH_TO_SIBR = 1
    FROM_SIBR_TO_ETH = 2


class Issue:
    def __init__(self, _status=False, _ns=0, _adr="0x0", _amount=0):
        self.status = _status
        self.numSigns = _ns
        self.address: str = ""
        self.amount = _amount

    def to_json(self):
        return json.dumps(self.__dict__)

    def as_array(self):
        return [self.status, self.numSigns, self.address, self.amount]

    def as_dict(self):
        return self.__dict__

    def to_csv(self, filename):
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.as_array())


class SwapTransaction:
    def __init__(self, _id=-1, _issue=Issue(), _dir=SwapDirection.NO_DIRECTION):
        self.id = _id
        self.direct = _dir
        self.hash_from = ""
        self.hash_to = ""
        self.issue: Issue = _issue

    def as_array(self):
        return [self.id, self.direct.value, self.hash_from, self.hash_to]

    def to_csv(self, filename):
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            row_data = self.as_array() + self.issue.as_array()
            writer.writerow(row_data)

    @classmethod
    def from_csv(cls, csv_string, delimiter=','):
        row = csv_string.strip().split(delimiter)
        _id = int(row[0])
        _dir = SwapDirection(int(row[1]))
        _issue = Issue(bool(row[4]), int(row[5]), row[6], int(row[7]))
        return cls(_id, _issue, _dir)

    def to_json(self):
        as_dict = {'id': self.id,
                   'direction': self.direct.value,
                   'hash_to': self.hash_to,
                   'hash_from': self.hash_from}
        as_dict.update(self.issue.as_dict())
        return json.dumps(as_dict)

