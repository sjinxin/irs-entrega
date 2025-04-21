import csv
import glob
import logging
import os
import typing as t
import uuid
from collections import namedtuple
from datetime import datetime

import attr
import attrs
from tabulate import tabulate
from unidecode import unidecode

# from irs import SaleRecord

_logger = logging.getLogger(__name__)


def normalize(in_str):
    if in_str:
        return unidecode(in_str).strip().replace(" ", "_").lower()
    return f"empty_field"


@attrs.define
class Transaction:
    date: t.Optional[datetime.date] = None
    unit: int = 0
    unit_value: float = 0
    value: float = 0
    commission: float = 0


@attrs.define
class Order:
    isin: str
    name: str
    order_id: str
    unit: int = 0
    unrealized_unit: t.Optional[int] = None
    value: float = 0
    commission: float = 0
    txn_list: t.List["Transaction"] = attr.ib(factory=list)
    split: bool = False

    @property
    def unit_value(self):
        return self.value / self.unit

    @property
    def order_type(self):
        if self.unit > 0 and self.value < 0:
            return "BUY"
        elif self.unit < 0 and self.value > 0:
            return "SELL"
        raise RuntimeError(f"unknown order type {self}!")

    def update(self, txn):
        self.txn_list.append(txn)
        self.commission += txn.commission
        self.unit += txn.unit
        self.value += txn.value
        self.unrealized_unit = abs(self.unit)

    @property
    def date(self):
        return self.txn_list[0].date

    @property
    def declared(self):
        return self.unrealized_unit == 0

    def cost_for_unit(self, unit):
        commision = abs(self.commission)
        order_unit = abs(self.unit)
        if self.declared:
            return commision - commision / order_unit * (order_unit - unit)
        return commision / order_unit * unit

    def __lt__(self, other):
        return self.txn_list[0].date < other.txn_list[0].date


@attrs.define
class Product:
    isin: str
    name: str
    unit: int = 0
    order_history: t.List["Order"] = attr.ib(factory=list)

    def update(self, order):
        self.order_history.append(order)
        self.unit += order.unit

    @property
    def sell_orders(self):
        return [
            order
            for order in sorted(self.order_history)
            if order.order_type == "SELL" and (not order.split)
        ]

    @property
    def buy_orders(self):
        return [
            order for order in sorted(self.order_history) if order.order_type == "BUY"
        ]

    def declare(self):

        records = []

        for sell_order in self.sell_orders:
            # _logger.debug(f"Processing order {sell_order.name}: {sell_order.unit}")
            for buy_order in self.buy_orders:
                if buy_order.unrealized_unit == 0:
                    continue
                # _logger.debug(f"Matching buy order {buy_order.name}")
                unit_to_declare = min(
                    sell_order.unrealized_unit, buy_order.unrealized_unit
                )
                buy_order.unrealized_unit -= unit_to_declare
                sell_order.unrealized_unit -= unit_to_declare

                if buy_order.declared or sell_order.declared:
                    record = dict(
                        realization_date=sell_order.date,
                        realization_value=abs(sell_order.unit_value) * unit_to_declare,
                        acquisition_date=buy_order.date,
                        acquisition_value=abs(buy_order.unit_value) * unit_to_declare,
                        expenses=sell_order.cost_for_unit(unit_to_declare)
                        + buy_order.cost_for_unit(unit_to_declare),
                        note=f"{self.name}[{self.isin}] {unit_to_declare}/{abs(sell_order.unit)}",
                    )
                    records.append(record)
                if sell_order.declared:
                    break
        return records


@attrs.define
class Portfolio:
    products: t.List["Product"] = attr.ib(factory=list)
    order_history: t.List["Order"] = attr.ib(factory=list)

    def update(self, order):
        if (product := self.get_product(order.isin)) is None:
            product = Product(isin=order.isin, name=order.name)
            self.products.append(product)
        product.update(order)

    def get_product(self, isin):
        for product in self.products:
            if product.isin == isin:
                return product
        return None

    def get_order(self, order_id: str):
        for order in self.order_history:
            if order.order_id == order_id:
                return order
        return None

    def open_position(self):
        open_positions = [p for p in self.products if p.unit > 0]
        positions_by_name = sorted(open_positions, key=lambda p: p.name.lower())
        headers = ["Product", "ISIN", "Unit"]
        table_data = [(p.name, p.isin, p.unit) for p in positions_by_name]
        return tabulate(
            table_data,
            headers,
            tablefmt="pretty",
            colalign=("left", "center", "right"),
        )

    @classmethod
    def from_transaction_csv_files(cls, input_dir):
        instance = cls()
        instance.load(cls.read(input_dir))
        return instance

    def load(self, data):
        for item in data:
            # _logger.debug(f"process line {item.produto}")
            order_id = item.id_da_ordem
            isin = item.isin
            name = item.produto
            txn = Transaction(
                date=datetime.strptime(item.data, "%d-%m-%Y"),
                value=float(item.valor),
                unit=int(item.quantidade),
                unit_value=item.precos,
                commission=float(item.custos_de_transacao or "0.0"),
            )
            split = False
            if not order_id:
                _logger.warning("transaction without order_id %s", txn)
                order_id = uuid.uuid4()
                split = True

            if (order := self.get_order(order_id)) is None:
                order = Order(isin=isin, name=name, order_id=order_id, split=split)
                self.order_history.append(order)

            if order:
                order.update(txn)

        for order in self.order_history:
            self.update(order)

    @staticmethod
    def read(input_dir) -> t.List:
        data = set()
        # Replace with your field names
        for file_path in glob.glob(os.path.join(input_dir, "*.csv")):
            with open(file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                fields = list(map(normalize, dict.fromkeys(reader.fieldnames)))
                Row = namedtuple("Row", fields)
                for row in reader:
                    data.add(Row(*row.values()))
        return sorted(list(data))

    def declare(self) -> t.Tuple[t.List[t.Tuple], t.Optional[t.List]]:
        records = []
        for prod in self.products:
            _logger.debug(f"declare for {prod.name}")
            records.extend(prod.declare())
        return records, None

    def summary(self):
        _logger.info("portfolio summary: \n")
        _logger.info("%d products in portfolio", len(self.products))
        _logger.info("order history:")
        for prod in self.products:
            _logger.info(
                "   product %s[%s]: %d order history",
                prod.name,
                prod.isin,
                len(prod.order_history),
            )
            for order in prod.order_history:
                _logger.info(
                    """     order %s: type %s txn %d, unit: %d, value: %f""",
                    order.order_id,
                    order.order_type,
                    len(order.txn_list),
                    order.unit,
                    order.value,
                )
        _logger.info("\n" + self.open_position())
