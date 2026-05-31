import sqlite3
from collections import OrderedDict
from datetime import datetime, timedelta

from .constants import RP, TS, A, D, H, M
from .processing.esofile_reader import Variable
from .results_dict import ResultsDictionary

DATA_TABLE = "ReportData"
DATA_DICT_TABLE = "ReportDataDictionary"
TIME_TABLE = "Time"


def to_eso_frequency(sql_frequency):
    """
    To eso frequency.
    
    Parameters
    ----------
    sql_frequency : Any
        Input parameter `sql_frequency`.
    
    Returns
    -------
    Any
        Return value from `to_eso_frequency`.
    """
    frequencies = {
        "Zone Timestep": TS,
        "Hourly": H,
        "Daily": D,
        "Monthly": M,
        "Run Period": RP,
        "Annual": A,
        "HVAC System Timestep": TS,
    }
    return frequencies[sql_frequency]


def to_sql_frequency(eso_frequency):
    """
    To sql frequency.
    
    Parameters
    ----------
    eso_frequency : Any
        Input parameter `eso_frequency`.
    
    Returns
    -------
    Any
        Return value from `to_sql_frequency`.
    """
    if eso_frequency is None:
        frequency = None
    else:
        frequencies = {
            TS: "Zone Timestep",
            H: "Hourly",
            D: "Daily",
            M: "Monthly",
            RP: "Run Period",
            A: "Annual",
        }
        frequency = frequencies[eso_frequency]
    return frequency


def eso_to_sql_variable(variable):
    """
    Eso to sql variable.
    
    Parameters
    ----------
    variable : Any
        Input parameter `variable`.
    
    Returns
    -------
    Any
        Return value from `eso_to_sql_variable`.
    """
    sql_columns = ["KeyValue", "Name", "Units"]
    sql_variable = {}
    for variable, column in zip(variable, sql_columns):
        if variable is not None:
            sql_variable[column] = variable
    return sql_variable


def data_dict_statement(columns, alike):
    """
    Data dict statement.
    
    Parameters
    ----------
    columns : Any
        Input parameter `columns`.
    
    alike : Any
        Input parameter `alike`.
    
    Returns
    -------
    Any
        Return value from `data_dict_statement`.
    """
    statement = (
        "SELECT ReportDataDictionaryIndex, ReportingFrequency, KeyValue, Name, Units"
        " FROM ReportDataDictionary WHERE ReportingFrequency =?"
    )
    eq_operater = " LIKE ?" if alike else "=?"
    conditions = [column + eq_operater for column in columns]
    if conditions:
        statement += "AND " + "AND ".join(conditions)
    return statement


def add_wild_cards(search_tuple):
    """
    Add wild cards.
    
    Parameters
    ----------
    search_tuple : Any
        Input parameter `search_tuple`.
    
    Returns
    -------
    Any
        Return value from `add_wild_cards`.
    """
    return tuple("%" + s + "%" for s in search_tuple)


def fetch_data_dict_rows(conn, variable, sql_frequency, alike):
    """
    Fetch data dict rows.
    
    Parameters
    ----------
    conn : Any
        Input parameter `conn`.
    
    variable : Any
        Input parameter `variable`.
    
    sql_frequency : Any
        Input parameter `sql_frequency`.
    
    alike : Any
        Input parameter `alike`.
    
    Returns
    -------
    Any
        Return value from `fetch_data_dict_rows`.
    """
    sql_variable = eso_to_sql_variable(variable)
    statement = data_dict_statement(sql_variable.keys(), alike)
    if sql_variable:
        if alike:
            place_holders = add_wild_cards(sql_variable.values())
        else:
            place_holders = tuple(sql_variable.values())
        res = conn.execute(statement, (sql_frequency,) + place_holders)
    else:
        res = conn.execute(statement, (sql_frequency,))
    return res


def to_string(unicode_variable):
    """
    To string.
    
    Parameters
    ----------
    unicode_variable : Any
        Input parameter `unicode_variable`.
    
    Returns
    -------
    Any
        Return value from `to_string`.
    """
    return Variable(*map(lambda x: str(x), unicode_variable))


def get_unsorted_sub_dict(rows):
    """
    Get unsorted sub dict.
    
    Parameters
    ----------
    rows : Any
        Input parameter `rows`.
    
    Returns
    -------
    Any
        Return value from `get_unsorted_sub_dict`.
    """
    unsorted_dict = {}
    for id_, frequency, key, type_, units in rows:
        unicode_variable = Variable(key, type_, units)
        variable = to_string(unicode_variable)
        unsorted_dict[id_] = variable
    return unsorted_dict


def sort_by_value(unsorted_dict):
    """
    Sort by value.
    
    Parameters
    ----------
    unsorted_dict : Any
        Input parameter `unsorted_dict`.
    
    Returns
    -------
    Any
        Return value from `sort_by_value`.
    """
    sorted_dct = OrderedDict()
    sorted_items = [item for item in sorted(unsorted_dict.items(), key=lambda x: x[1])]
    for key, value in sorted_items:
        sorted_dct[key] = value
    return sorted_dct


def get_ids_dict(conn, variables, sql_frequency, alike):
    """
    Get ids dict.
    
    Parameters
    ----------
    conn : Any
        Input parameter `conn`.
    
    variables : Any
        Input parameter `variables`.
    
    sql_frequency : Any
        Input parameter `sql_frequency`.
    
    alike : Any
        Input parameter `alike`.
    
    Returns
    -------
    Any
        Return value from `get_ids_dict`.
    """
    all_ids_dict = OrderedDict()
    for variable in variables:
        rows = fetch_data_dict_rows(conn, variable, sql_frequency, alike)
        ids_dict = get_unsorted_sub_dict(rows)
        all_ids_dict.update(sort_by_value(ids_dict))
    return all_ids_dict


def validate_time(timestamp, start_date, end_date):
    """
    Validate time.
    
    Parameters
    ----------
    timestamp : Any
        Input parameter `timestamp`.
    
    start_date : Any
        Input parameter `start_date`.
    
    end_date : Any
        Input parameter `end_date`.
    
    Returns
    -------
    Any
        Return value from `validate_time`.
    """
    if start_date and end_date:
        valid = start_date <= timestamp <= end_date
    elif start_date:
        valid = timestamp >= start_date
    elif end_date:
        valid = timestamp <= end_date
    else:
        valid = True
    return valid


def get_output_rows_with_time(conn, id_):
    """
    Get output rows with time.
    
    Parameters
    ----------
    conn : Any
        Input parameter `conn`.
    
    id_ : Any
        Input parameter `id_`.
    
    Returns
    -------
    Any
        Return value from `get_output_rows_with_time`.
    """
    statement = (
        "SELECT ReportData.Value, "
        "Time.IntervalType, Time.Year, Time.Month, Time.Day, Time.Hour, Time.Minute"
        " FROM ReportData"
        " JOIN Time ON ReportData.TimeIndex = Time.TimeIndex"
        " WHERE ReportData.ReportDataDictionaryIndex = ?"
    )
    return conn.execute(statement, (id_,))


def get_sliced_outputs(conn, id_, start_date, end_date):
    """
    Get sliced outputs.
    
    Parameters
    ----------
    conn : Any
        Input parameter `conn`.
    
    id_ : Any
        Input parameter `id_`.
    
    start_date : Any
        Input parameter `start_date`.
    
    end_date : Any
        Input parameter `end_date`.
    
    Returns
    -------
    Any
        Return value from `get_sliced_outputs`.
    """
    results = []
    for row in get_output_rows_with_time(conn, id_):
        timestamp = parse_sql_timestamp(row[1:])
        if validate_time(timestamp, start_date, end_date):
            results.append(row[0])
    return results


def get_outputs(conn, id_):
    """
    Get outputs.
    
    Parameters
    ----------
    conn : Any
        Input parameter `conn`.
    
    id_ : Any
        Input parameter `id_`.
    
    Returns
    -------
    Any
        Return value from `get_outputs`.
    """
    statement = (
        "SELECT ReportData.Value FROM ReportData"
        " WHERE ReportData.ReportDataDictionaryIndex = ?"
    )
    return [r[0] for r in conn.execute(statement, (id_,))]


def dates_statement(frequency):
    """
    Dates statement.
    
    Parameters
    ----------
    frequency : Any
        Input parameter `frequency`.
    
    Returns
    -------
    Any
        Return value from `dates_statement`.
    """
    switch = {TS: -1, H: 1, D: 2, M: 3, RP: 4, A: 5}
    statement = (
        "SELECT Time.IntervalType, Time.Year, Time.Month, Time.Day,"
        " Time.Hour, Time.Minute FROM Time"
        " WHERE Time.IntervalType = {}".format(switch[frequency.lower()])
    )
    return statement


def parse_sql_timestamp(time_row):
    """
    Parse sql timestamp.
    
    Parameters
    ----------
    time_row : Any
        Input parameter `time_row`.
    
    Returns
    -------
    Any
        Return value from `parse_sql_timestamp`.
    """
    interval, year, month, day, hour, minute = time_row
    year = 2002 if (year == 0 or year is None) else year

    # some fields may be none, 0 or 24 which is not compatible with datetime format
    if interval == 2:
        hour, minute = 0, 0
    elif interval == 3:
        day, hour, minute = 1, 0, 0
    elif interval in {4, 5}:
        month, day, hour, minute = 1, 1, 0, 0

    if hour == 24:
        # Convert last step of day
        shifted_datetime = datetime(year, month, day, hour - 1)
        corrected_datetime = shifted_datetime + timedelta(hours=1)
    else:
        corrected_datetime = datetime(year, month, day, hour, minute)
    return corrected_datetime


def parse_sql_timestamps(time_rows):
    """
    Parse sql timestamps.
    
    Parameters
    ----------
    time_rows : Any
        Input parameter `time_rows`.
    
    Returns
    -------
    Any
        Return value from `parse_sql_timestamps`.
    """
    timestamps = []
    for row in time_rows:
        timestamps.append(parse_sql_timestamp(row))
    return timestamps


def filter_timestamps(timestamps, start_date, end_date):
    """
    Filter timestamps.
    
    Parameters
    ----------
    timestamps : Any
        Input parameter `timestamps`.
    
    start_date : Any
        Input parameter `start_date`.
    
    end_date : Any
        Input parameter `end_date`.
    
    Returns
    -------
    Any
        Return value from `filter_timestamps`.
    """
    valid_timestamps = []
    for timestamp in timestamps:
        if validate_time(timestamp, start_date, end_date):
            valid_timestamps.append(timestamp)
    return valid_timestamps


def get_timestamps_from_sql(path, frequency, start_date=None, end_date=None):
    """
    Get timestamps from sql.
    
    Parameters
    ----------
    path : Any
        Input parameter `path`.
    
    frequency : Any
        Input parameter `frequency`.
    
    start_date : Any
        Input parameter `start_date`.
    
    end_date : Any
        Input parameter `end_date`.
    
    Returns
    -------
    Any
        Return value from `get_timestamps_from_sql`.
    """
    conn = sqlite3.connect(path)

    statement = dates_statement(frequency)
    rows = conn.execute(statement)
    timestamps = parse_sql_timestamps(rows)

    if start_date or end_date:
        timestamps = filter_timestamps(timestamps, start_date, end_date)

    conn.close()
    return timestamps


def get_results_from_sql(
    path, variables, frequency, alike=False, start_date=None, end_date=None
):
    """
    Get results from sql.
    
    Parameters
    ----------
    path : Any
        Input parameter `path`.
    
    variables : Any
        Input parameter `variables`.
    
    frequency : Any
        Input parameter `frequency`.
    
    alike : Any
        Input parameter `alike`.
    
    start_date : Any
        Input parameter `start_date`.
    
    end_date : Any
        Input parameter `end_date`.
    
    Returns
    -------
    Any
        Return value from `get_results_from_sql`.
    """
    conn = sqlite3.connect(path)
    variables = [variables] if isinstance(variables, Variable) else variables
    sql_frequency = to_sql_frequency(frequency)
    ids_dict = get_ids_dict(conn, variables, sql_frequency, alike)
    rd = ResultsDictionary(frequency)
    for id_, variable in ids_dict.items():
        if start_date or end_date:
            rd[variable] = get_sliced_outputs(conn, id_, start_date, end_date)
        else:
            rd[variable] = get_outputs(conn, id_)
    rd.time_series = get_timestamps_from_sql(path, frequency, start_date, end_date)
    conn.close()
    return rd

