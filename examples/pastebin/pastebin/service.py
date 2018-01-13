import pickle as pickle
import os.path
import time
from zope.interface import implementer

from twisted.application import service
from twisted.python import log

from pastebin import interfaces
from pastebin import pasting


class Record(object):

    def __init__(self, oid, author, time):
        self.oid = oid
        self.author = author
        self.time = time
        self.version = 0


@implementer(interfaces.IPasteBin)
class FSPasteBinService(service.Service):


    def __init__(self, storageDir):
        self._dir = storageDir

    def getListOfPastings(self, limit=None):
        if limit is None:
            limited = self._index
        else:
            limited = self._index[0:limit]
        return [(r.oid, r.author, r.time) for r in limited]

    def _makeFilename(self, name):
        return os.path.join(self._dir, name)

    def _loadPastingData(self, oid):
        with open(self._makeFilename(str(oid)), 'rb') as f:
            return pickle.load(f)

    def _savePastingData(self, oid, data):
        with open(self._makeFilename(str(oid)), 'wb') as f:
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

    def getPasting(self, oid):
        data = self._loadPastingData(oid)
        return Pasting(data)

    def addPasting(self, author, text):
        oid = self._nextOid
        now = time.gmtime()
        data = [{'author':author, 'time':now, 'text':text}]
        self._savePastingData(oid, data)
        self._index.insert(0, Record(oid, author, now))
        self._nextOid += 1
        return oid

    def updatePasting(self, oid, author, text):
        now = time.gmtime()
        data = self._loadPastingData(oid)
        data.append({'author':author, 'time':now, 'text':text})
        self._savePastingData(oid, data)
        for i, r in enumerate(self._index):
            if r.oid == oid:
                r.time = now
                self._index.insert(0,self._index.pop(i))
        
    def startService(self):
        log.msg('Loading index')
        try:
            with open(self._makeFilename('index'), 'rb') as f:
                d = pickle.load(f)
            self._index = d['index']
            self._nextOid = d['nextOid']
        except IOError:
            self._index = []
            self._nextOid = 1

    def stopService(self):
        log.msg('Storing index')
        d = {'index':self._index, 'nextOid':self._nextOid}
        with open(self._makeFilename('index'), 'wb'):
            pickle.dump(d, f, pickle.HIGHEST_PROTOCOL)

@implementer(pasting.IPasting)
class Pasting(object):
    

    def __init__(self, data):
        self._data = data
    
    def getLatestVersion(self):
        return self.getVersion(-1)
    
    def getVersion(self, version):
        return Version(self._data[version])

    def getHistory(self):
        history = [(i,d['author'],d['time']) for i,d in enumerate(self._data)]
        history.reverse()
        return history
                              

@implementer(pasting.IVersion)
class Version:


    def __init__(self, data):
        self._data = data

    def getAuthor(self):
        return self._data['author']

    def getText(self):
        return self._data['text']

    def getTime(self):
        return self._data['time']
