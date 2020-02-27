# Patientsky case solution

This python script is a solution for the Patiensky assignment to make a small program that can list available times for a meeting for several participants.

The main function produced `find_available_time(calendar_ids, duration, period)` takes as input a list of the id's (strings) of the calendars of the participants, the duration of the meeting in minutes (int) and the time period of which to search for an available time (ISO8601 time interval string).

## Installation

The program uses python 3 and the built-in json, datetime and sys modules. It requires no further installation.

## Usage
To run the program for the dummy data Danny boy.json, Emma Win.json and Joanna Hef.json, the duration 30 minutes, and the time interval string 2019-04-23T08:00:00/2019-04-27T00:00:00, execute the script. 

To run the script for your own data, place your patient json-files in the same directory as the script and add them to the list on line 116. Run the function with your own parameters at the bottom of the script.


## Contributing
Pull requests are welcome, but would be kind of weird.

## License
[MIT](https://choosealicense.com/licenses/mit/)