import json
import os
import sys
import requests
import click
from datetime import datetime
from parser import get_context, parse_string, avaliar_expressao, date_to_ts
from filters import magic_words


def set_up(config, sandbox = True):

    # Set sandbox in config.json to avoid unnecessary API accesses
    sandbox_file = config.get("sandbox", None)

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

    if group is not None:
        group_key = context[group]
        total_by_key[group_key] = total_by_key.get(group_key, 0) + float(context[key])

    # calculate __total__ even if group is defined
    total_by_key["__total__"] = total_by_key.get("__total__", 0) + float(context[key])

    return total_by_key

def run_query(data, query, totalizers_config):

    if query is not None:
        parsed_query = parse_string(query)
    else:
        parsed_query = None

    all_transactions = []
    totalizers = {}
    for transacao in data:
        if avaliar_expressao(transacao, parsed_query):
            context = get_context(transacao)
            all_transactions.append(context)

            totalizers['transactions'] = totalizers.get("transactions", 0) + 1

            for totalizer_item in totalizers_config:
                column = totalizer_item.get('column', None)
                group  = totalizer_item.get('group_by', None)
                totalizers[column] = calculate_totalizer(column, group, context, totalizers)

    all_transactions = sorted(all_transactions, key=lambda x: date_to_ts(x['date']))
    return all_transactions, totalizers

def command(config, sandbox, list, filter, query, append, columns, replace, fetch, csv):

    query = magic_words(query)

    if not columns:
        # default columns to improve the legebility
        columns = config.get("columns", None)

    data = set_up(config, sandbox).get('result')

    print('query:', query)
    totalizers_config = config.get("totalizers", {})
    trans, totalizers = run_query(data, query, totalizers_config)

    trans = select_columns(trans, columns)
    trans = sorted(trans, key=lambda x: date_to_ts(x['date']))

    if csv is not None:
        convert_to_csv(trans, csv)
    else:
        for i in trans:
            print(i)

    print("Totalizers:")
    for totalizer_item in totalizers_config:
       column = totalizer_item.get('column', None)
       rounded = {x: round(v, 2) for x,v in totalizers[column].items()}
       totalizers[column] = dict(sorted(rounded.items(), key=lambda x: x[0]))

    print(json.dumps(totalizers, indent = 4))