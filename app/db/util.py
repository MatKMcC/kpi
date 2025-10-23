import datetime as dt

def to_date(date_string):
    return dt.datetime.strptime(date_string, "%Y-%m-%d")

def from_date(date_object):
    return dt.datetime.strftime(date_object, "%Y-%m-%d")