import xml.etree.ElementTree as ET
import glob
import numpy as py
import pandas as pd
import parsedatetime
import re
from dateutil.parser import parse
from datetime import timedelta
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
stopwords = stopwords.words('english')
from nltk.tag import pos_tag
import spacy
from spacy import displacy
from collections import Counter
import en_core_web_sm
nlp = en_core_web_sm.load()

#%% extract and normalize dates manually tagged with MAE2
def handle_date_annotations(fn, dte):
    timexLst = []
    #fn = 'dateValidation/' + fid + '.txt.xml'
    fid = int(filename.replace('dateValidation/', '').replace('.txt.xml', '').replace('dateValidation2/', ''))
    pid = get_pid(fid)
    
    tree = ET.parse(fn)
    root = tree.getroot()
    
    for ann in root.iter('TIMEX3'):
        tid = ann.attrib['id']
        [spanStart, spanEnd] = [int(r) for r in ann.attrib['spans'].split('~')]
        fx = ann.attrib['functionInDocument']
        text = ann.attrib['text']
        fmat = ann.attrib['format']
        context = ann.attrib['context']
        section = ann.attrib.get('section').replace('\ufeff', '').replace('\\&', '\&').replace('HIstory', 'History') if ann.attrib.get('section') is not None else None
        value = parse(ann.attrib['value'])
        pastRef = ann.attrib.get('pastReference')
        relDir = ann.attrib.get('relativeDirection')
        repeat = ann.attrib.get('repeatedText')
        
        timexLst.append([fid, pid, tid, dte, spanStart, spanEnd, text, fx, fmat, value
                         , context, section, pastRef, relDir, repeat
                         ])
    return timexLst

#%%use parsedatetime to find dates in note, return list of extracted dates. if useSections is not None, limit note to spans of the specified sections
def parse_dates(fid, pid, dte, txt, useSections = None):
    #pid = df.loc[fid].patient_id
    #dte = df.loc[fid].contact_date
    #txt = df.loc[fid].note_text
    cal = parsedatetime.Calendar()
    
    sectsDf = sectionized_note_dict[fid]
    
    ext_dtes = []
    
    ext_obj = cal.nlp(txt, dte)
    
    if ext_obj is not None:
        for parsed_datetime, ptype, start, end, matched_text in ext_obj:
            
            sectSer = sectsDf[(sectsDf.sectionStart <= start) & (sectsDf.sectionEnd >= end)]
            if len(sectSer) == 0:
                section = 'None'
            else:
                section = sectSer.normSect.values[0]
            
            if (useSections is None or section in useSections ):
                if (ptype == 2):
                    reyear = re.compile('[1-2][0-9][0-9][0-9]')
                    for m in reyear.finditer(matched_text):
                        start = start + m.start()
                        end = start + m.end()
                        matched_text = m.group()
                        parsed_datetime = parse(matched_text + '-1-1').date()
                        
                        if parsed_datetime > dte.date():
                            future = 1
                        else:
                            future = 0
                        
                        if dte.date() + relativedelta(years=1) < parsed_datetime:
                            t_plus1 = 1
                        else:
                            t_plus1 = 0
                            
                        exactGold = isGoldDate(pid, parsed_datetime)
                        win30Gold = isGoldDate(pid, parsed_datetime, 30)
                        
                        #ext_dtes.append([fid, pid, dte.date(), ptype, start, end, matched_text, parsed_datetime, future, t_plus1])
                        ext_dtes.append([fid, pid, dte.date(), ptype, start, end, matched_text, parsed_datetime
                                         , future, t_plus1, parsed_datetime.year, parsed_datetime.month, parsed_datetime.day
                                         , section, exactGold, win30Gold])
                        
                if (ptype == 1 or ptype == 3):
                    parsed_datetime = parsed_datetime.date()
                    if parsed_datetime > dte.date():
                        future = 1
                    else:
                        future = 0
                    
                    if dte.date() + relativedelta(years=1) < parsed_datetime:
                        t_plus1 = 1
                    else:
                        t_plus1 = 0
                        
                    exactGold = isGoldDate(pid, parsed_datetime)
                    win30Gold = isGoldDate(pid, parsed_datetime, 30)
                    
                    #ext_dtes.append([fid, pid, dte.date(), ptype, start, end, matched_text, parsed_datetime, future, t_plus1])
                    ext_dtes.append([fid, pid, dte.date(), ptype, start, end, matched_text, parsed_datetime
                                     , future, t_plus1, parsed_datetime.year, parsed_datetime.month, parsed_datetime.day
                                     , section, exactGold, win30Gold])
                
    return ext_dtes

#%% use spacy to find dates in note, return list of extracted dates. if useSections is not None, limit note to spans of the specified sections
def parse_dates_spacy(fid, pid, dte, txt, useSections = None):

    ext_dtes = []
    cal = parsedatetime.Calendar()
    doc = spacy.nlp(txt)
    
    sectsDf = sectionized_note_dict[fid]
    
    for ent in doc.ents:
        
        if ent.label_ == 'DATE':
            #print(ent.start_char, ent.text)
            
            matched_text = ent.text
            start = ent.start_char
            end = ent.end_char
            
            sectSer = sectsDf[(sectsDf.sectionStart <= start) & (sectsDf.sectionEnd >= end)]
            if len(sectSer) == 0:
                section = 'None'
            else:
                section = sectSer.normSect.values[0]
            
            if (useSections is None or section in useSections ):
                if len(ent.text) = 4 and int(ent.text) < 1900:
                    continue
                try:
                    parsed_datetime = parse(ent.text, default=datetime(2019, 1, 1, 0, 0)).date()
                    ptype = 'dateutil'
                except (ValueError, OverflowError):
                    ext_obj = cal.nlp(ent.text, dte)
                    if ext_obj is None or ext_obj == ():
                        continue
                    parsed_datetime = ext_obj[0][0].date()
                    ptype = 'parsedatetime'
                    
                if parsed_datetime > dte.date():
                    future = 1
                else:
                    future = 0
                
                if dte.date() + relativedelta(years=1) < parsed_datetime:
                    t_plus1 = 1
                else:
                    t_plus1 = 0
                    
                exactGold = isGoldDate(pid, parsed_datetime)
                win30Gold = isGoldDate(pid, parsed_datetime, 30)
    
                ext_dtes.append([fid, pid, dte.date(), ptype, start, end, matched_text, parsed_datetime
                                 , future, t_plus1, parsed_datetime.year, parsed_datetime.month, parsed_datetime.day
                                 , section, exactGold, win30Gold])

    return ext_dtes

#%% use timex.py derived regex functions, return list of extracted dates. if useSections is not None, limit note to spans of the specified sections
def parse_dates_regex(fid, pid, dte, txt, useSections = None):
    ext_dtes = []
    sectsDf = sectionized_note_dict[fid]
    ext_obj, exceptions = groundList(tag(txt)[1], dte.date())
    
    for [text, start, end, parsed_datetime, specificity, fmat] in ext_obj:
        sectSer = sectsDf[(sectsDf.sectionStart <= start) & (sectsDf.sectionEnd >= end)]
        if len(sectSer) ==0:
            section = 'None'
        else:
            section = sectSer.normSect.values[0]
        
        if(useSections is None or section in useSections):
            if isinstance(parsed_datetime, str):
                pass
            else:
                if parsed_datetime > dte.date():
                    future = 1
                else:
                    future = 0
                
                if dte.date() + relativedelta(years=1) < parsed_datetime:
                    t_plus1 = 1
                else:
                    t_plus1 = 0
                
                exactGold = isGoldDate(pid, parsed_datetime)
                win30Gold = isGoldDate(pid, parsed_datetime, 30)
                
                ext_dtes.append([fid, pid, dte.date(), fmat, start, end, text, parsed_datetime \
                                 , future, t_plus1, parsed_datetime.year, parsed_datetime.month, parsed_datetime.day \
                                 , section, exactGold, win30Gold])
    return ext_dtes, exceptions
 


#%% return all manually annotated dates identified by extractors, by overlapping character spans, with delta
def find_match_rows(fid, source, target):
    matches = []
    target = target[target.fid==fid]
    source = source[source.fid==fid]
    if source.shape[0] ==0:
        pass
    for i, r in source.iterrows():
        sStart = r.start
        sEnd = r.end
        sVal = r.ann_date.to_pydatetime().date()
        sSect = r.normSect
        sFmat = r.format
        sText = r.text
        for j, k in target.iterrows():
            tStart = k.start
            tEnd = k.end
            tVal = k.parsed_datetime
            if (sStart <= tStart <= sEnd or tStart <= sStart <=tEnd) and sVal == tVal:
                matches.append([fid, i, sSect, sFmat, sText, sStart, sEnd, sVal, tStart, tEnd, 1, 0])
            elif (sStart <= tStart <= sEnd or tStart <=sStart <=tEnd) and sVal != tVal:
                matches.append([fid, i, sSect, sFmat, sText, sStart, sEnd, sVal, tStart, tEnd, 0, (sVal - tVal).days])
    return matches

#%% calculate summary identification and interpretation scores for extracted dates compared to annotations
def match_summary(fidList, source, target):
    matchList = []
    summary = {}
    for fid in fidList:
        match = find_match_rows(fid, source, target)
        matchList.extend(match)
    match = pd.DataFrame(matchList, columns = ['fid', 'annIndex', 'annSect', 'annFmat', 'annText' \
                                               , 'annStart', 'annEnd', 'annVal' \
                                               , 'extStart', 'extEnd', 'valMatch', 'delta'])
    summary['fid span found'] = len(match.fid.unique())
    summary['ADD span found'] = len(match.annIndex.unique())
    summary['fid value found'] = len(match[match.valMatch == 1].fid.unique())
    summary['ADD value found'] = len(match[match.valMatch == 1].annIndex.unique())
    summary['avg delta'] = match.delta.mean()
    summary['stdev delta'] = match.delta.std()
    summary['median delta'] = match.delta.median()
    return summary, match



    