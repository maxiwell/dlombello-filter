import numpy as np
import pyparsing as pp
import sys
import csv
import json, ast
from datetime import datetime, timedelta

def ts_to_date(timestamp: int, formato = "%Y-%m-%d") -> str:
    return timestamp.strftime(formato)

def date_to_ts(date) -> int:
    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%m/%Y", "%Y"]
    for formato in formatos:
        try:
            ts = datetime.strptime(date, formato)
            return ts
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {date}")

def build_parse():
    field = pp.oneOf("date corretora preco qtd_atual qtd_ant fluxo_caixa evento")

    operator = pp.oneOf("= >= <= < > == != <> ~ in")
    not_op = pp.oneOf("NOT not !")
    and_op = pp.oneOf("AND and")
    or_op  = pp.oneOf("OR or")

    value_str = pp.QuotedString("'")
    value_num = pp.Word(pp.nums + ".").setParseAction(lambda t: float(t[0]))
    value_list = pp.Suppress("[") + pp.Group(pp.delimitedList(pp.QuotedString("'"))) + pp.Suppress("]") 

    value = value_str | value_num | value_list

    exp = pp.Group(field + operator + value)

    cond = pp.infixNotation(exp, [
        (not_op, 1, pp.opAssoc.RIGHT),
        (and_op, 2, pp.opAssoc.LEFT),
        (or_op, 2, pp.opAssoc.LEFT),
        (operator, 2, pp.opAssoc.LEFT)
    ], lpar=pp.Suppress("("), rpar=pp.Suppress(")"))

    return cond

def parse_string(query):
    parser = build_parse()
    try:
        parsed_query = parser.parseString(query, parseAll=True)[0]
        return parsed_query
    except pp.ParseException as e:
        print(f"Erro ao interpretar query: {e}")
        sys.exit(1)

def get_context(transacao):
    # we can use this function to manipulate some data inside the parser
    return transacao

def avaliar_expressao(transacao, parsed_query):
    contexto = get_context(transacao)

    def avaliar(parsed):

        # stop condition
        if (np.isscalar(parsed)):
            return parsed

        while (len(parsed) > 3):
            parsed = parsed[0:2] + [avaliar(parsed[2:])]

        if (len(parsed) == 3):
            op_left, operator, op_right = parsed
        elif (len(parsed) == 2):
            operator, op_right = parsed

        # special operators
        if operator.upper() == "NOT" or operator == "!":
            return not avaliar(op_right)
        elif operator.upper() == "AND":
            return avaliar(op_left) and avaliar(op_right)
        elif operator.upper() == "OR":
            return avaliar(op_left) or avaliar(op_right)

        # right_value has the right side value from homebank file
        right_value = contexto.get(op_left, "")

        # semantic exceptions
        if (op_left == "date"):
            right_value = date_to_ts(right_value)
            op_right    = date_to_ts(op_right)
        elif (isinstance(op_right, float)):
            right_value = float(right_value)
        elif operator == 'in':
            # convert the string "['word1', 'word2']"" to a real array
            op_right = ast.literal_eval(str(op_right).upper())
            right_value = right_value.upper()
        else:
            right_value = right_value.upper()
            op_right = op_right.upper()

        if operator == "~":
            return op_right in right_value
        elif operator == "=" or operator == "==":
            return right_value == op_right
        elif operator == "!=" or operator == "<>":
            return right_value != op_right
        elif operator == ">=":
            return right_value >= op_right
        elif operator == "<=":
            return right_value <= op_right
        elif operator == ">":
            return right_value > op_right
        elif operator == "<":
            return right_value < op_right
        elif operator == "in":
            if right_value in op_right:
                return True

        return False

    return avaliar(parsed_query)