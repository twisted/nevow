
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
A toy email server.
"""
from zope.interface import implements

from twisted.internet import defer
from twisted.mail import smtp

from axiom.item import transacted

from axiomstore import Post
from iblogengine import IBlog


# You need to set this to your real SMTP_HOST
SMTP_HOST = 'localhost'
FROM = 'user@localhost'

__doc__ = """
This is the mail message format to post something via mail, no special
order is required, but all those fields must be present:
======
[Id: ID] 
Author: AUTHOR_NAME
Category: CATEGORY_NAME
Title: TITLE
Content: CONTENT
"""

class BlogMessageDelivery:
    implements(smtp.IMessageDelivery)
    def __init__(self, store):
        self.store = store
    
    def receivedHeader(self, helo, origin, recipients):
        return recipients
    
    def validateFrom(self, helo, origin):
        # All addresses are accepted
        return origin
    
    def validateTo(self, user):
        # Only messages directed to the "console" user are accepted.
        if user.dest.local == "blog":
            return lambda: BlogMessage(self.store)
        raise smtp.SMTPBadRcpt(user)

class BlogMessage:
    implements(smtp.IMessage)
    
    def __init__(self, store):
        self.lines = []
        self.store = store
    
    def lineReceived(self, line):
        self.lines.append(line)
    
    def eomReceived(self):
        post = {}
        isContent = False
        ctnt_buff = []
        recipients = self.lines[0]
        addrs = []

        for recipient in recipients:
            if '@' not in recipient.orig.addrstr:
                # Avoid answering to bounches
                if not recipient.orig.addrstr == '<>':
                    addrs.append(recipient.orig.addrstr[:-1]+'@'+recipient.orig.domain+'>')
            else:
                # Avoid answering to bounches
                if not recipient.orig.addrstr == '<#@[]>':
                    addrs.append(recipient.orig.addrstr)
            
        for line in self.lines[1:]:
            if not isContent:
                try:
                    field, value = line.split(':', 1)
                except ValueError:
                    continue
                if field.lower() != 'content':
                    post[field.lower()] = value.strip()
                else: 
                    isContent = True
                    ctnt_buff.append(value.strip())
            else:
                ctnt_buff.append(line.strip())
        post['content'] = '\n'.join(ctnt_buff)
        
        for header in 'content author category title'.split():
            if not post.has_key(header):
                self.lines = []
                return defer.fail(None) 
        if post.has_key('id'):
            oldpost = IBlog(self.store).getOne(int(post['id']))
            oldpost.author = unicode(post['author'])
            oldpost.title = unicode(post['title'])
            oldpost.category = unicode(post['category'])
            oldpost.content = unicode(post['content'])
            oldpost.setModified()
            action = 'modified'
            id = post['id']
        else:
            newid = IBlog(self.store).getNextId()
            newPost = Post(store=self.store,
                           id=newid,
                           author=unicode(post['author']),
                           title=unicode(post['title']),
                           category=unicode(post['category']),
                           content=unicode(post['content']))
            IBlog(self.store).addNewPost(newPost)
            action = 'added'
            id = newid
        self.lines = []
        msg = """From: <%s>
Subject: Successfull Post

Post number %s successfully %s
""" % (FROM, id, action)
        return self.sendNotify(addrs, msg)
    eomReceived = transacted(eomReceived)
    
    def toLog(self, what):
        print what
        
    def sendNotify(self, to_addr, msg):
        d = smtp.sendmail(SMTP_HOST, FROM, to_addr, msg)
        d.addCallback(self.toLog)
        d.addErrback(self.toLog)
        return d
    
    def connectionLost(self):
        # There was an error, throw away the stored lines
        self.lines = None

class BlogSMTPFactory(smtp.SMTPFactory):
    def __init__(self, store, *a, **kw):
        smtp.SMTPFactory.__init__(self, *a, **kw)
        self.delivery = BlogMessageDelivery(store)
    
    def buildProtocol(self, addr):
        p = smtp.SMTPFactory.buildProtocol(self, addr)
        p.delivery = self.delivery
        return p
