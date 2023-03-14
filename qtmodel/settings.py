from datetime import datetime
from typing import Union

from qtmodel.patterns.singleton import SingletonType
from qtmodel.utilities.observablevalue import ObservableValue


class DateProxy(ObservableValue):
    def __init__(self,
                 value: datetime = datetime(datetime.today().year, datetime.today().month, datetime.today().day)):
        super().__init__(value=value)


class Settings(metaclass=SingletonType):
    def __init__(self):
        self._evaluation_date = DateProxy()
        self.include_reference_date_events = False
        self.include_todays_cash_flows: Union[bool, None] = None
        self.enforces_todays_historic_fixings = False

    def anchor_evaluation_date(self):
        # set to today's date if not already set.
        if self._evaluation_date.value is None:
            today = datetime.today()
            self._evaluation_date.value = datetime(today.year, today.month, today.day)
        # If set, no-op since the date is already anchored.

    def reset_evaluation_date(self):
        self._evaluation_date.value = None

    @property
    def evaluation_date(self):
        return self._evaluation_date.value

    @evaluation_date.setter
    def evaluation_date(self, v: datetime):
        self._evaluation_date.value = v


class SavedSettings:

    def __init__(self):
        self.evaluation_date: DateProxy = Settings().evaluation_date
        self.include_reference_date_events: bool = Settings().include_reference_date_events
        self.include_todays_cash_flows: Union[bool, None] = Settings().include_todays_cash_flows
        self.enforces_todays_historic_fixings: bool = Settings().enforces_todays_historic_fixings

    def __del__(self):
        try:
            if Settings().evaluation_date != self.evaluation_date:
                Settings().evaluation_date = self.evaluation_date
            Settings().include_reference_date_events = self.include_reference_date_events
            Settings().include_todays_cash_flows = self.include_todays_cash_flows
            Settings().enforces_todays_historic_fixings = self.enforces_todays_historic_fixings
        except Exception:
            ...  # nothing we can do except bailing out.
