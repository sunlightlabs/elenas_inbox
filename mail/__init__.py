def timedelta_to_days(td):
    return td.days + (td.seconds / (60*60*24.0))
