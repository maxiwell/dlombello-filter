import json
import sys
import calendar

from datetime import datetime, timedelta

def get_query_filter(filter_name):
    json_file = "filters.json"
    filters = {}

    try:
        with open(json_file, "r") as f:
            filters = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading filters from {json_file}: {e}")

    if filter_name is None:
        return filters

    query = filters.get(filter_name, None)
    if query is None:
        print(f"Filter '{filter_name}' not found!")
        sys.exit(1)

    return query

def dt_format(dt):
    return dt.strftime("%d/%m/%Y")

def magic_words(query):
    if query is None:
        return None

    today = datetime.today()

    first_day_this_month = today.replace(day=1)
    last_day_this_month  = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)
    last_day_last_month  = first_day_this_month - timedelta(days=1)

    first_day_this_year = today.replace(month=1, day=1)
    last_day_this_year  = today.replace(month=12, day=31)

    first_day_last_year = today.replace(year=today.year-1, month=1, day=1)
    last_day_last_year = today.replace(year=today.year-1, month=12, day=31)

    replace_magic_words = {
        'today'     : f"date = '{dt_format(today)}'",
        'yesterday' : f"date = '{dt_format(today - timedelta(days=1))}'",
        'tomorrow'  : f"date = '{dt_format(today + timedelta(days=1))}'",
        'this_month': f"date >= '{dt_format(first_day_this_month)}' and date <= '{dt_format(last_day_this_month)}'",
        'last_month': f"date >= '{dt_format(first_day_last_month)}' and date <= '{dt_format(last_day_last_month)}'",
        'last_30_days': f"date >= '{dt_format(today - timedelta(days=30))}' and date <= '{dt_format(today)}'",
        'this_year' : f"date >= '{dt_format(first_day_this_year)}' and date <= '{dt_format(last_day_this_year)}'",
        'last_year' : f"date >= '{dt_format(first_day_last_year)}' and date <= '{dt_format(last_day_last_year)}'",
    }

    for key, value in replace_magic_words.items():
        query = query.replace('{' + key + '}', value)

    return query