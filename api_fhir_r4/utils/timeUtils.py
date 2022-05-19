import core
from dateutil import parser


class TimeUtils(object):

    @classmethod
    def now(cls):
        return core.datetime.datetime.now()

    @classmethod
    def date(cls):
        return core.datetime.datetime.date(cls.now())

    @classmethod
    def str_to_date(cls, str_date, str_time="00:00:00"):
        py_date = parser.parse(f"{str_date} {str_time}")
        return core.datetime.datetime.from_ad_datetime(py_date)

    @classmethod
    def str_iso_to_date(cls, str_iso_datetime):
        py_date = parser.parse(f"{str_iso_datetime}")
        return core.datetime.datetime.from_ad_datetime(py_date)
