#!/bin/bash

# Exit on error
set -e

echo "Running linters..."

# Run black
echo "\nRunning black..."
black --check src tests

# Run isort
echo "\nRunning isort..."
isort --check-only src tests

# Run flake8
echo "\nRunning flake8..."
flake8 src tests

# Run mypy
echo "\nRunning mypy..."
mypy src

# Run pylint
echo "\nRunning pylint..."
pylint src tests

echo "\nAll linters completed successfully!" 