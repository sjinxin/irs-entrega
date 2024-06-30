import logging
import typing as t
import xml.etree.ElementTree as ET
import pathlib
from degiro import Portfolio
from irs import IRS
import argparse

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


def parse_arguments():
    parser = argparse.ArgumentParser(description="A simple argument parser example")

    # Add arguments
    parser.add_argument(
        "-i",
        "--input",
        type=pathlib.Path,
        required=True,
        help="Path to the pre-filled irs declaration xml file",
    )
    parser.add_argument(
        "-d",
        "--data",
        type=pathlib.Path,
        required=True,
        help="Transaction data from brokers",
    )
    parser.add_argument(
        "-o", "--output", type=pathlib.Path, default="output/output.xml"
    )
    # Parse the arguments
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    portfolio = Portfolio.from_transaction_csv_files(input_dir=args.data)
    sales, _ = portfolio.declare()
    irs = IRS()
    irs.load(args.input)
    irs.declare(sales, fiscal_year=2023)
    irs.export(args.output)


if __name__ == "__main__":
    main()
