from .constants import RP, TS, A, D, H, M
from .exceptions import CollectionRequired
from .processing.esofile_reader import process_eso_file
from .processing.esofile_time import (
    convert_raw_date_data,
    get_n_days_from_cumulative,
)


class DBEsoFile:
    def __init__(self, environment_name, header, outputs, dates, n_days, days_of_week):
        """
          init  .
        
        Parameters
        ----------
        environment_name : Any
            Input parameter `environment_name`.
        
        header : Any
            Input parameter `header`.
        
        outputs : Any
            Input parameter `outputs`.
        
        dates : Any
            Input parameter `dates`.
        
        n_days : Any
            Input parameter `n_days`.
        
        days_of_week : Any
            Input parameter `days_of_week`.
        
        Returns
        -------
        None
            Return value from `__init__`.
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
         from raw outputs.
        
        Parameters
        ----------
        raw_outputs : Any
            Input parameter `raw_outputs`.
        
        year : Any
            Input parameter `year`.
        
        Returns
        -------
        Any
            Return value from `_from_raw_outputs`.
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
        From path.
        
        Parameters
        ----------
        file_path : Any
            Input parameter `file_path`.
        
        year : Any
            Input parameter `year`.
        
        Returns
        -------
        Any
            Return value from `from_path`.
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
        Frequencies.
        
        Returns
        -------
        Any
            Return value from `frequencies`.
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
          init  .
        
        Parameters
        ----------
        db_eso_files : Any
            Input parameter `db_eso_files`.
        
        Returns
        -------
        None
            Return value from `__init__`.
        """
        self._db_eso_files = [] if not db_eso_files else db_eso_files

    @classmethod
    def from_path(cls, file_path, year=None):
        """
        From path.
        
        Parameters
        ----------
        file_path : Any
            Input parameter `file_path`.
        
        year : Any
            Input parameter `year`.
        
        Returns
        -------
        Any
            Return value from `from_path`.
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
        Environment names.
        
        Returns
        -------
        Any
            Return value from `environment_names`.
        """
        return [ef.environment_name for ef in self._db_eso_files]

    def __iter__(self):
        """
          iter  .
        
        Returns
        -------
        Any
            Return value from `__iter__`.
        """
        for item in self._db_eso_files:
            yield item

    def __getitem__(self, item):
        """
          getitem  .
        
        Parameters
        ----------
        item : Any
            Input parameter `item`.
        
        Returns
        -------
        Any
            Return value from `__getitem__`.
        """
        return self._db_eso_files[item]

    def __contains__(self, item):
        """
          contains  .
        
        Parameters
        ----------
        item : Any
            Input parameter `item`.
        
        Returns
        -------
        Any
            Return value from `__contains__`.
        """
        return item in self._db_eso_files

    def append(self, item):
        """
        Append.
        
        Parameters
        ----------
        item : Any
            Input parameter `item`.
        
        Returns
        -------
        Any
            Return value from `append`.
        """
        self._db_eso_files.append(item)

    def count(self):
        """
        Count.
        
        Returns
        -------
        Any
            Return value from `count`.
        """
        len(self._db_eso_files)

    def index(self, item):
        """
        Index.
        
        Parameters
        ----------
        item : Any
            Input parameter `item`.
        
        Returns
        -------
        Any
            Return value from `index`.
        """
        return self._db_eso_files.index(item)

    def extend(self, items):
        """
        Extend.
        
        Parameters
        ----------
        items : Any
            Input parameter `items`.
        
        Returns
        -------
        Any
            Return value from `extend`.
        """
        self._db_eso_files.extend(items)

    def insert(self, index, item):
        """
        Insert.
        
        Parameters
        ----------
        index : Any
            Input parameter `index`.
        
        item : Any
            Input parameter `item`.
        
        Returns
        -------
        Any
            Return value from `insert`.
        """
        self._db_eso_files.insert(index, item)

    def pop(self, index):
        """
        Pop.
        
        Parameters
        ----------
        index : Any
            Input parameter `index`.
        
        Returns
        -------
        Any
            Return value from `pop`.
        """
        return self._db_eso_files.pop(index)

    def remove(self, item):
        """
        Remove.
        
        Parameters
        ----------
        item : Any
            Input parameter `item`.
        
        Returns
        -------
        Any
            Return value from `remove`.
        """
        self._db_eso_files.remove(item)

    def reverse(self):
        """
        Reverse.
        
        Returns
        -------
        Any
            Return value from `reverse`.
        """
        reversed(self._db_eso_files)

    def sort(self, reverse):
        """
        Sort.
        
        Parameters
        ----------
        reverse : Any
            Input parameter `reverse`.
        
        Returns
        -------
        Any
            Return value from `sort`.
        """
        self._db_eso_files.sort(key=lambda ef: ef.file_name, reverse=reverse)

