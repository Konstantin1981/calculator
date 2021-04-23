"""
Task 1: Standard Calculator
Input using the mouse or keyboard.

Optional: calculations based on the priorities of operations.
Optional: support for parentheses.
Optional: display of calculation history.
"""

import re
import numpy as np


# print current state of expr (for errors reports)
def print_expr(expr):
    while True:
        search = re.search(r"(A\d+A)", expr)
        if search:
            value = memory_dict[search.groups()[0]]
            i_low = search.span()[0]
            i_high = search.span()[1]
            expr = expr[0:i_low] + str(value) + expr[i_high:]
        else:
            return expr


# test expr for correct input
def test(expr):
    # some corrections
    expr = expr.lower()
    expr = expr.replace(" ", "")
    expr = expr.replace(":", "/")
    expr = expr.replace("\\", "/")
    expr = re.sub(r"[*]{2,}", "^", expr)
    expr = re.sub(r"[/]{2,}", "/", expr)
    expr = re.sub(r"[\^]{2,}", "^", expr)
    expr = re.sub(r"[.]{2,}", ".", expr)

    # is there numbers?
    search = re.search(r"[0-9]", expr)
    if search is None:
        print("There must be numbers...")
        return False

    # search paired symbols of operations
    search = re.findall(r"[-+*^/.]{2,}", expr)  # find all combination of operators

    def fun(x):
        return x not in ["/-", "*-", "^-", "+-", "-.", "+.", "/-.", "--", "--.", "+-.",
                         "*.", "/.", "^.", "^-.", "*-."]  # correct list of combinations

    if search:
        if any(map(fun, search)):
            expr = fix(expr, list(filter(fun, search)))  # if contains any that not in correct list
        if not expr:
            return False

    # is there chars?
    search = re.findall(r"[a-zA-zа-яА-ЯёЁ]+", expr)
    for match in search:
        if match not in ["log", "ln", "lg", "^",
                         "^log", "^lg", "^ln"]:  # except log, lg and ln, all chars combination is wrong
            print("Expression incorrect, see help(h)")
            return False

    # Search wrong symbols
    search = re.findall(r"[^0-9()+.*/^logn-]+", expr)
    if search:
        print("expression contains wrong symbols:", *search)
        return False

    search = re.search(r"\d\(|\)\d", expr)
    if search:
        expr = fix_bracers_multiply(expr)  # replace number(..) with number*(..)

    return expr


# replace number(..) with number*(..)
def fix_bracers_multiply(expr):
    while True:
        search = re.search(r"(\d)\(", expr)
        if search:
            value = search.groups()[0] + "*("
            i_low = search.span()[0]
            i_high = search.span()[1]
            expr = expr[0:i_low] + str(value) + expr[i_high:]  # construct new expr
        else:
            break
    while True:
        search = re.search(r"\)(\d)", expr)
        if search:
            value = ")*" + search.groups()[0]
            i_low = search.span()[0]
            i_high = search.span()[1]
            expr = expr[0:i_low] + str(value) + expr[i_high:]  # construct new expr
        else:
            break
    print("Expression was corrected to: ", expr)
    return expr


def fix(expr, notice):
    expr = re.sub(r"[+]{2,}", "+", expr)
    expr = re.sub(r"[-]{3,}", "--", expr)
    expr = re.sub(r"\^--", "^-", expr)
    expr = re.sub(r"/--", "/-", expr)
    expr = re.sub(r"\*--", "*-", expr)

    search = re.findall(r"[-+*/^]+[-.]*[+*/^]+", expr)  # search combinations as: "*+*"
    if search:
        print("expression contains wrong combination of symbols:", notice)
        return False

    print("There was a suspicious combination of symbols: ", notice)
    print("Expression to compute is:")
    print(expr)
    return expr


# call for searching of paired braces, if none - compute current expr
def execute_main(expr):
    while True:
        search = find_bracers(expr)
        if search:
            # compute expr in bracers
            # replace the expr in braces with computed value
            value = compute_in_bracers(search[1])
            if not value:
                return None
            i_low = search.span()[0]
            i_high = search.span()[1]
            expr = expr[0:i_low] + str(value) + expr[i_high:]  # new expr
        else:
            break
    if re.search(r"[()]", expr):
        print("expression contains unpaired bracers", print_expr(expr))
        return False

    return compute(expr)


# search for paired bracers at deepest level
def find_bracers(expr):
    pattern = re.compile(r"\(([-0-9.+* /^lognA]+?)\)")
    return pattern.search(expr)


# compute expr in bracers
def compute_in_bracers(expr):
    # is there numbers?
    search = re.search(r"[0-9]", expr)
    if search is None:
        print("There must be numbers...")
        return False

    # check the (123) case
    search = re.search(r"[-+*/^lA]", expr)
    if not search:
        token_index = next(token)  # get new token
        memory_dict[token_index] = get_value(expr)  # write new token to dict
        return token_index

    return compute(expr)


def compute(expr):
    # print("compute expression: ", expr)
    expr = compute_power(expr)
    if not expr:
        return False
    expr = compute_logs(expr)
    if not expr:
        return False
    expr = compute_multiply(expr)
    if not expr:
        return False
    expr = compute_sum(expr)
    return expr


def chek_start(expr):
    # search for [+-]value at the beginning of expr string to replace it with token
    search = re.search(r"^([-+])", expr)
    # print(expr)
    if search:
        if search.groups()[0] == "-":
            search_value = re.search(r'[-]?(-[\d.]+|-A[\d.]+A)', expr)
        else:
            search_value = re.search(r'([+]?[\d.]+|[+]?A[\d.]+A)', expr)
        value = get_value(search_value.groups()[0])
        expr = put_token(expr, value, search_value.span())  # change expr with token
    return expr


# search "value1 operand value2" structure,  return value1:str, value2:str, span of expr or False
def validate_expr(expr, operator):
    #  define the reg expr
    re_value1 = r"([\d.]+|A\d+A)"  # use r"([\d.]+" or token index r"A\d+A" to find values
    re_value2 = r"([-]?[\d.]+|[-]?A\d+A)"
    re_expr = re_value1 + operator + re_value2  # for "-" and "/"

    # search with re_expr = (value1 operand value2)
    if operator == "*":
        re_expr = re_value1 + r"[*]" + re_value2
    if operator == "^":
        re_expr = re_value1 + r"[\^]" + re_value2
    if operator == "+":
        re_expr = re_value1 + r"[\+]" + re_value2
    search = re.search(re_expr, expr)
    if search:
        return search.groups()[0], search.groups()[1], search.span()
    print("missing values in expression", print_expr(expr))
    return False


# get value, define if it numbers as string or token, return float(value) or int
def get_value(x):
    # print(x)
    if "A" in x:  # is value1 a token?
        if x[0] == "A":
            x = memory_dict[x]  # load from dict
        elif x[0] == "+":  # +AnA case
            x = memory_dict[x[1:]]
        elif x[0] == "-":  # -AnA case
            x = -memory_dict[x[1:]]
    else:
        if '.' in x:
            x = float(x)  # get float from string
        else:
            x = int(x)
    return x


# generate token, put it in dict with float(x) value, change expr with token in span-range
def put_token(string, x, span):
    token_index = next(token)  # get new token
    memory_dict[token_index] = x  # write new token to dict
    i_low = span[0]
    i_high = span[1]
    return string[0:i_low] + token_index + string[i_high:]  # change expr with token


#  try to fix some mistakes with float
def float_fix(x1, x2, y, operator):
    if operator in ["+", "-", "*"]:
        if "e" not in str(y) and "." in str(y):
            x1 = float(x1)
            x2 = float(x2)
            a, b = str(x1).split(".")
            c, d = str(x2).split(".")
            e, f = str(y).split(".")
            if operator in ["+", "-"]:
                if len(f) > max(len(b), len(d)):
                    y = round(y, max(len(b), len(d)))
            if operator == "*":
                if len(f) > len(b) * len(d):
                    y = round(y, len(b) + len(d))
    if str(y).endswith(".0"):
        y = int(y)
    return y


def compute_sum(expr):
    expr = chek_start(expr)  # replace [+-]Value at the string beginning with token
    while True:
        search = re.search(r"([-+])", expr)
        if search:
            operator = search.groups()[0]
            # print("compute expression: ", expr)
            val = validate_expr(expr, operator)  # search pattern to compute
            if val:
                value1, value2, search_span = val  # get values and span of math operation in expr string
                value1 = get_value(value1)
                value2 = get_value(value2)
                if operator == "+":  # compute expr
                    value = value1 + value2
                else:
                    value = value1 - value2
                value = float_fix(value1, value2, value, operator)
                expr = put_token(expr, value, search_span)  # change expr with token
            else:
                return False
        else:
            break

    if expr[0] != "A":
        token_index = next(token)  # get new token
        memory_dict[token_index] = get_value(expr)  # write new token to dict
        expr = token_index

    return expr


def compute_multiply(expr):
    search = re.search(r"([/*])", expr)
    if search:
        expr = chek_start(expr)  # replace [+-]Value at the string beginning with token
    else:
        return expr
    while True:
        search = re.search(r"([/*])", expr)
        if search:
            operator = search.groups()[0]
            # print("compute expression: ", expr)
            val = validate_expr(expr, operator)
            if val:
                value1, value2, search_span = val
                value1 = get_value(value1)
                value2 = get_value(value2)
                if operator == "*":
                    value = value1 * value2
                else:
                    try:
                        value = value1 / value2
                    except ZeroDivisionError:
                        print("Zero division error", print_expr(expr))
                        return False
                value = float_fix(value1, value2, value, operator)
                expr = put_token(expr, value, search_span)
            else:
                return False
        else:
            break
    return expr


def compute_power(expr):
    search = re.search(r"(\^)", expr)
    if search:
        expr = chek_start(expr)  # replace [+-]Value at the string beginning with token
    else:
        return expr
    while True:
        search = re.search(r"(\^)", expr)
        if search:
            # print("compute expression: ", expr)
            val = validate_expr(expr, search.groups()[0])
            if val:
                value1, value2, search_span = val
                value1 = get_value(value1)
                value2 = get_value(value2)
                try:
                    value = value1 ** value2
                except OverflowError:
                    print("values too huge, try another")
                    return False
                expr = put_token(expr, value, search_span)
            else:
                return False
        else:
            break
    return expr


def compute_logs(expr):
    while True:
        search = re.search(r"l([ogn]+)", expr)
        search_full = re.search(r"l([ogn]+)[-]?([-]?[\d.]+|A\d+A)", expr)
        if search and search_full:
            # print("compute expression: ", search_full)
            value = search_full.groups()[1]
            value = get_value(value)
            if value > 0:
                if search_full.groups()[0] == "og":
                    value = np.log10(value)
                if search_full.groups()[0] == "n":
                    value = np.log(value)
                if search_full.groups()[0] == "g":
                    value = np.log2(value)
            else:
                print("logarithm must be > 0: ", print_expr(expr))
                return False
            expr = put_token(expr, value, search_full.span())
        elif search and not search_full:
            return False
        else:
            break

    return expr


# generate tokens of A\d+A kind
def get_token(n=0):
    while True:
        n += 1
        yield "A" + str(n) + "A"


# help
def hlp():
    print("")
    print("Help")
    print("use '+ - * /' as math operations, ':' is also '/'")
    print(".2 is 0.2 ")
    print("5--5 = 5+5, 5*-5 = -25, 5/-5 = -1, 5^-1 = 0.2, 5-+5 is wrong syntax")
    print("use '^' or '**' for power")
    print("use 'log' for decimal, 'lg' for base 2 and 'ln' fo natural logarithm")
    print("don't use chars, except to write logarithms")
    print("use '()' to set the order, or define expression: (log(ln100) + 10^(lg4)) / ln10^2)")
    print("for continue with the last result input new operation, then new value or expression")
    print("Press 'q' for exit, 'h' for help")
    print("")


print("Calculator.")
hlp()
memory_dict = {}  # dict contains token indexes as keys and computed values as values of dict
res = None
math_operator = None

while True:
    new = input("> ")  # input new expression
    if new.lower() == "q":
        break
    if new in ["+", "-", "*", "^", "/"] and memory_dict.get(res):  # chek operator input and last res in dict
        math_operator = new  # keep in memory till next turn
        continue
    if new.lower() == "h":
        hlp()
        continue
    new = test(new)  # test the new expression
    if not new:
        continue
    if math_operator:
        new = res + math_operator + new  # reformat expr string with last result and operator
        token = get_token()  # token index generator
        last_result = memory_dict[res]
        memory_dict = {res: last_result}  # update dict
    else:
        token = get_token()  # reset dict
        memory_dict = {}
    res = execute_main(new)  # compute expr
    if res:
        res_value = memory_dict[res]
        try:
            print("Result:", "{:g}".format(res_value))
        except OverflowError:
            res_value = str(res_value)
            res_value = res_value[0] + "." + res_value[1:11] + "e" + str(len(res_value) - 1)
            print("Result: ", res_value)
    math_operator = None
