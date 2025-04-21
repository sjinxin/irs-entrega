# IRS Entrega

A Python tool for processing and generating IRS (Portuguese Tax) declarations in XML format.

## Description

This tool helps automate the process of generating IRS declarations by:

- Processing transaction data from various brokers (currently supports Degiro)
- Converting the data into the official IRS XML format
- Handling different IRS declaration versions (2024/2025)
- Managing capital gains and other tax-related calculations

## Installation

The project uses Poetry for dependency management. To install:

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone https://github.com/yourusername/irs-entrega.git
cd irs-entrega

# Install dependencies
poetry install
```

## Usage

```bash
# Activate the virtual environment
poetry shell

# Run the tool
irs -i input/declaration.xml -d data/ -o output/result.xml -t YOUR_TAX_ID
```

### Command Line Arguments

- `-i, --input`: Path to the pre-filled IRS declaration XML file
- `-d, --data`: Directory containing transaction data from brokers
- `-o, --output`: Output file path (default: output/output.xml)
- `-y, --year`: Fiscal year for the declaration (default: previous year)
- `-t, --tax-id`: Tax identification number (NIF)

## Project Structure

```
irs-entrega/
├── src/
│   └── irs/
│       ├── broker/         # Broker-specific data processing
│       │   └── degiro.py   # Degiro broker implementation
│       ├── model/          # IRS data models
│       │   └── model.py    # Core IRS model implementation
│       └── cli.py          # Command line interface
├── data/                   # Transaction data from brokers
├── input/                  # Input XML templates
├── output/                 # Generated XML files
└── tests/                  # Test files
```

## Development

### Setup

1. Install development dependencies:

```bash
poetry install --with dev
```

2. Install pre-commit hooks:

```bash
pre-commit install
```

### Testing

Run tests using pytest:

```bash
poetry run pytest
```

### Code Style

The project uses:

- Black for code formatting
- isort for import sorting
- flake8 for linting

## License

This project is licensed under the terms of the LICENSE file.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -S -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
