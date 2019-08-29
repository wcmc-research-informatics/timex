"""
Modification of NLTK-contrib timex.py: https://github.com/nltk/nltk_contrib/blob/master/nltk_contrib/timex.py
Original Copyright (C) 2001-2011 NLTK Project

Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Code for tagging temporal expressions in text
# For details of the TIMEX format, see http://timex2.mitre.org/

import re
import string
import os
import sys

# Requires eGenix.com mx Base Distribution
# http://www.egenix.com/products/python/mxBase/
try:
    from mx.DateTime import *
except ImportError:
    print ("""
Requires eGenix.com mx Base Distribution
http://www.egenix.com/products/python/mxBase/""")

#%%
# Predefined strings.
numbers = "(^a(?=\s)|one|two|three|four|five|six|seven|eight|nine|ten| \
          eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen| \
          eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty| \
          ninety|hundred|thousand)"
day = "(monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
week_day = "(monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
month = "((january|february|march|april|may|june|july|august|september| \
          october|november|december)|((jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)(?=\W)))"
mm = "(1|2|3|4|5|6|7|8|9|(10)|(11)|(12)|(01)|(02)|(03)|(04)|(05)|(06)|(07)|(08)|(09))"
dmy = "(year|day|week|month)"
rel_day = "(today|yesterday|tomorrow|tonight|tonite)"
exp1 = "(before|after|earlier|later|ago)"
exp2 = "(this|next|last)"
iso = "((^|(?<=\s))" + mm + "[/\.]\d{1,2}[/\.]\d{2,4}(?=\D))" #"(^|(?<=\s))\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}(?=\D)" #"\d+[/-]\d+[/-]\d+ \d+:\d+:\d+\.\d+"
year = "(?<=\s)[12][09]\d{2}(?=\D)" #"((?<=\s)\d{4}|^\d{4})"
mmyyyy = "((?<=\D)" + mm +"/([12][09])?\d{2}(?=\D))" #"(?<=\s)([1-9]|(10)|(11)|1/(19|20)?\d{2}(?=\D)"
season = "(spring|summer|fall|winter)"
longdate = "(" + month + "( \d{1,2}| of)?.? " + year + ")"
regxp1 = "((\d+|(" + numbers + "[-\s]?)+) " + dmy + "s? " + exp1 + ")"
regxp2 = "(" + exp2 + " (" + dmy + "|" + week_day + "|" + month + "))"
regxp3 = "(in (\d+|(" + numbers + "[-\s]?)+) " + dmy + "s?)"
regxp4 = "(" + season + "( of)? " + year + ")"


reg1 = re.compile(regxp1, re.IGNORECASE)
reg2 = re.compile(regxp2, re.IGNORECASE)
reg3 = re.compile(rel_day, re.IGNORECASE)
reg4 = re.compile(iso)
reg5 = re.compile(year)
reg6 = re.compile(mmyyyy)
reg7 = re.compile(longdate, re.IGNORECASE)
reg8 = re.compile(month, re.IGNORECASE)
reg9 = re.compile(regxp3, re.IGNORECASE)
reg10 = re.compile(regxp4, re.IGNORECASE)

#%%
def tag(text):

    # Initialization
    timex_found = []

    # re.findall() finds all the substring matches, keep only the full
    # matching string. Captures expressions such as 'number of days' ago, etc.
    found = reg1.findall(text)
    found = [a[0] for a in found if len(a) > 1]
    for timex in found:
        timex_found.append(timex)

    # Variations of this thursday, next year, etc
    found = reg2.findall(text)
    found = [a[0] for a in found if len(a) > 1]
    for timex in found:
        timex_found.append(timex)

    # today, tomorrow, etc
    found = reg3.findall(text)
    for timex in found:
        timex_found.append(timex)

    # mm-dd-yyyy
    found = reg4.findall(text)
    found = [a[0] for a in found if len(a) > 1]
    for timex in found:
        timex_found.append(timex)
#
#    # mmyy{yy}
    found = reg6.findall(text)
    found = [a[0] for a in found if len(a) > 1]
    for timex in found:
        timex_found.append(timex)
        
    #longdate
    found = reg7.findall(text)
    found = [a[0] for a in found if len(a) > 1]
    for timex in found:
        timex_found.append(timex)
        
    # Year
    found = reg5.findall(text)
    for timex in found:
        timex_found.append(timex)
        
    # month
    found = reg8.findall(text)
    found = [a[0] for a in found if len(a) > 1]
    for timex in found:
        timex_found.append(timex)
        
    # in x units
    found = reg9.findall(text)
    found = [a[0] for a in found if len(a) > 1]
    for timex in found:
        timex_found.append(timex)
        
    # season
    found = reg10.findall(text)
    found = [a[0] for a in found if len(a) > 1]
    for timex in found:
        timex_found.append(timex)

    # catch spans
    timex_spans = []
    # Tag only temporal expressions which haven't been tagged.
    tagtext = text
    for timex in timex_found:
        for match in re.finditer(timex, text):
            timex_spans.append([timex, match.span()[0], match.span()[1]])
        #text = re.sub(timex + '(?!</TIMEX2>)', '<TIMEX2>' + timex + '</TIMEX2>', text)
        tagtext = re.sub(timex + '(?!</TIMEX2>)', '<TIMEX2>' + timex + '</TIMEX2>', tagtext)

    # exclude timex if contained within another
    for timex in reversed(timex_found):
        tagtext = re.sub('<TIMEX2><TIMEX2>' + timex + '</TIMEX2>', '<TIMEX2>' + timex, tagtext)
 
    # reduce timex spans to only those in final tagged text
    timex_regex = re.compile(r'<TIMEX2>.*?</TIMEX2>', re.DOTALL)
    timex_found = timex_regex.findall(tagtext)
    timex_found = list(map(lambda timex: re.sub(r'</?TIMEX2.*?>', '', timex), timex_found))
    ts_df = pd.DataFrame(timex_spans, columns=['text', 'start', 'end'])
    
    final_spans = []
    for text, start, end in timex_spans:
        inclusive = ts_df[(ts_df.text!=text) & (ts_df.start <= start) & (ts_df.end >= end)]
        if inclusive.shape[0]==0 and [text, start, end] not in final_spans and text in timex_found:
            final_spans.append([text, start, end])
    #timex_spans = [item for item in timex_spans if item[0] in timex_found]
    
    return tagtext, final_spans

#%% return four digit year
def normYear(y):
    if y <= 19:
        return(2000 + y)
    elif y < 100:
        return(1900 + y)
    else:
        return y
#%% return two digit month or day
def normDM(x):
    if len(str(x)) == 1:
        return('0'+str(x))
    else:
        return str(x)
#%%
# Hash function for week days to simplify the grounding task.
# [Mon..Sun] -> [0..6]
hashweekdays = {
    'MONDAY': 0,
    'TUESDAY': 1,
    'WEDNESDAY': 2,
    'THURSDAY': 3,
    'FRIDAY': 4,
    'SATURDAY': 5,
    'SUNDAY': 6}

# Hash function for months to simplify the grounding task.
# [Jan..Dec] -> [1..12]
hashmonths = {
    'JANUARY': 1,
    'FEBRUARY': 2,
    'MARCH': 3,
    'APRIL': 4,
    'MAY': 5,
    'JUNE': 6,
    'JULY': 7,
    'AUGUST': 8,
    'SEPTEMBER': 9,
    'OCTOBER': 10,
    'NOVEMBER': 11,
    'DECEMBER': 12,
    'JAN' : 1,
    'FEB': 2,
    'MAR': 3,
    'APR': 4,
    'MAY': 5,
    'JUN': 6,
    'JUL': 7,
    'AUG': 8,
    'SEPT': 9,
    'SEP': 9,
    'OCT': 10,
    'NOV': 11,
    'DEC': 12}

# hash season 
hashseason = {
    'SPRING' : 3,
    'SUMMER' : 7,
    'FALL' : 9,
    'WINTER': 12}

# Hash number in words into the corresponding integer value
def hashnum(number):
    if re.match(r'one|^a\b', number, re.IGNORECASE):
        return 1
    if re.match(r'two', number, re.IGNORECASE):
        return 2
    if re.match(r'three', number, re.IGNORECASE):
        return 3
    if re.match(r'four', number, re.IGNORECASE):
        return 4
    if re.match(r'five', number, re.IGNORECASE):
        return 5
    if re.match(r'six', number, re.IGNORECASE):
        return 6
    if re.match(r'seven', number, re.IGNORECASE):
        return 7
    if re.match(r'eight', number, re.IGNORECASE):
        return 8
    if re.match(r'nine', number, re.IGNORECASE):
        return 9
    if re.match(r'ten', number, re.IGNORECASE):
        return 10
    if re.match(r'eleven', number, re.IGNORECASE):
        return 11
    if re.match(r'twelve', number, re.IGNORECASE):
        return 12
    if re.match(r'thirteen', number, re.IGNORECASE):
        return 13
    if re.match(r'fourteen', number, re.IGNORECASE):
        return 14
    if re.match(r'fifteen', number, re.IGNORECASE):
        return 15
    if re.match(r'sixteen', number, re.IGNORECASE):
        return 16
    if re.match(r'seventeen', number, re.IGNORECASE):
        return 17
    if re.match(r'eighteen', number, re.IGNORECASE):
        return 18
    if re.match(r'nineteen', number, re.IGNORECASE):
        return 19
    if re.match(r'twenty', number, re.IGNORECASE):
        return 20
    if re.match(r'thirty', number, re.IGNORECASE):
        return 30
    if re.match(r'forty', number, re.IGNORECASE):
        return 40
    if re.match(r'fifty', number, re.IGNORECASE):
        return 50
    if re.match(r'sixty', number, re.IGNORECASE):
        return 60
    if re.match(r'seventy', number, re.IGNORECASE):
        return 70
    if re.match(r'eighty', number, re.IGNORECASE):
        return 80
    if re.match(r'ninety', number, re.IGNORECASE):
        return 90
    if re.match(r'hundred', number, re.IGNORECASE):
        return 100
    if re.match(r'thousand', number, re.IGNORECASE):
      return 1000


#%%
# from list of discovered dates, process with ground date and return in list   
def groundList(timex_found, base_date):
    timex_grounded = []
    exceptions = []
    base_month = base_date.month
    base_year = base_date.year
    # set relative week anchor
    if base_date.weekday() == 0:
        base_week = 0
    else: 
        base_week = -1
        
    for timex in timex_found:
        timex_start = timex[1]
        timex_end = timex[2]
        timex_val = 'UNKNOWN'
        timex_ori = timex[0]
        timex = timex[0]
        
        norm_val = 'UNKNOWN'
        timex_format = 'UNKNOWN'
        
        # replace words with integers in relative statements
        if re.search(numbers, timex, re.IGNORECASE):
            split_timex = re.split(r'\s(?=days?|months?|years?|weeks?)', \
                                                              timex, re.IGNORECASE)
            value = split_timex[0]
            unit = split_timex[1]
            num_list = map(lambda s:hashnum(s),re.findall(numbers + '+', \
                                          value, re.IGNORECASE))
            timex = 'sum(num_list)' + ' ' + unit
        
        # replace season with month intgers
        if re.search(season, timex, re.IGNORECASE):
            timex = re.sub('of ', '', timex)
            split_timex = re.split(' ', timex)
            timex = str(hashseason[split_timex[0].upper()]) + '/' + split_timex[1]
            
        # If timex matches mm-dd-yyyy format
        if re.match(r'^(' + mm + '[/\.]\d{1,2}[/\.]\d{2,4})$', timex):
            #dmy = re.split(r'\s', timex)[0]
            dmy = re.split(r'/|-|\.', timex)
            dmy0, dmy1, dmy2 = int(dmy[0]), int(dmy[1]), normYear(int(dmy[2]))
            try:
                timex_val = str(dmy2) + '-' + normDM(dmy0) + '-' + normDM(dmy1)
                norm_val = datetime(dmy2, dmy0, dmy1).date()
                timex_format = 'MM/DD/YYYY'
            except(ValueError):
                exceptions.append([timex, timex_start, timex_end, 'MM/DD/YYYY'])
        
        # if timex matches longdate
        elif re.match("^(" + month + "( \d{1,2}| of)?.? \d{2,4})$", timex, re.IGNORECASE):
            dmy = re.split(",? *", timex)
            # month, year
            if len(dmy) == 2:
                try:
                    dmy0, dmy1 = dmy[0], normYear(int(dmy[1]))
                    norm_val = datetime(dmy1, hashmonths[dmy0.upper()], 1).date()
                    timex_val = str(dmy1) + '-' + normDM(dmy0) + '-XX'
                    timex_format = 'Month, YYYY'
                except(ValueError, KeyError):
                    exceptions.append([timex, timex_start, timex_end, 'Month, YYYY'])
            elif dmy[1] == 'of':
                try:
                    dmy0, dmy1 = dmy[0], normYear(int(dmy[2]))
                    norm_val = datetime(dmy1, hashmonths[dmy0.upper()], 1).date()
                    timex_val = str(dmy1) + '-' + normDM(dmy0) + '-XX'
                    timex_format = 'Month, YYYY'
                except(ValueError, KeyError):
                    exceptions.append([timex, timex_start, timex_end, 'Month, YYYY'])
            else:
                try:
                    dmy0, dmy1, dmy2 = dmy[0], int(dmy[1]), normYear(int(dmy[2]))
                    norm_val = datetime(dmy2, hashmonths[dmy0.upper()], dmy1).date()
                    timex_val = str(dmy2) + '-' + normDM(hashmonths[dmy0.upper()]) + '-' + normDM(dmy1)
                    timex_format = 'Month DD, YYYY'
                except(ValueError, KeyError):
                    exceptions.append([timex, timex_start, timex_end, 'Month DD, YYYY'])
        
        # if timex matches ##/## and mm within 12 and dd within 31, assume mm/dd. else interpret as mm/yyyy
        elif re.match("^(" + mm +"/([12][09])?\d{2})$", timex):
            dmy = re.split(r'/', timex)
            dmy0, dmy1 = int(dmy[0]), int(dmy[1])
            if dmy0 <= base_month and dmy1 <= 31:
                base_year = base_date.year
            elif base_month < dmy0 <= 12 and dmy1 <= 31:
                base_year = base_date.year - 1
            try:
                norm_val = datetime(base_year, dmy0, dmy1).date()
                timex_val = 'XXXX-' + normDM(dmy0) + '-' + normDM(dmy1)
                timex_format = 'MM/DD'
            except(ValueError):
                if dmy1 < 100:
                    timex_format = 'MM/YY'
                else:
                    timex_format = 'MM/YYYY'
                try:
                    dmy1 = normYear(dmy1)
                    norm_val = datetime(dmy1, dmy0, 1).date()
                    timex_val = str(dmy1) + '-' + normDM(dmy0) + '-XX'
                except(ValueError):
                    exceptions.append([timex, timex_start, timex_end, timex_format])
        
        # if timex matches 4 digit year
        elif re.match(r'^([12][09]\d{2})$', timex):
            dmy = normYear(int(timex))
            timex_val = str(dmy)+ '-XX-XX'
            norm_val = datetime(dmy, 1, 1).date()
            timex_format = 'YYYY'
            
        # long month
        elif re.match("^((january|february|march|april|may|june|july|august|september| \
          october|november|december)|(jan|feb|mar|apr|jun|jul|aug|sept|sep|nov|dec))$", timex, re.IGNORECASE):
            dmy = hashmonths[timex.upper()]
            if dmy <= base_month:
                base_year = base_date.year
            else:
                base_year = base_date.year - 1
            try:
                norm_val = datetime(base_year, dmy, 1).date()
                timex_val = 'XXXX-' + normDM(dmy) + '-XX'
                timex_format = 'Month'
            except(ValueError):
                    exceptions.append([timex, timex_start, timex_end, timex_format])
                
        # Relative dates
        elif re.match(r'tonight|tonite|today', timex, re.IGNORECASE):
            timex_val = str(base_date)
            norm_val = base_date
            timex_format = 'yest/today/tom'
        elif re.match(r'yesterday', timex, re.IGNORECASE):
            norm_val = (base_date + relativedelta(days=-1))
            timex_val = str(norm_val)
            timex_format = 'yest/today/tom'
        elif re.match(r'tomorrow', timex, re.IGNORECASE):
            norm_val = (base_date + relativedelta(days=+1))
            timex_val = str(norm_val)
            timex_format = 'yest/today/tom'
    ##
            
        # Weekday in the previous week.
        elif re.match(r'last ' + week_day, timex, re.IGNORECASE):
            day = hashweekdays[timex.split()[1].upper()]
            norm_val = base_date + relativedelta(weeks=-1, \
                            weekday=(day))
            timex_val = str(norm_val)
            timex_format = 'relative weekday'

        # Weekday in the current week.
        elif re.match(r'this ' + week_day, timex, re.IGNORECASE):
            day = hashweekdays[timex.split()[1].upper()]
            norm_val = base_date + relativedelta(weeks=0, \
                            weekday=(day))
            timex_val = str(norm_val)
            timex_format = 'relative weekday'

        # Weekday in the following week.
        elif re.match(r'next ' + week_day, timex, re.IGNORECASE):
            day = hashweekdays[timex.split()[1].upper()]
            norm_val = base_date + relativedelta(weeks=+1, \
                              weekday=(day))
            timex_val = str(norm_val)
            timex_format = 'relative weekday'

        # Last, this, next week.
        elif re.match(r'last week', timex, re.IGNORECASE):
            norm_val = base_date + relativedelta(weeks=(base_week -1), weekday=0)
            yr = norm_val.year
            week = norm_val.isocalendar()[1]
            timex_val = str(yr) + 'W' + str(week)
            timex_format = 'relative week'
        elif re.match(r'this week', timex, re.IGNORECASE):
            norm_val = base_date + relativedelta(weeks=base_week, weekday=0)
            yr = norm_val.year
            week = norm_val.isocalendar()[1]
            timex_val = str(yr) + 'W' + str(week)
            timex_format = 'relative week'
        elif re.match(r'next week', timex, re.IGNORECASE):
            norm_val = base_date + relativedelta(weeks=(base_week+1), weekday=0)
            yr = norm_val.year
            week = norm_val.isocalendar()[1]
            timex_val = str(yr) + 'W' + str(week)
            timex_format = 'relative week'

        # Month in the previous year.
        elif re.match(r'last ' + month, timex, re.IGNORECASE):
            try:
                mnth = hashmonths[timex.split()[1].upper()]
                timex_val = str(base_date.year - 1) + '-' + str(mnth) + '-XX'
                norm_val = datetime(base_date.year - 1, mnth, 1).date()
                timex_format = 'relative month'
            except(ValueError, KeyError):
                exceptions.append([timex, timex_start, timex_end, timex_format])

        # Month in the current year.
        elif re.match(r'this ' + month, timex, re.IGNORECASE):
            try:
                mnth = hashmonths[timex.split()[1].upper()]
                timex_val = str(base_date.year) + '-' + str(mnth) + '-XX'
                norm_val = datetime(base_date.year, mnth, 1).date()
                timex_format = 'relative month'
            except(ValueError, KeyError):
                exceptions.append([timex, timex_start, timex_end, timex_format])

        # Month in the following year.
        elif re.match(r'next ' + month, timex, re.IGNORECASE):
            try:
                mnth = hashmonths[timex.split()[1].upper()]
                timex_val = str(base_date.year + 1) + '-' + str(mnth) + '-XX'
                norm_val = datetime(base_date.year + 1, mnth, 1).date()
                timex_format = 'relative month'
            except(ValueError, KeyError):
                exceptions.append([timex, timex_start, timex_end, timex_format])
            
        elif re.match(r'last month', timex, re.IGNORECASE):

            # Handles the year boundary.
            if base_date.month == 1:
                timex_val = str(base_date.year - 1) + '-12-XX'
                norm_val = datetime(base_date.year - 1, 12, 1).date()
                timex_format = 'relative month'
            else:
                timex_val = str(base_date.year) + '-' + str(base_date.month - 1) + '-XX'
                norm_val = datetime(base_date.year, base_date.month - 1, 1).date()
                timex_format = 'relative month'
                
        elif re.match(r'this month', timex, re.IGNORECASE):
                timex_val = str(base_date.year) + '-' + str(base_date.month) + '-XX'
                norm_val = datetime(base_date.year, base_date.month, 1).date()
                timex_format = 'relative month'
                
        elif re.match(r'next month', timex, re.IGNORECASE):
            # Handles the year boundary.
            if base_date.month == 12:
                timex_val = str(base_date.year + 1) + '-01-XX'
                norm_val = datetime(base_date.year + 1, 1, 1).date()
                timex_format = 'relative month'
            else:
                timex_val = str(base_date.year) + '-' + str(base_date.month + 1) + '-XX'
                norm_val = datetime(base_date.year, base_date.month + 1, 1).date()
                timex_format = 'relative month'
                
        elif re.match(r'last year', timex, re.IGNORECASE):
            timex_val = str(base_date.year - 1) + '-XX-XX'
            norm_val = datetime(base_date.year -1, 1, 1).date()
            timex_format = 'relative year'
        elif re.match(r'this year', timex, re.IGNORECASE):
            timex_val = str(base_date.year) + '-XX-XX'
            norm_val = datetime(base_date.year, 1, 1).date()
            timex_format = 'relative year'
        elif re.match(r'next year', timex, re.IGNORECASE):
            timex_val = str(base_date.year + 1) + '-XX-XX'
            norm_val = datetime(base_date.year + 1, 1, 1).date()
            timex_format = 'relative year'    
  ##          
        
        elif re.match(r'\d+ days? (ago|earlier|before)', timex, re.IGNORECASE):

            # Calculate the offset by taking '\d+' part from the timex.
            offset = int(re.split(r'\s', timex)[0])
            norm_val = base_date + relativedelta(days=-offset)
            timex_val = str(norm_val)
            timex_format = 'relative days'
        elif re.match(r'\d+ days? (later|after)', timex, re.IGNORECASE):
            offset = int(re.split(r'\s', timex)[0])
            norm_val = base_date + relativedelta(days=+offset)
            timex_val = str(norm_val)
            timex_format = 'relative days'
        elif re.match(r'\d+ weeks? (ago|earlier|before)', timex, re.IGNORECASE):
            offset = int(re.split(r'\s', timex)[0])
            norm_val = base_date + relativedelta(weeks=-offset)
            yr = norm_val.year
            week = norm_val.isocalendar()[1]
            timex_val = str(yr) + 'W' + str(week)
            timex_format = 'relative weeks'
        elif re.match(r'\d+ weeks? (later|after)', timex, re.IGNORECASE):
            offset = int(re.split(r'\s', timex)[0])
            norm_val = base_date + relativedelta(weeks=+offset)
            yr = norm_val.year
            week = norm_val.isocalendar()[1]
            timex_val = str(yr) + 'W' + str(week)
            timex_format = 'relative weeks'
        elif re.match(r'\d+ months? (ago|earlier|before)', timex, re.IGNORECASE):
            extra = 0
            offset = int(re.split(r'\s', timex)[0])

            # Checks if subtracting the remainder of (offset / 12) to the base month
            # crosses the year boundary.
            if (base_date.month - offset % 12) < 1:
                extra = 1

            # Calculate new values for the year and the month.
            yr = base_date.year - offset // 12 - extra
            mnth = (base_date.month - offset % 12) % 12

            # Fix for the special case.
            if mnth == 0:
                mnth = 12
            norm_val = datetime(yr, mnth, 1).date()
            timex_val = str(yr) + '-' + normDM(mnth) + '-XX'
            timex_format = 'relative months'
        elif re.match(r'\d+ months? (later|after)', timex, re.IGNORECASE):
            extra = 0
            offset = int(re.split(r'\s', timex)[0])
            if (base_date.month + offset % 12) > 12:
                extra = 1
            yr = base_date.year + offset // 12 + extra
            mnth = (base_date.month + offset % 12) % 12
            if mnth == 0:
                mnth = 12
            norm_val = datetime(yr, mnth, 1).date()
            timex_val = str(yr) + '-' + normDM(mnth) + '-XX'
            timex_format = 'relative months'
        elif re.match(r'\d+ years? (ago|earlier|before)', timex, re.IGNORECASE):
            offset = int(re.split(r'\s', timex)[0])
            timex_val = str(base_date.year - offset) + '-XX-XX'
            norm_val = datetime(base_date.year - offset, 1, 1).date()
            timex_format = 'relative years'
        elif re.match(r'\d+ years? (later|after)', timex, re.IGNORECASE):
            offset = int(re.split(r'\s', timex)[0])
            timex_val = str(base_date.year + offset) + '-XX-XX'
            norm_val = datetime(base_date.year + offset, 1, 1).date()
            timex_format = 'relative years'
        elif re.match(r'in \d+ weeks?', timex, re.IGNORECASE):
            norm_val = base_date + relativedelta(weeks=+1)
            timex_val = str(norm_val)
            timex_format = 'relative weeks'
        elif re.match(r'in \d+ days?', timex, re.IGNORECASE):
            norm_val = base_date + relativedelta(days=+1)
            timex_val = str(norm_val)
            timex_format = 'relative days'
        elif re.match(r'in \d+ months?', timex, re.IGNORECASE):
            norm_val = base_date + relativedelta(months=+1)
            timex_val = str(norm_val)
            timex_format = 'relative months'
        
        
        timex_grounded.append([timex_ori, timex_start, timex_end, norm_val, timex_val, timex_format])
        
    return timex_grounded, exceptions
        
#%%
####

def demo():
    import nltk
    text = nltk.corpus.abc.raw('rural.txt')[:10000]
    print (tag(text))

if __name__ == '__main__':
    demo()