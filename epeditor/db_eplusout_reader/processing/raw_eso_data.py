from collections import defaultdict

from db_eplusout_reader.constants import RP, A, M


class RawOutputData:
    def __init__(self, environment_name, header):
        """
        Initialize the simulation environment with given name and header.
        
        Parameters
        ----------
        environment_name : str
            Name of the environment for the simulation.
        header : dict
            Header information containing metadata for the simulation.
        
        Returns
        -------
        None
            This constructor does not return a value.
        """
        self.environment_name = environment_name
        self.header = header
        (
            self.outputs,
            self.dates,
            self.cumulative_days,
            self.days_of_week,
        ) = self.initialize_results_bins()

    def initialize_results_bins(self):
        """
        Initialize and return empty data structures for storing results based on frequency and variable IDs.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the `header` attribute, which maps frequency keys to variable dictionaries.
            Expected to have a `header` attribute where keys are frequency constants (e.g., M, A, RP) and values are dictionaries
            mapping variable identifiers to their respective IDs.
        
        Returns
        -------
        tuple
            A tuple containing four elements:
            - outputs : collections.defaultdict of dict
                Nested dictionaries initialized as empty lists for each variable ID, keyed by frequency and ID.
            - dates : dict
                Dictionary with frequency keys and empty list values to store date information.
            - cumulative_days : dict
                Dictionary with frequency keys (M, A, RP) and empty list values to store cumulative day counts.
            - days_of_week : dict
                Dictionary with frequency keys (not M, A, RP) and empty list values to store days of the week.
        """
        outputs = defaultdict(dict)
        dates = {}
        cumulative_days = {}
        days_of_week = {}
        for frequency, variables in self.header.items():
            dates[frequency] = []
            if frequency in (M, A, RP):
                cumulative_days[frequency] = []
            else:
                days_of_week[frequency] = []
            for id_ in variables.values():
                outputs[frequency][id_] = []
        return outputs, dates, cumulative_days, days_of_week

    def initialize_next_outputs_step(self, frequency):
        """
        Initialize the next step for outputs at a given frequency by appending NaN values.
        
        Parameters
        ----------
        frequency : hashable
            The key specifying the frequency level in the outputs dictionary whose values 
            will be extended with NaN.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        for value in self.outputs[frequency].values():
            value.append(float("nan"))
