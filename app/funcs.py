from datetime import datetime

def getNumBuisnessWeeks():
    # this is the starting week of the buisness, weeks are then itterated from this date
    # there is 0 revenue from before this date
    firstWeek = datetime(2024, 2, 1)
    # this is the diff between the start week and current week
    # so number of weeks since first week
    return (((datetime.now() - firstWeek)).days) // 7