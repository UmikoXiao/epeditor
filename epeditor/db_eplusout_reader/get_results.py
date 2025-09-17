import os

from db_eplusout_reader.db_esofile import DBEsoFile, DBEsoFileCollection
from db_eplusout_reader.sql_reader import get_results_from_sql


def get_results(
    file_or_path, variables, frequency, alike=False, start_date=None, end_date=None
):
    r"""
    Extract results from given file.

    Use a single or list of 'Variable' named tuples to specify requested outputs.

    v = Variable(
        key="PEOPLE BLOCK1:ZONE2",
        type="Zone Thermal Comfort Fanger Model",
        units=None
    )

    When one (or multiple) 'Variable' fields would be set as None, filtering
    for specific part of variable will not be applied.

    Variable(None, None, None) returns all outputs
    Variable(None, None, "J") returns all 'energy' outputs.

    Frequency defines output interval - it can be one of "timestep", "hourly", "daily",
    "monthly" "annual" and "runperiod". Constants module includes helpers TS, H, D, M, A, RP.

    Function needs to be called multiple times to get results from various intervals.

    Alike optional argument defines whether variable search should filter results by
    full or just a substring (search is always case insensitive).

    Start and end date optional arguments can slice resulting array based on timestamp data.


    Examples
    --------
    from datetime import datetime

    from db_esofile_reader import Variable, get_results
    from db_esofile_reader.constants import D


    variables = [
         Variable("", "Electricity:Facility", "J"), # standard meter
         Variable("Cumulative", "Electricity:Facility", "J"), # cumulative meter
         Variable(None, None, None), # get all outputs
         Variable("PEOPLE BLOCK1:ZONE2", "Zone Thermal Comfort Fanger Model PMV", ""),
         Variable("PEOPLE BLOCK", "Zone Thermal Comfort Fanger Model PMV", "")
    ]

    # get results for variables fully matching output variables
    # the last variable above won't be found as variable 'key' does not fully match
    # variables will be extracted from 'daily' interval results
    # start and end date slicing is not applied

    results = get_results(
        r"C:\some\path\eplusout.sql",
        variables=variables,
        frequency=D,
        alike=False
    )

    # 'alike' argument is set to True so even substring match is enough to match variable
    # the last variable will be found ("PEOPLE BLOCK" matches "PEOPLE BLOCK1:ZONE2")
    # start and end dates are specified so only 'May' data will be included

    results = get_results(
        r"C:\some\path\eplusout.sql",
        variables=variables,
        frequency=D,
        alike=True,
        start_date=datetime(2002, 5, 1, 0),
        end_date=datetime(2002, 5, 31, 23, 59)
    )

    Parameters
    ----------
    file_or_path : DBEsoFile, DBEsoFileCollection or PathLike
        A processed EnergyPlus .eso file, path to unprocessed .eso file
        or path to unprocessed .sql file.
    variables : Variable or List of Variable
        Requested output variables.
    frequency : str
        An output interval, this can be one of {TS, H, D, M, A, RP} constants.
    alike : default False, bool
        Specify if full string or only part of variable attribute
        needs to match, filtering is case insensitive in both cases.
    start_date : default None, datetime.datetime
        Lower datetime interval boundary, inclusive.
    end_date : default None, datetime.datetime
        Upper datetime interval boundary, inclusive.

    Returns
    -------
    ResultsDictionary : Dict of {Variable, list of float}
        A dictionary like class with some properties to easily extract output values.

    """
    if isinstance(file_or_path, str):
        _, ext = os.path.splitext(file_or_path)
        if ext == ".sql":
            results = get_results_from_sql(
                file_or_path,
                variables,
                frequency,
                alike=alike,
                start_date=start_date,
                end_date=end_date,
            )
        elif ext == ".eso":
            raise NotImplementedError("Sorry, this has not been implemented yet.")
        else:
            raise TypeError("Unsupported file type '{}' provided!".format(ext))
    else:
        if isinstance(file_or_path, (DBEsoFile, DBEsoFileCollection)):
            raise NotImplementedError("Sorry, this has not been implemented yet.")
        else:
            raise TypeError(
                "Unsupported class '{}' provided!".format(type(file_or_path).__name__)
            )
    return results
