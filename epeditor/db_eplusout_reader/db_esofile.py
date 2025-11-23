from db_eplusout_reader.constants import RP, TS, A, D, H, M
from db_eplusout_reader.exceptions import CollectionRequired
from db_eplusout_reader.processing.esofile_reader import process_eso_file
from db_eplusout_reader.processing.esofile_time import (
    convert_raw_date_data,
    get_n_days_from_cumulative,
)


class DBEsoFile:
    def __init__(self, environment_name, header, outputs, dates, n_days, days_of_week):
        """
        Represents processed EnergyPlus eso file output data.

        Results are stored in bins identified by output frequency.

        Parameters
        ----------
        environment_name : str
            A name of the environment.
        header : dict of {str, dict of {int, Variable}}
            Processed header dictionary.
        outputs : dict of {str, dict of {int, list of float}}
            Processed numeric outputs.
        dates : dict of {str, datetime}
            Parsed dates.
        n_days : dict of {str, list of int}
            Number of days for each step for monthly to runperiod frequencies.
        days_of_week:
            Day of week for each step for timestep to daily frequencies.

        Example
        -------
        environment_name 'TEST (01-01:31-12)'
        header {
            'hourly' : {
                Variable(key='B1:ZONE1', type='Zone Mean Air Temperature', units='C'): 322,
                Variable(key='B1:ZONE2', type='Zone Air Relative Humidity', units='%'): 304
                ...
            },
            'daily' : {
                Variable(key='B1:ZONE1', type='Zone Air Relative Humidity', units='%'): 521,
                Variable(key='B1:ZONE2', type='Zone Air Relative Humidity', units='%'): 565
                ...
            }
        }
        outputs {
            'hourly' : {
               322 : [17.906587634970627, 17.198486368112462, 16.653197201251096, ...]
               304 : [0.006551864336487204, 0.0061786832466626095, 0.005800374315868216, ...]
                ...
            },
            'daily' : {
                521 : [38.83017767728567, 48.74604212532369, 41.69013850729892, ...]
                565 : [43.25127519033924, 55.42681891740626, 42.215387940031526, ...]
                ...
            }
        }
        dates {
            'hourly' : [
                datetime.datetime(2002, 1, 1, 1, 0),
                datetime.datetime(2002, 1, 1, 2, 0),
                datetime.datetime(2002, 1, 1, 3, 0),
                ...
            ],
            'daily' : [
                datetime.datetime(2002, 1, 1, 0, 0),
                datetime.datetime(2002, 1, 2, 0, 0),
                datetime.datetime(2002, 1, 3, 0, 0),
                ...
        }
        n_days {
            'monthly': [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
            'annual': [365],
            'runperiod': [365]
        }
        days_of_week {
            'hourly': ['Tuesday', 'Tuesday', 'Tuesday', 'Tuesday', ...],
            'daily': ['Tuesday', 'Wednesday', 'Thursday', 'Friday', ...],
            ...
        }

        """
        self.environment_name = environment_name
        self.header = header
        self.outputs = outputs
        self.dates = dates
        self.n_days = n_days
        self.days_of_week = days_of_week

    @classmethod
    def _from_raw_outputs(cls, raw_outputs, year):
        """
        Create an instance from raw output data.
        
        Parameters
        ----------
        cls : type
            The class constructor, used to instantiate the object.
        raw_outputs : object
            An object containing raw output data with attributes: dates, days_of_week, 
            cumulative_days, environment_name, header, and outputs.
        year : int
            The year used to interpret and convert the raw date data.
        
        Returns
        -------
        cls
            An instance of the class initialized with processed data from raw_outputs.
        """
        dates = convert_raw_date_data(raw_outputs.dates, raw_outputs.days_of_week, year)
        n_days = get_n_days_from_cumulative(raw_outputs.cumulative_days)
        return cls(
            environment_name=raw_outputs.environment_name,
            header=raw_outputs.header,
            outputs=raw_outputs.outputs,
            dates=dates,
            n_days=n_days,
            days_of_week=raw_outputs.days_of_week,
        )

    @classmethod
    def from_path(cls, file_path, year=None):
        """
        Create an instance from a given file path.
        
        Parameters
        ----------
        file_path : str
            Path to the ESO file to be processed.
        year : int, optional
            The calendar year to associate with the data. If not provided, defaults to None.
        
        Returns
        -------
        DBEsoFile
            An instance of DBEsoFile constructed from the processed ESO file data.
        
        """
        all_raw_outputs = process_eso_file(file_path)
        if len(all_raw_outputs) == 1:
            return cls._from_raw_outputs(all_raw_outputs[0], year)
        raise CollectionRequired(
            "Cannot process file {}. "
            "as there are multiple environments included.\n"
            "Use 'DBEsoFileCollection.from_path' "
            "to generate multiple files."
            "".format(file_path)
        )

    @property
    def frequencies(self):
        """
        Sorted list of frequency keys from the header, ordered by predefined priority.
        
        Returns
        -------
        list
            A list of frequency keys (e.g., TS, H, D, M, A, RP) sorted according to 
            the predefined order: TS (0), H (1), D (2), M (3), A (4), RP (5).
        """
        order = {TS: 0, H: 1, D: 2, M: 3, A: 4, RP: 5}
        return sorted(list(self.header.keys()), key=lambda x: order[x])


class DBEsoFileCollection:
    """
    Custom list to hold processed .eso file data.

    The collection can be populated by passing a path into
    'DBEsoFileCollection.from_path(some/path.eso)' class
    factory method.

    Parameters
    ----------
    db_eso_files : list of DBEsoFile or None
        A processed list of EnergyPlus output .eso files.

    """

    def __init__(self, db_eso_files=None):
        """
        Initialize the instance with a list of ESO database files.
        
        Parameters
        ----------
        db_eso_files : list, optional
            List of ESO database file paths. If not provided, an empty list is assigned.
        
        Returns
        -------
        None
        """
        self._db_eso_files = [] if not db_eso_files else db_eso_files

    @classmethod
    def from_path(cls, file_path, year=None):
        """
        Create an instance from a file path by processing ESO data.
        
        Parameters
        ----------
        cls : type
            The class constructor, used to instantiate the object.
        file_path : str
            Path to the ESO file to be processed.
        year : int, optional
            The year to associate with the ESO data. If not provided, defaults to None.
        
        Returns
        -------
        cls
            An instance of the class containing processed DBEsoFile objects.
        """
        all_raw_outputs = process_eso_file(file_path)
        db_eso_files = []
        for raw_outputs in all_raw_outputs:
            db_eso_file = DBEsoFile._from_raw_outputs(raw_outputs, year)
            db_eso_files.append(db_eso_file)
        return cls(db_eso_files)

    @property
    def environment_names(self):
        """
        Names of the environments associated with the ESO files.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the `_db_eso_files` attribute.
        
        Returns
        -------
        list of str
            A list of environment names extracted from the `_db_eso_files` attribute.
        """
        return [ef.environment_name for ef in self._db_eso_files]

    def __iter__(self):
        """
        Iterate over items in the internal database ESO files list.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the `_db_eso_files` attribute.
        
        Returns
        -------
        generator
            A generator yielding each item in `self._db_eso_files`.
        """
        for item in self._db_eso_files:
            yield item

    def __getitem__(self, item):
        """
        Return the item from the database of ESO files by index or key.
        
        Parameters
        ----------
        item : int or str
            Index or key to access a specific ESO file in the database.
        
        Returns
        -------
        Any
            The ESO file object corresponding to the given index or key.
        """
        return self._db_eso_files[item]

    def __contains__(self, item):
        """
        Check if an item exists in the internal database of ESO files.
        
        Parameters
        ----------
        item : object
            The item to check for existence in the `_db_eso_files` collection.
        
        Returns
        -------
        bool
            True if the item is present in `_db_eso_files`, False otherwise.
        """
        return item in self._db_eso_files

    def append(self, item):
        """
        Append an item to the internal database of ESO files.
        
        Parameters
        ----------
        item : any
            The item to be appended to the internal list `_db_eso_files`.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        self._db_eso_files.append(item)

    def count(self):
        """Count the number of ESO database files.
        
                Returns
                -------
                int
                    The number of ESO database files in `_db_eso_files`.
                """
        len(self._db_eso_files)

    def index(self, item):
        """
        Return the index of the first occurrence of the specified item in the database ESO files list.
        
        Parameters
        ----------
        item : object
            The item to find the index of in the `_db_eso_files` list.
        
        Returns
        -------
        int
            The index of the first occurrence of `item` in the `_db_eso_files` list.
        """
        return self._db_eso_files.index(item)

    def extend(self, items):
        """
        Extend the internal list of ESO files with the given items.
        
        Parameters
        ----------
        items : iterable
            An iterable of items to append to the internal `_db_eso_files` list.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        self._db_eso_files.extend(items)

    def insert(self, index, item):
        """
        Insert an item at the specified index in the internal list of ESO files.
        
        Parameters
        ----------
        index : int
            The position at which to insert the item.
        item : object
            The item to insert into the list.
        
        Returns
        -------
        None
            This function does not return a value.
        """
        self._db_eso_files.insert(index, item)

    def pop(self, index):
        """
        Remove and return an item at the specified index from the database ESO files list.
        
        Parameters
        ----------
        index : int
            The index of the item to remove and return from the list.
        
        Returns
        -------
        object
            The item that was removed from the list at the specified index.
        """
        return self._db_eso_files.pop(index)

    def remove(self, item):
        """
        Remove an item from the database ESO files list.
        
        Parameters
        ----------
        item : object
            The item to be removed from the internal `_db_eso_files` list.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        self._db_eso_files.remove(item)

    def reverse(self):
        """Reverse the order of elements in the _db_eso_files list.
        
                This method attempts to reverse the order of elements in the internal `_db_eso_files` list.
                Note: The current implementation uses `reversed()` without reassigning the result, which does not modify the list in place.
        
                Parameters
                ----------
                self : object
                    The instance of the class containing the `_db_eso_files` attribute.
        
                Returns
                -------
                None
                    This method does not return any value (or returns None) as it currently does not effectively modify the list.
                """
        reversed(self._db_eso_files)

    def sort(self, reverse):
        """
        Sort the database ESO files by file name.
        
        Parameters
        ----------
        reverse : bool
            If True, sort in descending order; otherwise, sort in ascending order.
        
        Returns
        -------
        None
            This function modifies the list in place and does not return a value.
        """
        self._db_eso_files.sort(key=lambda ef: ef.file_name, reverse=reverse)
