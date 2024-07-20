import datetime
def convert_time_to_timestamp(time: datetime ):
    time = datetime.datetime.now()
    return int(f"{datetime.datetime.year}\
               {datetime.datetime.month}\
                {datetime.datetime.day}\
                {datetime.datetime.hour}
                \{datetime.datetime.minute}")
