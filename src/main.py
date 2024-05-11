import logging
import typing as t
import xml.etree.ElementTree as ET

from degiro import Portfolio
from irs import IRS

logging.basicConfig(level=logging.DEBUG)

_logger = logging.getLogger(__name__)

def create_xml(data, output_file):
    root = ET.Element("root")
    for item in data:
        item_element = ET.SubElement(root, "item")
        for key, value in item.items():
            ET.SubElement(item_element, key).text = str(value)
    tree = ET.ElementTree(root)
    tree.write(output_file)


def main():
    xml_output_file = "output/output.xml"  # replace with your xml output file path
    portfolio = Portfolio.from_transaction_csv_files(input_dir="data/276280628")
    sales, _ = portfolio.declare()
    irs = IRS()
    irs.declare(sales, fiscal_year=2023)

if __name__ == "__main__":
    main()
