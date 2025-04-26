import logging
import pathlib
import re
import typing as t
import xml.etree.ElementTree as ET
from datetime import datetime

import attr
import attrs
from tabulate import tabulate

logging.basicConfig(level=logging.DEBUG)

_logger = logging.getLogger(__name__)


YEAR_NS_MAP = {
    "2024": "http://www.dgci.gov.pt/2009/Modelo3IRSv2024",
    "2025": "http://www.dgci.gov.pt/2009/Modelo3IRSv2025",
}

XML_NS = "{http://www.dgci.gov.pt/2009/Modelo3IRSv2025}"


COUTRY_CODE_MAP = dict(US=840, IE=372, DE=276, GB=826)


@attrs.define
class Country:
    name: str
    code: int

    def __str__(self) -> str:
        return str(self.code)


@attrs.define
class Code:
    name: str
    clause: str

    def __str__(self) -> str:
        return self.name


@attrs.define
class SaleRecord:
    """Alienação Onerosa de Partes Sociais e Outros Valores Mobiliários [art.º 10.º, n.º 1, al. b), do CIRS]"""

    linha: int = 951
    _coutry_of_origin: t.Optional[Country] = None
    _code: t.Optional[Code] = None
    realization_date: t.Optional[datetime] = None
    realization_value: t.Optional[float] = None
    acquisition_date: t.Optional[datetime] = None
    acquisition_value: t.Optional[float] = None
    expenses: t.Optional[float] = None
    coutry_of_counterparty: t.Optional[Country] = Country("Paises Baixos", 528)
    note: str = ""

    @property
    def profit(self):
        return self.realization_value - self.acquisition_date

    @property
    def coutry_of_origin(self):
        if not self._coutry_of_origin:
            # Pattern to match all fields from note
            # Example note format: "name[isin] unit_to_declare/abs(sell_order.unit)"
            pattern = r"^(?P<name>[^[]+)\[(?P<isin>[^\]]+)\]\s+(?P<unit_to_declare>\d+)/(?P<total_units>\d+)$"
            match = re.match(pattern, self.note)
            if match:
                isin = match.group("isin").strip()
                country = isin[0:2]
                self._coutry_of_origin = Country(country, COUTRY_CODE_MAP[country])
        return self._coutry_of_origin

    @property
    def code(self):
        if not self._code:
            self._code = Code(
                name="G20",
                clause="Resgates ou alienações de unidades de participação ou liquidação de fundos de investimento;",
            )
        return self._code


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
            line.coutry_of_counterparty
        )

    def declare(self, sales, fiscal_year, xml_root):
        total_realization = 0.0
        total_acquisition = 0.0
        total_expenses = 0.0

        q092AT01 = xml_root.find(f".//{XML_NS}AnexoJq092AT01")
        for index, sale in enumerate(sales):
            line = SaleRecord(**sale)
            line.linha += index
            if line.realization_date.year == fiscal_year:
                self.generate_content(q092AT01, XML_NS, line)
                total_realization += round(line.realization_value, 2)
                total_acquisition += round(line.acquisition_value, 2)
                total_expenses += round(line.expenses, 2)

        # Add the sum elements as siblings to AnexoJq092AT01

        Quadro09 = xml_root.find(f".//{XML_NS}Quadro09")
        # Create sum elements
        sum_c01 = ET.SubElement(Quadro09, f"{XML_NS}AnexoJq092AT01SomaC01")
        sum_c01.text = f"{total_realization:.2f}"

        sum_c02 = ET.SubElement(Quadro09, f"{XML_NS}AnexoJq092AT01SomaC02")
        sum_c02.text = f"{total_acquisition:.2f}"

        sum_c03 = ET.SubElement(Quadro09, f"{XML_NS}AnexoJq092AT01SomaC03")
        sum_c03.text = f"{total_expenses:.2f}"

        sum_c04 = ET.SubElement(Quadro09, f"{XML_NS}AnexoJq092AT01SomaC04")
        sum_c04.text = f"{0:.2f}"


@attrs.define
class Quadro9:
    """9 Rendimentos de Incrementos Patrimoniais (Categoria G)."""

    cap_gains: CapitalGains = attr.field(factory=CapitalGains)

    def declare(self, sales, fiscal_year, xml_root):
        self.cap_gains.declare(sales, fiscal_year, xml_root=xml_root)


@attrs.define
class AnexoJ:
    """Anexo J. Rendimentos Obitidos no Estrangeiro"""

    quadro9: Quadro9 = attr.field(factory=Quadro9)

    def declare(self, sales, fiscal_year, xml_root):
        self.quadro9.declare(sales, fiscal_year, xml_root)


@attrs.define
class IRS:
    annex_j: AnexoJ = attr.field(factory=AnexoJ)
    root: ET.Element = attr.field(default=None)

    def declare(self, sales, fiscal_year):
        self.annex_j.declare(
            sales, fiscal_year, xml_root=self.root.find(f".//{XML_NS}AnexoJ")
        )

    def load(self, file: pathlib.Path):
        tree = ET.parse(str(file))
        self.root = tree.getroot()

    def export(self, output):
        # Register the default namespace without a prefix
        ET.register_namespace("", XML_NS.strip("{}"))
        tree = ET.ElementTree(self.root)
        ET.indent(tree, "")

        # Convert to string and use lxml for better formatting
        xml_string = ET.tostring(self.root, encoding="utf-8", xml_declaration=True)
        from lxml import etree

        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(xml_string, parser)
        etree.indent(root, space="")

        # Write with lxml which handles empty elements better
        with open(output, "wb") as f:
            f.write(
                etree.tostring(
                    root, encoding="utf-8", xml_declaration=True, pretty_print=True
                )
            )
