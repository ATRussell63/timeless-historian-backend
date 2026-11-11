import math

def intersection_has_any(list1, list2) -> bool:
    return len(list(set(list1) & set(list2))) > 0

def truncate_float(number, decimal_places):
    factor = 10**decimal_places
    return math.floor(number * factor) / factor