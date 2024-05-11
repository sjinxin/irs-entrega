import typing as t
from datetime import datetime

# from degiro.import Portfolio
import attrs
import attr
import logging
from tabulate import tabulate

logging.basicConfig(level=logging.DEBUG)

_logger = logging.getLogger(__name__)


@attrs.define
class Country:
    name: str
    code: int


@attrs.define
class Code:
    name: str
    clause: str

    def __str__(self) -> str:
        return f"{self.name} - {self.clause}"


@attrs.define
class SaleRecord:
    """Alienação Onerosa de Partes Sociais e Outros Valores Mobiliários [art.º 10.º, n.º 1, al. b), do CIRS]"""

    linha: int = 951
    coutry_of_origin: t.Optional[Country] = None
    code: t.Optional[Code] = None
    realization_date: t.Optional[datetime] = None
    realization_value: t.Optional[float] = None
    acquisition_date: t.Optional[datetime] = None
    acquisition_value: t.Optional[float] = None
    expenses: t.Optional[float] = None
    note: str = ""

    @property
    def profit(self):
        return self.realization_value - self.acquisition_date


@attrs.define
class CapitalGains:
    """9.2 Incrementos Patrimoniais de Opção de Englobamento"""

    sales_of_shares_and_securities: t.List[SaleRecord] = attr.field(factory=list)

    def declare(self, sales):
        for sale in sales:
            line = SaleRecord(**sale)
            _logger.debug(line)


@attrs.define
class Quadro9:
    """9 Rendimentos de Incrementos Patrimoniais (Categoria G)."""

    cap_gains: CapitalGains = attr.field(factory=CapitalGains)

    def declare(self, sales):
        self.cap_gains.declare(sales)


@attrs.define
class AnexoJ:
    """Anexo J. Rendimentos Obitidos no Estrangeiro"""

    quadro9: Quadro9 = attr.field(factory=Quadro9)

    def declare(self, sales):
        self.quadro9.declare(sales)


@attrs.define
class IRS:
    annex_j: AnexoJ = attr.field(factory=AnexoJ)

    def declare(self, sales, fiscal_year):
        self.annex_j.declare(sales)
