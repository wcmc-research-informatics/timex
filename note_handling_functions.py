import xml.etree.ElementTree as ET
import glob
import numpy as py
import pandas as pd
import parsedatetime
import re

#%% check prevalence of section keywords in notes
def noteSectionPresence(notes, sectionHeaders):
    n = len(notes)
    p = 0
    l = 0
    progressCnt = 0
    pathCnt = 0
    
    for i, t in notes.iterrows():
        m = 0
        shCount = len(sectionHeaders)
        
        for sh in sectionHeaders:
            if re.search(sh, t.note_text) is not None:
                m += 1
        if m == shCount:
            p += 1
            l = l + len(t.note_text)
            if t.note_type == 'PROGRESS NOTE':
                progressCnt += 1
            else:
                pathCnt += 1
    return [p, n, p/n, l/p, progressCnt, pathCnt]



#%% map section keywords to groups
sectionDict = {
'Allergies' : 'Allergies' ,
'AP:' : 'A&P' ,
'Assessment \& Plan' : 'A&P' ,
'Assessment \&amp; Plan' : 'A&P' ,
'Assessment & Plan' : 'A&P' ,
'Assessment and Plan' : 'A&P' ,
'Assessment:' : 'A&P' ,
'Chief Complaint' : 'Chief Complaint' ,
'ChronicMedical Problems:' : 'Problem List' ,
'CLINICAL INFORMATION:' : 'Clinical Information' ,
'COMMENTS:'  : 'Comments' ,
'Current Medications' : 'Medications' ,
'Current Medications:' : 'Medications' ,
'Data Review' : 'Data Review' ,
'Diagnosis Date'  : 'Diagnosis Date' ,
'Diagnosis:' : 'Diagnosis' ,
'DIAGNOSIS:' : 'Diagnosis' ,
'Electronic signature' : 'Signature' ,
'Electronically Signed' : 'Signature' ,
'Family History' : 'Family History' ,
'FAMILY HISTORY:' : 'Family History' ,
'GROSS DESCRIPTION:'  : 'Gross Description' ,
'Habits:' : 'Other' ,
'History of Present Illness' : 'HPI' ,
'History:' : 'HPI' ,
'HPI:' : 'HPI' ,
'ICD9 Codes:' : 'Coding' ,
'Imaging:' : 'Data Review' ,
'Impression:' : 'Impression' ,
'INTERPRETATION:' : 'Interpretation' ,
'Interval History' : 'HPI' ,
'Interval History' : 'HPI' ,
'Lab Result(s)' : 'Data Review' ,
'Lab Results()' : 'Data Review' ,
'LABORATORY' : 'Data Review' ,
'Medications  Name' : 'Medications' ,
'Medications \(' : 'Medications' ,
'Medications:' : 'Medications' ,
'Mental Status Exam' : 'Physical Exam' ,
'METHODS:' : 'Pathology' ,
'MICROSCOPIC DESCRIPTION:' : 'Pathology' ,
'Nursing Note' : 'Nursing Note' ,
'Other Modalities:' : 'Data Review' ,
'Past Medical History' : 'PMH' ,
'PAST MEDICAL HISTORY:' : 'PMH' ,
'Past Medical/Surgical History' : 'PMH' ,
'Past Psychiatric History:' : 'PMH' ,
'Past Surgical History' : 'PMH' ,
'PATHOLOGY' : 'Pathology' ,
'Patient Active Problem List' : 'Problem List' ,
'Physical Exam' : 'Physical Exam' ,
'PHYSICAL EXAM:' : 'Physical Exam' ,
'Plan ' : 'A&P' ,
'PLAN:' : 'A&P' ,
'Plan:' : 'A&P' ,
'PMH:' : 'PMH' ,
'PMHx:' : 'PMH' ,
'prescriptions:' : 'Medications' ,
'Procedure:' : 'Procedure' ,
'RADIOLOGY' : 'Data Review' ,
'Review of Systems' : 'Physical Exam' ,
'REVIEW OF SYSTEMS' : 'Physical Exam' ,
'SNOMED:' : 'SNOMED' ,
'Social History' : 'Social History' ,
'Social/Personal History:' : 'Social History' ,
'SPECIMEN:' : 'Pathology' ,
'Visit Notes' : 'Other' ,
'Vitals' : 'Physical Exam',
None : 'None'
}


#%% given list of section keywords to tag in notes, create sectionized_note_dict with indices of all sections in each note
def noteSectionIndsToDict(fidList, sectionHeaders):
    #sects = []
    sectDict = {}
    for fid in fidList:
        sects = []
        note_text = notes.loc[fid, 'note_text']
        #dte = dte.date()
        #print(fid, pid)
        for sh in sectionHeaders:
            pattern = re.compile(sh)
            
            for match in pattern.finditer(note_text):
                sects.append([sh, sectionDict[sh], match.start()])
                #print(fid, pid, dte, sh, match.start())
        sects = pd.DataFrame(sects, columns=['section', 'normSect', 'sectionStart'])
                    
        sects = sects.sort_values(['sectionStart'])
        
        sects['sectionEnd'] = sects.sectionStart.shift(-1) - 1

    
        for i, r in sects[sects.sectionEnd.isna()].iterrows():
             sects.loc[i, 'sectionEnd'] = len(notes.loc[fid].note_text)
        
        sectDict[fid] = sects

    return sectDict


#%%
# for note text passed in, create generator/list of ordered word tokens and spans
def getTokensSpans(txt, exclStopwords = False, exclPunct = True, stemToken = True):
    tokens = nltk.word_tokenize(txt)
    stemmer = nltk.stem.porter.PorterStemmer()
    offset = 0
    for token in tokens:
        offset = txt.find(token, offset)
        if exclPunct:
            if re.match('^\W$', token) is None:
                if exclStopwords:
                    if token.lower() not in stopwords:
                        if stemToken:
                            yield stemmer.stem(token), offset, offset + len(token)
                        else:
                            yield token, offset, offset + len(token)
                else:
                    if stemToken:
                        yield stemmer.stem(token), offset, offset + len(token)
                    else:
                        yield token, offset, offset + len(token)
        else:
            if exclStopwords:
                if token.lower() not in stopwords:
                    if stemToken:
                        yield stemmer.stem(token), offset, offset + len(token)
                    else:
                        yield token, offset, offset + len(token)
            else:
                if stemToken:
                    yield stemmer.stem(token), offset, offset + len(token)
                else:
                    yield token, offset, offset + len(token)
        offset += len(token)
#https://stackoverflow.com/questions/31668493/get-indices-of-original-text-from-nltk-word-tokenize


#%% retrieve tokens +/-wsize from each extracted date 
def getTextWindowFromDf(tokenList, start, end, wsize):
    windowTokens = []
    startToken = None
    endToken = None
    startInd = None
    
    dictEnd = tokenList[-1][2]
    if start > dictEnd:
        return []
    else:
        for i, token in enumerate(tokenList):
            tokenString, tokenStart, tokenEnd = token
            if tokenStart <= start <= tokenEnd:
                #assert not startToken
                startToken = token
                startInd = i
            if tokenStart > start and startToken is None:
                if i == 0:
                    startToken = token
                    startInd = i
                else:
                    _, prevStart, prevEnd = tokenList[i - 1]
                    if start - prevEnd <= tokenStart - start:
                        startToken = tokenList[i - 1]
                        startInd = i - 1
                    else:
                        startToken = token
                        startInd = i
            
        endInd = min(len(tokenList)-1, startInd + 3)
        endToken = tokenList[endInd]
        endFlag = None
        for i, token in enumerate(tokenList[startInd:endInd]):
            tokenString, tokenStart, tokenEnd = token
            if tokenStart <= end <= tokenEnd:
                endToken = token
                endInd = startInd + i
                endFlag = 1
            if tokenStart > end and endFlag is None:
                _, prevStart, prevEnd = tokenList[i - 1]
                if start - prevEnd <= tokenStart - start:
                    endToken = tokenList[i - 1]
                    endInd = startInd + i - 1
                    endFlag = 1
                else:
                    endToken = token
                    endInd = startInd + i
                    endFlag = 1

        wind = []
        windStart = max(0, startInd - wsize)
        windEnd = min(len(tokenList), endInd + wsize + 1)
        for token, tokenStart, tokenEnd in tokenList[windStart:windEnd]:
            wind.append(token)
        
        return wind

#%% retrieve df of tokens +/-wsize from each extracted date in all notes in a set as string
def buildCorpus(fidLst, tokenDict, extDates, wsize, label='win30Gold'):
    corpus = []
    for i, f in enumerate(fidLst):
        #print('file',f)
        df = tokenDict[f]
        for i, r in extDates[extDates.fid==f].iterrows():
            windLst = getTextWindowFromDf(df, r.start, r.end, wsize)
            if len(windLst) > 0:
                windStr = ''.join(x + ' ' for x in windLst)
#                corpus.append([f, r.pid, i, r.parsed_datetime, windStr, r.win30Gold])
                if label=='win30Gold':
                    corpus.append([f, r.pid, i, r.parsed_datetime, windStr, r.win30Gold])
#                    df = pd.DataFrame(corpus, columns=['fid', 'pid', 'extInd', 'parsed_datetime', 'windStr', 'win30Gold'])
                elif label=='exactGold':
                    corpus.append([f, r.pid, i, r.parsed_datetime, windStr, r.exactGold])
#                    df = pd.DataFrame(corpus, columns=['fid', 'pid', 'extInd', 'parsed_datetime', 'windStr', 'exactGold'])
    #return df
    return pd.DataFrame(corpus, columns=['fid', 'pid', 'extInd', 'parsed_datetime', 'windStr', label])
