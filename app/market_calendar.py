import datetime
import pytz
import holidays


GHANA_TZ=pytz.timezone("Afica/Accra")
gh_holidays=holidays.CountryHoliday("GH")

def is_weekend(date):
    return date.weekday()>=5

def is_public_holiday(date):
    return date in gh_holidays

def is_market_hours(now=None):
    if not now:
        now=datetime.datetime.now(GHANA_TZ)

    market_open=now.replace(hour=10,minute=0,second=0,microsecond=0)
    market_close=now.replace(hour=15,minute=0,second=0,microsecond=0)

    return market_open <= now <=market_close

def is_market_open():
    now=datetime.datetime.now(GHANA_TZ)
    today=now.date()

    if is_weekend(today):
        print("Market closed: weekend")
        return False
    
    if is_public_holiday(today):
        print("Market closed public holiday")

        return False
    
    if not is_market_hours(now):
        print("market closed: Outside trading hours")
        return False
    
    return True