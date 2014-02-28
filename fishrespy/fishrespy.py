import re
import time
import csv
from datetime import datetime, timedelta
from numpy import array, ones, linalg, mean, std

class RawFileParse:
    """
    Class to parse raw output file from PreSens Oxyview PST3-V7.01 (untested on
    other versions) recorded with a Fibox 3 fiber optic oxygen transmitter.
    Removes header and extracts only data from closed cycles.
    Data stored includes the variables date (dd/mm/yy), time (hh:mm:ss), O2 (mg/L) and temp
    (deg C).  The class method get_data() returns a dictionary.  Key values refer
    to cycle index value (0 to total # of closed cycles - 1).  Each key is another
    dictionary whose key values refer to a list for each data variable representing
    all the data for the particular variable from a single closed cycle.

    Inputs:
        file - directory path to raw file, string.
        start_time - start time for first closed cycle, string
        start_date - start date for first closed cycle, string
        cycle_time - duration of closed cycle, list or tuple [minutes, seconds]
    """

    def __init__(self, file, start_time, start_date, cycle_time):
        self.file = file
        self.cycle_time = cycle_time
        self.start_time = start_time
        self.start_date = start_date
        self.start_dateTime = start_date + ' ' + start_time
        self.TIME_FORMAT = '%H:%M:%S'
        self.DATETIME_FORMAT = '%d/%m/%y %H:%M:%S'
        self.end_dateTime = self.add_time(self.convert_str_dateTime(self.start_dateTime),
                                      self.cycle_time[0],
                                      self.cycle_time[1])
        #group lacations for result of re.search
        self.DATE, self.TIME, self.O2, self.TEMPC = 1, 2, 4, 7
        self.GROUPS = [self.DATE, self.TIME, self.O2, self.TEMPC]
        self.regex = re.compile(r'([\d+/]+\d+);\s+([\d+:]+\d+);\s+(\d+.\d+);\s+(\d+.\d+);\s+(\d+.\d+);\s+(\d+);\s+(\d+.\d+);')
        self.bin_data = self.extract_data()

    def check_data(self, line):
        """
        Searches line for regular expression (regex) representing data
        structure for multiline data. Returns False if the line doesn't
         match.  If line does match, returns MatchObject. Used to strip header.
        """
        m = re.search(self.regex, line)
        if m == None: return False
        else: return m

    def convert_str_dateTime(self, s, mode = 1):
        """
        Convert a time in string format (s) to datetime format, returns datetime object.
        Mode 1 = 'datetime' string, Mode = 2 = 'time' string
        """
        if mode == 1:
            return datetime.strptime(s, self.DATETIME_FORMAT)
        if mode == 2:
            return datetime(*time.strptime(s, self.TIME_FORMAT)[:6])

    def list_dateTime(self, s, mode = 1):
        """Create a 2-value list with [time, time + 1 second] in datetime format
           from string (s). Returns list.
           Mode = 1 'datetime' string, Mode = 2, 'time' string
        """
        dt = self.convert_str_dateTime(s, mode)
        dt1 = dt + timedelta(seconds = 1)
        return [dt, dt1]

    def convert_dateTime_string(self, t, mode = 1):
        """
        Convert a datetime object (t) to string, returns string.
        Mode = 1 'datetime' string, Mode = 2 'time' string
        """
        if mode == 1:
            if isinstance(t, list):
                return [t[0].strftime(self.DATETIME_FORMAT), t[1].strftime(self.DATETIME_FORMAT)]
            else:
                return t.strftime(self.DATETIME_FORMAT)
        if mode == 2:
            if isinstance(t, list):
                return [t[0].strftime(self.TIME_FORMAT), t[1].strftime(self.TIME_FORMAT)]
            else:
                return t.strftime(self.TIME_FORMAT)

    def add_time(self, dt, nmin, nsec):
        """Adds timedelta object to datetime object (dt), returns string"""
        return self.convert_dateTime_string(dt + timedelta(minutes = nmin, seconds = nsec))

    def increment_time(self, start_dateTime, end_dateTime, mode = 1):
        """
        Increments datetime object by cycle_time (min,sec). Returns datetime
        object and two values list of datetime objects.
        Mode = 1 'start_time' is incremented, Mode = 2 'end_time' is incremented
        """
        if mode == 1:
            start_dateTime = self.add_time(self.convert_str_dateTime(end_dateTime),
                                       self.cycle_time[0],
                                       self.cycle_time[1])
            start_dateTime_list = self.list_dateTime(start_dateTime)
            return start_dateTime, start_dateTime_list

        if mode == 2:
            end_dateTime = self.add_time(self.convert_str_dateTime(start_dateTime),
                                     self.cycle_time[0],
                                     self.cycle_time[1])
            end_dateTime_list = self.list_dateTime(end_dateTime)
            return end_dateTime, end_dateTime_list

    def extract_line_data(self, match):
        """
        Extracts data for a single line (data point).  Converts O2 and temp
        variables to float. Returns list of data for that data point.
        """
        line_data = []
        for i in self.GROUPS:
            if i in [self.O2, self.TEMPC]:
                line_data.append(float(match.group(i)))
            else:
                line_data.append(match.group(i))
        return line_data

    def extract_data(self):
        """
        Bins data into groupings based on the cycle_time and time of first
        close (initial start_time), with cycle_time between each bin.
        Returns dictionary object with cycle count (begins with 0) mapped to
        a list of a list of data lines.
        """
        bin_data = {}
        data = []
        count = 0
        record, first_flag_set = False, False
        start_dateTime = self.start_dateTime
        end_dateTime_list = self.list_dateTime(self.end_dateTime)
        end_dateTime = self.end_dateTime

        with open(self.file, 'r') as f:
            for line in f:
                match = self.check_data(line)
                if not match:
                    continue
                else:
                    if not first_flag_set:
                        curr_time = match.group(self.TIME)
                        #checks against list of [start_time, start_time + 1 second] to account for
                        #seconds which weren't written to raw data file
                        if curr_time in self.convert_dateTime_string(self.list_dateTime(self.start_time, mode = 2), mode = 2):
                            end_dateTime, end_dateTime_list = self.increment_time(start_dateTime, end_dateTime, mode = 2)
                            data.append(self.extract_line_data(match))
                            record = True
                            first_flag_set = True
                            continue
                        else:
                            continue
                    curr_dateTime = match.group(self.DATE) + ' ' + match.group(self.TIME)
                    if not record:
                        #if reached start time
                        if curr_dateTime in self.convert_dateTime_string(start_dateTime_list):
                            record = True
                            end_dateTime, end_dateTime_list = self.increment_time(start_dateTime, end_dateTime, mode = 2)
                            data.append(self.extract_line_data(match))
                            continue
                        else:
                            continue
                    if record:
                        #if reached end time
                        if curr_dateTime in self.convert_dateTime_string(end_dateTime_list):
                            record = False
                            start_dateTime, start_dateTime_list = self.increment_time(start_dateTime, end_dateTime)
                            bin_data[count] = data
                            count += 1
                            data = []
                        else:
                            data.append(self.extract_line_data(match))
        return bin_data

    def list_to_dict(self, lst):
        """
        takes a list of lists and returns a dict with key = data type
        ('date', 'time', 'O2', 'tempC') with value = a list of all data
        for that data type in the closed cycle
        """
        tmp = {0: [], 1: [], 2: [], 3: []}
        for line in lst:
            for key in tmp:
                tmp[key].append(line[key])
        d = {'date': tmp[0], 'time': tmp[1], 'O2': tmp[2], 'tempC': tmp[3]}
        return d

    def formatData(self, d):
        """
        Takes output from RawFileParse.extract_data() and returns dict object,
        key = cycle count, value = dict with a key for each data type ('date',
        'time', 'O2', 'tempC').  Each data type is a list of that data type for
        the closed cycle in cycle count
        """
        for key in d:
            d[key] = self.list_to_dict(d[key])
        return d

    def get_data(self):
        return self.formatData(self.bin_data)

    def store_data(self):
        # use pickle if need method to store results of file parse
        pass

##############################################


class MO2Calculate:
    """
    Class to calculate oxygen consumption for each closed cycle in a single
    experiment.  Quality control method included to account for missing values
    in the time series, affects slope values. The class method get_data() returns
    a dictionary of summary data for each closed cycle.

    Inputs:
        data - dictionary returned from RawFileParse.get_data()
        mass - mass of fish
        volume - volume of chamber
    """
    def __init__(self, data, mass, volume, cycle_time):
        self.data = data
        self.mass = mass
        self.volume = volume
        self.cycle_time = cycle_time
        self.DATETIME_FORMAT = '%d/%m/%y %H:%M:%S'
        self.output = self.storeMO2()

    def get_close(self, cycle_count):
        """Extract and return values for a single closed cycle from data"""
        return self.data[cycle_count]

    def get_var(self, close, var):
        """Extract and return single variable from a single closed cycle.
           Var is a string representing the variable to be extracted
           Variables include 'O2', 'tempC', 'date', 'time'
        """
        return close[var]

    def get_sec_string(self, timeString):
        """Extracts and returns the seconds component of timeString"""
        return int(timeString[6:])

    def str_to_datetime(self, date, time):
        """Generates a timeseries (in seconds) of datetime objects
           starting at the first date and time of a closed cycle with length
           equal to the number of data points in the closed cycle. Used in
           quality_control().  Date and time are lists of all values for each
           variable in a closed cycle.
           """
        dateTime = datetime.strptime(date[0] + ' ' + time[0], self.DATETIME_FORMAT)
        prev = self.get_sec_string(time[0])
        output = [dateTime]
        tot_sec = 0

        for i in range(1,len(time)):
            curr = self.get_sec_string(time[i])
            diff = curr - prev
            if diff < 0:
                diff %= 60
            tot_sec += diff
            tdelt = timedelta(seconds = tot_sec)
            output.append(dateTime + tdelt)
            prev = curr
        return output

    def quality_control(self, date, time, O2):
        """Checks for missing values (values not recorded in raw file).  If value
           is missing, generates value for that time as the average of the
           previous and last values.  Returns list of O2 values for full 10 min
           period.
        """
        seconds = self.cycle_time[0] * 60 + self.cycle_time[1]
        start = datetime.strptime(date[0] + ' ' + time[0], self.DATETIME_FORMAT)
        sec = timedelta(seconds = 1)
        dt = self.str_to_datetime(date, time)
        dt_key = {}
        for i in range(len(dt)):
            dt_key[dt[i]] = O2[i]
        qc_dt = [start]
        for i in range(1, seconds): #number of seconds in close cycle
            qc_dt.append(qc_dt[i-1] + sec)
        qc_O2 = [0.] * seconds
        mvals = []
        for i in range(len(qc_dt)):
            if qc_dt[i] in dt_key:
                qc_O2[i] = dt_key[qc_dt[i]]
            else:
                mvals.append([i, qc_dt[i]])
                if i == 0:
                    sub = dt_key[qc_dt[i+1]]
                elif i == len(qc_dt) - 1:
                    sub = dt_key[qc_dt[i-1]]
                else:
                    prev = dt_key[qc_dt[i-1]]
                    nxt = dt_key[qc_dt[i+1]]
                    sub = (nxt + prev) / 2.
                qc_O2[i] = sub
        return qc_O2

    def fit_slope(self, O2):
        """Fits slope to O2 time series, returns slope and R-sq value"""
        x = range(len(O2))
        A = array([x, ones(len(O2))])
        y = O2
        model = linalg.lstsq(A.T, y)
        slope = model[0][0]
        SSE = model[1][0]
        mn = mean(O2)
        SST = sum((O2 - mn)**2)
        R2 = 1 - (SSE / SST)
        return slope, R2

    def O2consumption(self, slope, mass, volume):
        """
        Return MO2 (mgO2/kg/h)
        """
        return ((-slope * 3600) * (volume - mass)) / mass

    def storeMO2(self):
        """Calculates slope, R-sq, MO2, mean temp and sd temp for each closed
           cycle.  Returns dictionary of summary statistics for each closed cycle
        """
        new_data = {}

        for key in self.data:
            close = self.get_close(key)
            date = self.get_var(close, 'date')
            time = self.get_var(close, 'time')
            start = date[0] + ' ' + time[0]
            O2 = self.get_var(close, 'O2')
            tempC = self.get_var(close, 'tempC')
            qc_O2 = self.quality_control(date, time, O2)
            slope, R2 = self.fit_slope(qc_O2)
            MO2 = self.O2consumption(slope, self.mass, self.volume)
            meanTemp = mean(tempC)
            sdTemp = std(tempC)
            variables = [slope, R2, start, MO2, self.mass, meanTemp, sdTemp]
            new_data[key] = variables
        return new_data

    def get_data(self):
        """Returns output from _storeMO2()"""
        return self.output

    def save_data(self, file):
        """Writes output from _storeMO2() to .csv file with header. File is
           path to destination.
        """
        with open(file, 'w', newline = '') as f:
            w = csv.writer(f)
            header = ['slope', 'R2', 'start', 'MO2', 'mass', 'meanTemp', 'sdTemp']
            w.writerow(header)
            for row in range(len(self.output)):
                line = self.output[row]
                w.writerow(line)