import logging
import typing as t
import xml.etree.ElementTree as ET
import pathlib
from datetime import datetime
from irs.broker.degiro import Portfolio
from irs.model.model import IRS

import argparse

# Configure logging for all modules
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
    parser.add_argument(
        "-y",
        "--year",
        type=int,
        default=datetime.now().year - 1,
        help="Fiscal year for the declaration (default: previous year)",
    )
    parser.add_argument(
        "-t",
        "--tax-id",
        type=str,
        required=True,
        help="Tax identification number (NIF)",
    )
    # Parse the arguments
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    data_dir = f'{args.data}/{args.tax_id}'
    portfolio = Portfolio.from_transaction_csv_files(input_dir=data_dir)
    portfolio.summary()
    sales, _ = portfolio.declare()
    irs = IRS()
    irs.load(args.input)
    irs.declare(sales, fiscal_year=args.year)
    irs.export(args.output)


if __name__ == "__main__":
    main()
