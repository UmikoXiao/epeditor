import os

from .db_esofile import DBEsoFile, DBEsoFileCollection
from .sql_reader import get_results_from_sql


def get_results(
    file_or_path, variables, frequency, alike=False, start_date=None, end_date=None
):
    """
    Get results.
    
    Parameters
    ----------
    file_or_path : Any
        Input parameter `file_or_path`.
    
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
        Return value from `get_results`.
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

