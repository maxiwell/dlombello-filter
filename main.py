#!/bin/env python3
# -*- coding: utf-8 -*-

import click
import json
import sys
import re

from filters import get_query_filter
from command import command

@click.group()
def cli():
    pass

def load_config_file(config_file):
    config = {}
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config from {config_file}: {e}")

    return config

def validate_options(list, filter, query, append, columns, replace, fetch):
    if filter is not None:
        query = get_query_filter(filter)

    if query is not None:
        query = query

    if list is not None:
        for key, value in get_query_filter(None).items():
            print(f"{key}:\n    {value}\n")
        sys.exit(0)

    if columns:
        if not query and not filter:
            raise click.UsageError("Mandatory '-f' or '-q' with '-c'")
            sys.exit(1)

    if append:
        if not filter:
            raise click.UsageError("Mandatory '-f' with '-a'")
            sys.exit(1)
        query = '(' + query + ') ' + append

    if replace:
        if not filter:
            raise click.UsageError("Mandatory '-f' with '-r'")
            sys.exit(1)
        query = re.sub(r'{.*}', replace, query)

    if fetch:
        sandbox = False
    else:
        sandbox = True

    return query, sandbox

def call_command(cmd, list, filter, query, append, columns, replace, fetch, csv):
    config = load_config_file('config.json')
    config_cmd = config.get(cmd, {})
    query, sandbox = validate_options(list, filter, query, append, columns, replace, fetch)
    command(config_cmd, sandbox, list, filter, query, append, columns, replace, fetch, csv)

def common_options(func):
    options = [
        click.option('-l', "--list", default=None, is_flag=True, help="List all saved filters"),
        click.option('-f', "--filter", help="Saved filter to apply"),
        click.option('-q', "--query", help="JQL like query to filter transactions"),
        click.option('-a', "--append", help="Append more conditions in the filter called by '-f'"),
        click.option('-c', "--columns", help="Columns to show in the output"),
        click.option('-r', "--replace", help="Replace the first magic work"),
        click.option('--fetch', default=None, is_flag=True, help="Fetch data from API to populate the sandbox files"),
        click.option('--csv', help="Save the output in a csv file")
    ]
    for option in reversed(options):
        func = option(func)
    return func

@click.command()
@common_options
def operacoes(list, filter, query, append, columns, replace, fetch, csv):
    call_command("operacoes", list, filter, query, append, columns, replace, fetch, csv)

@click.command()
@common_options
def proventos(list, filter, query, append, columns, replace, fetch, csv):
    call_command("proventos", list, filter, query, append, columns, replace, fetch, csv)

@click.command()
@common_options
def carteira(list, filter, query, append, columns, replace, fetch, csv):
    call_command("carteira", list, filter, query, append, columns, replace, fetch, csv)

cli.add_command(operacoes)
cli.add_command(proventos)
cli.add_command(carteira)

if __name__ == '__main__':
    if (len(sys.argv) < 2):
        print("usage: main.py --help")
        sys.exit(1)

    cli()
