import csv
from collections import namedtuple
from datetime import datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom
import os
import attr


@attr.define
class Line:
    numero: int
    nlilha: int
    codpais: int
    anorealizacao: int
    mesrealizacao: int
    diarealizacao: int
    valorrealizacao: float
    anoaquisicao: int
    mesaquisicao: int
    diaaquisicao: int
    valoraquisicao: float
    despesasencargos: float
    codpaiscontraparte: int
    codigo: str = "G01"


def generate_content(parent, line: Line):
    ns = "{http://www.dgci.gov.pt/2009/Modelo3IRSv2024}"
    linha = ET.SubElement(parent, f"{ns}AnexoJq092AT01-Linha")
    linha.set("numero", str(line.numero))
    ET.SubElement(linha, f"{ns}NLinha").text = str(line.nlilha)
    ET.SubElement(linha, f"{ns}CodPais").text = str(line.codpais)
    ET.SubElement(linha, f"{ns}Codigo").text = line.codigo
    ET.SubElement(linha, f"{ns}AnoRealizacao").text = str(line.anorealizacao)
    ET.SubElement(linha, f"{ns}MesRealizacao").text = str(line.mesrealizacao)
    ET.SubElement(linha, f"{ns}DiaRealizacao").text = str(line.diarealizacao)
    ET.SubElement(linha, f"{ns}ValorRealizacao").text = str(line.valorrealizacao)
    ET.SubElement(linha, f"{ns}AnoAquisicao").text = str(line.anoaquisicao)
    ET.SubElement(linha, f"{ns}MesAquisicao").text = str(line.mesaquisicao)
    ET.SubElement(linha, f"{ns}DiaAquisicao").text = str(line.diaaquisicao)
    ET.SubElement(linha, f"{ns}ValorAquisicao").text = str(line.valoraquisicao)
    ET.SubElement(linha, f"{ns}DespesasEncargos").text = str(line.despesasencargos)
    ET.SubElement(linha, f"{ns}CodPaisContraparte").text = str(line.codpaiscontraparte)


Stock = {
    "D. Lufthansa": 276,
    "Air France-KLM": 250,
    "585 | Aug | Netherlands 25": 528,
}


with open("data/284318760/book.csv", "r") as f:
    reader = csv.reader(f)
    headers = []  # get the first 3 line
    headers.extend(next(reader))
    headers.extend(next(reader))
    headers.extend(next(reader))

    headers = [h for h in headers if h]
    headers = [h.replace("/", "_") for h in headers]  # replace '/' with '_'
    print(headers)

    headers = [h.replace(" ", "_") for h in headers]  # replace '/' with '_'
    print(headers)

    headers[0] = headers[0].lstrip("\ufeff")  # remove BOM from first field name
    print(headers)
    Row = namedtuple("Row", headers)  # create namedtuple class

    merged_rows = []
    temp = []
    for i, row in enumerate(reader, start=4):
        row = [item for item in row if item]  # remove empty strings
        temp.extend(row)
        if i % 3 == 0:
            merged_rows.append(Row(*temp))
            temp = []
    if temp:
        merged_rows.append(Row(*temp))

    linha = 951
    total = 0
    encargas_total = 0
    codigo = "G01"
    lines = []
    for row in merged_rows:
        if not row.Amount.endswith("Shares"):
            continue
        pais_do_fonte = "eu"
        if row.Open_Value.startswith("$"):
            pais_do_fonte = "840"  # Estados Unidos da America
        if row.Open_Value.startswith("¥"):
            pais_do_fonte = "392"  # Japao
        if row.Open_Value == row.Close_Value:
            continue
        if row.Exchange_Rate == "EUR/EUR --":
            pais_do_fonte = Stock[row.Instrument]
            exchange = 1
        else:
            # print(row)
            # print(row.Exchange_Rate)
            exchange = float(row.Exchange_Rate.split(" ")[1])

        open_date = datetime.strptime(row.Open_Time, "%m/%d/%Y %H:%M").date()
        close_date = datetime.strptime(row.Close_Time, "%m/%d/%Y %H:%M").date()

        open_value = float(row.Open_Value[1:].replace(",", "").strip()) / exchange
        close_value = float(row.Close_Value[1:].replace(",", "").strip()) / exchange
        if row.Buy_Sell == "Buy":
            profit = close_value - open_value

        else:
            close_value = -close_value
            open_value = -open_value
            profit = close_value - open_value
        adjustment = float(
            row.Adjustments.replace("-", "")[1:].replace(",", "").strip()
        )
        overnight = float(
            row.Overnight_Funding.replace("-", "")[1:].replace(",", "").strip()
        )
        curre_conversion = float(
            row.Currency_Conversion.replace("-", "")[1:].replace(",", "").strip()
        )
        encargas = adjustment + overnight + curre_conversion
        encargas_total += encargas
        print(f"{row.Instrument}{row.Open_Value}{row.Close_Value}")
        print(
            "|".join(
                [
                    str(linha),
                    str(pais_do_fonte),
                    str(codigo),
                    str(close_date),
                    str(close_value),
                    str(open_date),
                    str(open_value),
                    str(encargas),
                    "196",  # Chipre
                ]
            )
        )
        lines.append(
            Line(
                numero=linha - 950,
                nlilha=linha,
                codpais=pais_do_fonte,
                anorealizacao=close_date.year,
                mesrealizacao=close_date.month,
                diarealizacao=close_date.day,
                valorrealizacao=close_value,
                anoaquisicao=open_date.year,
                mesaquisicao=open_date.month,
                diaaquisicao=open_date.day,
                valoraquisicao=open_value,
                despesasencargos=encargas,
                codpaiscontraparte=196,
            )
        )
        total += profit
        linha += 1
    print(f"total: {total} cost: {encargas_total} net: {total - encargas_total}")
    tree = ET.parse("input/decl-m3-irs-2020-284318760.xml")
    ns = "{http://www.dgci.gov.pt/2009/Modelo3IRSv2024}"

    root = tree.getroot()

    for anexo in root.findall(f".//{ns}AnexoJq092AT01"):
        for line in lines:
            generate_content(anexo, line)
    xml_string = ET.tostring(root, encoding="utf-8")
    dom = xml.dom.minidom.parseString(xml_string)
    pretty_xml_as_string = dom.toprettyxml(indent="")

    lines = pretty_xml_as_string.split(os.linesep)
    lines = [
        f"{line.replace('ns0:', '').replace(':ns0','')}{os.linesep}"
        for line in lines
        if line.strip()
    ]
    with open("output/formatted_output.xml", "w", encoding="utf-8") as f:
        f.writelines(lines)
