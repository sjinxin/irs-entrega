import typing as t
from datetime import datetime
import xml.etree.ElementTree as ET

import attrs
import attr
import logging
import pathlib
from tabulate import tabulate

logging.basicConfig(level=logging.DEBUG)

_logger = logging.getLogger(__name__)

XML_NS = "{http://www.dgci.gov.pt/2009/Modelo3IRSv2024}"


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

    def generate_content(self, parent, ns, line: SaleRecord):
        linha = ET.SubElement(parent, f"{ns}AnexoJq092AT01-Linha")
        linha.set("numero", str(line.linha))
        ET.SubElement(linha, f"{ns}NLinha").text = str(line.linha)
        ET.SubElement(linha, f"{ns}CodPais").text = str(line.coutry_of_origin)
        ET.SubElement(linha, f"{ns}Codigo").text = str(line.code)
        ET.SubElement(linha, f"{ns}AnoRealizacao").text = str(
            line.realization_date.year
        )
        ET.SubElement(linha, f"{ns}MesRealizacao").text = str(
            line.realization_date.month
        )
        ET.SubElement(linha, f"{ns}DiaRealizacao").text = str(line.realization_date.day)
        ET.SubElement(linha, f"{ns}ValorRealizacao").text = str(
            round(line.realization_value, 2)
        )
        ET.SubElement(linha, f"{ns}AnoAquisicao").text = str(line.acquisition_date.year)
        ET.SubElement(linha, f"{ns}MesAquisicao").text = str(
            line.acquisition_date.month
        )
        ET.SubElement(linha, f"{ns}DiaAquisicao").text = str(line.acquisition_date.day)
        ET.SubElement(linha, f"{ns}ValorAquisicao").text = str(
            round(line.acquisition_value, 2)
        )
        ET.SubElement(linha, f"{ns}DespesasEncargos").text = str(
            round(line.expenses, 2)
        )
        ET.SubElement(linha, f"{ns}CodPaisContraparte").text = str(
            line.coutry_of_origin
        )

    def declare(self, sales, xml_root):
        _logger.info(xml_root)
        for index, sale in enumerate(sales):
            line = SaleRecord(**sale)
            line.linha += index
            self.generate_content(xml_root, XML_NS, line)


@attrs.define
class Quadro9:
    """9 Rendimentos de Incrementos Patrimoniais (Categoria G)."""

    cap_gains: CapitalGains = attr.field(factory=CapitalGains)

    def declare(self, sales, xml_root):
        self.cap_gains.declare(
            sales, xml_root=xml_root.find(f".//{XML_NS}AnexoJq092AT01")
        )


@attrs.define
class AnexoJ:
    """Anexo J. Rendimentos Obitidos no Estrangeiro"""

    quadro9: Quadro9 = attr.field(factory=Quadro9)

    def declare(self, sales, xml_root):
        self.quadro9.declare(sales, xml_root)


@attrs.define
class IRS:
    annex_j: AnexoJ = attr.field(factory=AnexoJ)
    root: ET.Element = attr.field(default=None)

    def declare(self, sales, fiscal_year):
        self.annex_j.declare(sales, xml_root=self.root.find(f".//{XML_NS}AnexoJ"))

    def load(self, file: pathlib.Path):
        tree = ET.parse(str(file))
        self.root = tree.getroot()

    def export(self, output):
        ET.register_namespace("", "http://www.dgci.gov.pt/2009/Modelo3IRSv2024")
        tree = ET.ElementTree(self.root)
        ET.indent(tree, "")

        tree.write(
            output,
            encoding="utf-8",
            xml_declaration=True,
            short_empty_elements=True,
        )
