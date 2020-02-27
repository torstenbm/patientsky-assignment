import json, datetime, sys


############# Util #############

# Checks if overlap exists between two date ranges
# date_tuple has the shape of (datetime start, datetime end)
def has_overlap(date_tuple_1, date_tuple_2):
    if date_tuple_1[0] <= date_tuple_2[1] and date_tuple_1[1] >= date_tuple_2[0]:
        return True
    else:
        return False

# Concatenates adjacent timeslots of shape (datetime1, datetime2) into
# the longest possible continous timeslots of shape (datetime_i, datetime_j)
def concatenate_timeslots(list_of_timeslot_tuples):    
    if len(list_of_timeslot_tuples) == 0:
        return []
    if len(list_of_timeslot_tuples) == 1:
        return list_of_timeslot_tuples

    continous_blocks = []
    continous_block_start = list_of_timeslot_tuples[0][0]
    for i in range(len(list_of_timeslot_tuples)):
        start_i, end_i = list_of_timeslot_tuples[i]
        
        if i < len(list_of_timeslot_tuples)-1:
            start_j, end_j = list_of_timeslot_tuples[i+1]
        
        continous_block_end = end_i
        if end_i >= start_j:
            continous_block_end = end_j
        
        else:
            continous_blocks.append( (continous_block_start, continous_block_end) )
            continous_block_start = start_j
        
    continous_blocks.append( (continous_block_start, continous_block_end) )
    
    return continous_blocks

# Splits timeblocks of shape (datetime_1, datetime_2) into tuples of (datetime_i, datetime_j) 
# where the granularity is the difference between datetime_i and datetime_j.
def split_timeblocks(timeblocks, granularity=1):
    split_blocks = []
    
    for timeblock in timeblocks:
        cursor = timeblock[0]
        split_block = []
        while cursor < timeblock[1]:
            split_block.append( (cursor, cursor + datetime.timedelta(minutes=granularity)) )
            cursor += datetime.timedelta(minutes=granularity)
        split_blocks.append(split_block)

    return split_blocks

# Flatten arrays
flatten = lambda l: [item for sublist in l for item in sublist]



############# Models #############

class Appointment:
    def __init__(self, id, calendar_id, start, end):
        self.id = id
        self.calendar_id = calendar_id
        self.start = start
        self.end = end

class Timeslot:
    def __init__(self, id, calendar_id, start, end):
        self.id = id
        self.calendar_id = calendar_id
        self.start = start
        self.end = end

class Calendar:
    def __init__(self, id, appointments, timeslots):
        self.id = id
        self.appointments = appointments
        self.timeslots = timeslots
    
    def get_free_timeslots_in_period(self, period):
        try:
            period_start_string, period_end_string = period.split("/")
            period_start, period_end = datetime.datetime.fromisoformat(period_start_string), datetime.datetime.fromisoformat(period_end_string)
        except:
            print("The program did understand not the time interval.")
            print("Should be of form equal to 2019-04-23T08:00:00/2019-04-27T00:00:00.")
            sys.exit(0)
        
        timeslots_in_period = [timeslot for timeslot in self.timeslots if has_overlap( (timeslot.start, timeslot.end), (period_start, period_end) )]
        appointments_in_period = [appointment for appointment in self.appointments if has_overlap( (appointment.start, appointment.end), (period_start, period_end) )]

        free_time_slots_in_period = []
        for timeslot in timeslots_in_period:
            conflict_list = [has_overlap( (timeslot.start, timeslot.end), (appointment.start, appointment.end) ) for appointment in appointments_in_period]
            if not (True in conflict_list):
                free_time_slots_in_period.append(timeslot)
            
        return free_time_slots_in_period
    
    def get_continous_free_timeblocks_in_period(self, period):
        timeslot_starts_and_ends = [(timeslot.start, timeslot.end) for timeslot in self.get_free_timeslots_in_period(period)]
        timeslot_starts_and_ends.sort(key=lambda x: x[0])

        continous_blocks = concatenate_timeslots(timeslot_starts_and_ends)

        return continous_blocks
        


############# Loading data from files #############

patient_json_files = ["Danny boy.json", "Emma Win.json", "Joanna Hef.json"]

calendars_from_ids = {}
for file in patient_json_files:
    with open(file) as f:
        calendar_json = json.load(f)
        appointments = []
        timeslots = []
        for appointment_json in calendar_json["appointments"]:
            _id = appointment_json["id"]
            calendar_id = appointment_json["calendar_id"]
            start = datetime.datetime.fromisoformat(appointment_json["start"])
            end = datetime.datetime.fromisoformat(appointment_json["end"])
            appointments.append(Appointment(_id, calendar_id, start, end))
        
        for timeslot_json in calendar_json["timeslots"]:
            _id = timeslot_json["id"]
            calendar_id = timeslot_json["calendar_id"]
            start = datetime.datetime.fromisoformat(timeslot_json["start"])
            end = datetime.datetime.fromisoformat(timeslot_json["end"])
            timeslots.append(Timeslot(_id, calendar_id, start, end))
        
        calendar_id = appointments[0].calendar_id
        calendars_from_ids[calendar_id] = Calendar(calendar_id, appointments, timeslots)



############# Star of the show #############

def find_available_time(calendar_ids, duration, period_to_search):
    
    # Getting all free timeblocks from all calendars
    free_timeblocks_for_calendars = []
    for calendar_id in calendar_ids:
        calendar = calendars_from_ids[calendar_id]
        timeblocks = calendar.get_continous_free_timeblocks_in_period(period_to_search)
        free_timeblocks_for_calendars.append(timeblocks)

    # Splitting the all free timeslots into timeslots of 1 minute
    # to account for different lengths and start/end times
    granulated_timeblocks = [flatten(split_timeblocks(timeblocks)) for timeblocks in free_timeblocks_for_calendars]

    # Using set intersection to find all common free 1 minute timeslots 
    # present in all calendars
    common_free_timeslots_granulated = list(set(granulated_timeblocks[0]).intersection(*granulated_timeblocks))

    # Patching 1 minute timeslots back together to find longest continous
    # common free timeslots
    common_free_timeslots_granulated.sort(key=lambda x: x[0])
    common_free_timeslots = concatenate_timeslots(common_free_timeslots_granulated)

    # Filtering out timeslots shorter than meeting duration
    long_enough_common_free_timeslots = []
    for common_free_timeslot in common_free_timeslots:
        minutes_diff = (common_free_timeslot[1] - common_free_timeslot[0]).total_seconds() / 60.0
        if minutes_diff >= duration:
            long_enough_common_free_timeslots.append(common_free_timeslot)

    # Printing resulting timeblocks to the console
    print("Possible timeslots for appointment booking:")
    for timeslot in long_enough_common_free_timeslots:
        print(timeslot[0].strftime("%B %d %Y,")+" from " + timeslot[0].strftime("%H:%M") + " to " + timeslot[1].strftime("%H:%M"))



############# Running function for test calendars #############

calendar_ids = ["48cadf26-975e-11e5-b9c2-c8e0eb18c1e9", "452dccfc-975e-11e5-bfa5-c8e0eb18c1e9", "48644c7a-975e-11e5-a090-c8e0eb18c1e9"]
find_available_time(calendar_ids, 30, "2019-04-23T08:00:00/2019-04-27T00:00:00")
