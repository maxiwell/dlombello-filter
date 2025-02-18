#!/bin/env python3
# -*- coding: utf-8 -*-

import click
import requests
import json
import sys, os
from datetime import datetime

from parser import get_context, build_parse, parse_string, avaliar_expressao, ts_to_date, date_to_ts
from filters import magic_words, get_query_filter

def load_config_file(config_file):
    config = {}
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config from {config_file}: {e}")

    return config

def set_up(route, config, sandbox = True):

    # Set sandbox in config.json to avoid unnecessary API accesses
    sandbox_file = config.get("sandbox", {}).get(route, None)

    if sandbox == True:
        if os.path.exists(sandbox_file):
            with open(sandbox_file, "r") as file:
                body = json.load(file)
            return body
        else:
            print("sandbox file not found; run with --fetch to get data from API")
            sys.exit(1)

    url = config.get("endpoint", {}).get(route, None)
    if url is None:
        print("endpoint not found")
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "Authorization": config.get("authorization", None)
    }

    # fetch data from API
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if sandbox_file is not None:
            with open(sandbox_file, "w+") as file:
                json.dump(data, file, indent=4)
        return data
    else:
        response.raise_for_status()

def select_columns(all_transactions, columns):
    ret_trans = []
    columns_to_show = columns.split(",") if columns else None
    if columns_to_show:
        for i in all_transactions:
            i_selected_columns = {}
            for col in columns_to_show:
                try:
                    col = col.strip()
                    i_selected_columns[col] = i[col]
                except KeyError:
                    print(f"Columns'{col}' not found!")
                    sys.exit(1)

            ret_trans.append(i_selected_columns)
    else:
        ret_trans = all_transactions

    return ret_trans

def calculate_totalizer(key, group, context, totalizer):
    total_by_key = totalizer.get(key, {}) 
    key_value = context[group]
    total_by_key[key_value] = total_by_key.get(key_value, 0) + float(context[key])
    return total_by_key

def run_query(data, query):
    parsed_query = parse_string(query)

    all_transactions = []
    totalizers = {}
    for transacao in data:
        if avaliar_expressao(transacao, parsed_query):
            context = get_context(transacao)
            all_transactions.append(context)

            totalizers['transactions'] = totalizers.get("transactions", 0) + 1

            totalizers['qtd_total'] = totalizers.get('qtd_total', 0) + float(transacao['qtd'])
            totalizers['qtd'] = calculate_totalizer("qtd", "ativo", context, totalizers)

            totalizers['fluxo_caixa_total'] = totalizers.get('fluxo_caixa_total', 0) + float(transacao['fluxo_caixa'])
            totalizers['fluxo_caixa'] = calculate_totalizer("fluxo_caixa", "corretora", context, totalizers)

    all_transactions = sorted(all_transactions, key=lambda x: date_to_ts(x['date']))
    return all_transactions, totalizers

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


@click.command()
@click.option('-l', "--list", default=None, is_flag=True, help="List all saved filters")
@click.option('-f', "--filter", help="Saved filter to apply")
@click.option('-q', "--query", help="JQL like query to filter transactions")
@click.option('-a', "--append", help="Append more conditions in the filter called by '-f'")
@click.option('-c', "--columns", help="Columns to show in the output")
@click.option('-r', "--replace", help="Replace the first magic work")
@click.option('--fetch', default=None, is_flag=True, help="Fetch data from API to populate the sandbox files")
@click.option('--csv', help="Save the output in a csv file")
def operacoes(list, filter, query, append, columns, replace, fetch, csv):

    query, sandbox = validate_options(list, filter, query, append, columns, replace, fetch)
    query = magic_words(query)

    if not columns:
        # default columns to improve the legebility
        columns = "date, corretora, ativo, evento, preco, qtd_atual, qtd_ant, fluxo_caixa"

    config = load_config_file('config.json')
    data = set_up("/operacoes", config, sandbox).get('result')

    print('query:', query)

    # execute the query using the dlombello data
    trans, totalizers = run_query(data, query)

    trans = select_columns(trans, columns)
    trans = sorted(trans, key=lambda x: date_to_ts(x['date']))

    if csv is not None:
        convert_to_csv(trans, csv)
    else:
        for i in trans:
            print(i)

    print("Totalizers:")
    try:
        totalizers["fluxo_caixa_total"] = round(totalizers["fluxo_caixa_total"], 2)
        rounded_fluxo_caixa = {x: round(v, 2) for x,v in totalizers["fluxo_caixa"].items()}
        totalizers["fluxo_caixa"] = dict(sorted(rounded_fluxo_caixa.items(), key=lambda x: x[0]))
    except KeyError:
        totalizers = {}

    print(json.dumps(totalizers, indent = 4))

if __name__ == '__main__':
    if (len(sys.argv) < 2):
        print("usage: main.py --help")
        sys.exit(1)

    operacoes()
