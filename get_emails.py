# -*- coding: utf-8 -*-

# This file is part of PyBOSSA.
#
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.

import logging
logger = logging.getLogger('get_emails')  # Get unnamed root logger.
import os
import sys
import mailbox
import email.Errors
from email.utils import parsedate_tz
from email.utils import mktime_tz
from email.utils import formatdate
from email.header import decode_header


ch = logging.StreamHandler()
logger.addHandler(ch)

DEBUG = ('--verbose' in sys.argv) or ('-v' in sys.argv)
if DEBUG:
    logger.setLevel(10)


#------------------------------------------------------------------------------
# Constants
#------------------------------------------------------------------------------
THISDIR = os.path.abspath(os.curdir)

# We create 'SyriaSpeakingGmail' part of path...
SYRIASPEAKINGGMAIL = os.path.join(THISDIR, '..', '..', 'SyriaSpeakingGmail')
if not os.path.exists(SYRIASPEAKINGGMAIL):
    logger.critical(
        "You must create %s and run offlineimap.py." % SYRIASPEAKINGGMAIL)

# ...but offlineimap.py creates 'INBOX' part of path.
INBOX = os.path.join(SYRIASPEAKINGGMAIL, 'INBOX')

# Save messages that have been sent to PyBossa.
PROCESSED_MESSAGES_DIR = os.path.join(SYRIASPEAKINGGMAIL, 'PYBOSSA')

# Save messages that have been sent to PyBossa.
PROBLEMS_MESSAGES_DIR = os.path.join(SYRIASPEAKINGGMAIL, 'PROBLEMS')

# http://ginstrom.com/scribbles/2007/11/19/parsing-multilingual-email-with-python/
def get_charset2(message, default="ascii"):
    """Get the message charset."""

    charset = message.get_content_charset()
    if not charset:
        charset = message.get_charset()

    if charset:
        if charset.find('"')>0:
            charset = charset[:charset.find('"')]
        return charset
    return default

def get_multilingual_header(header_text, default="ascii"):
    if not header_text is None:
        try:
            headers = header.decode_header(header_text)
        except HeaderParseError:
            return u"Error"

        try:
            header_sections = [
                unicode(text, charset if charset and charset!='unknown' 
                        else default, errors='replace') 
                for text, charset in headers]
        except LookupError:
            header_sections = [unicode(text, default, errors='replace') 
                               for text, charset in headers]

        return u"".join(header_sections)
    else:
        return None

def decode_email(raw_email):
    raw_email = raw_email.replace('\r', ' ').replace(
        '\n', ' ').replace(' ', ' ')
    if re.match('=\?.*?\?[QqBb]\?.*\?=$', raw_email):
        name, email = utils.parseaddr(get_multilingual_header(raw_email))
    else:
        name, email = utils.parseaddr(raw_email)
        name = get_multilingual_header(name)
        email = get_multilingual_header(email)

    decoded_email = utils.formataddr((name, email))
    return decoded_email


from email.Iterators import typed_subpart_iterator
def get_charset(message, default="ascii"):
    """Get the message charset"""

    if message.get_content_charset():
        return message.get_content_charset()

    if message.get_charset():
        return message.get_charset()

    return default

def get_body(message):
    """Get the body of the email message"""
    
    if message.is_multipart():
        #get the plain text version only
        text_parts = [part
                      for part in typed_subpart_iterator(message,
                                                         'text',
                                                         'plain')]
        body = []
        for part in text_parts:
            charset = get_charset(part, get_charset(message))
            body.append(unicode(part.get_payload(decode=True),
                                charset,
                                "replace"))

        return u"\n".join(body).strip()

    else: # if it is not multipart, the payload will be a string
          # representing the message body
        body = unicode(message.get_payload(decode=True),
                       get_charset(message),
                       "replace")
        return body.strip()



def get_multilingual_subject(message):
    return ''.join([unicode(t[0], t[1] or 'ascii') 
                    for t in decode_header(message['Subject'])])


def do_pybossa(message):

    logger.debug('FROM:  %s' % message['from'])
    logger.debug('SUBJECT:  %s' % get_multilingual_subject(message))
    logger.debug('DATE:  %s' % message['date'])

    ret = {'msgs_text': get_body(message),
           'msgs_html': [],
           'msg_subject': get_multilingual_subject(message),
           'msg_date': message['date']}

    return ret

def do_pybossa_trash(message):

    if message['from'].find('laith abdelali') < 0:
        return {}

    logger.debug('FROM:  %s' % message['from'])
    logger.debug('SUBJECT:  %s' % message['subject'])
    logger.debug('DATE:  %s' % message['date'])

    # Do not know a priori which email part contains actual payload.
    texts = []
    htmls = []

    # Email messages are multipart mime beasts. Even sub-parts of a
    # message could be multipart. So walk through each part and its
    # sub-parts and save all text/xxxx parts.
    for m in message.walk():

        content_type = m.get_content_type()
        logger.debug('CONTENT_TYPE:  %s' % content_type)

        #if content_type in ('multipart/alternative', 'multipart/related'):
        if content_type.find('multipart') > -1:
            continue

        if content_type in ('image/png'):
            continue
            
        if m.is_multipart():
            try:
                # Ryan debugging on his machine.
                from erpy.ipshell import ipshell
                ipshell('here')
            except:
                print 'Perhaps there is another multipart issue?'
            sys.exit()


        if 'Content-Transfer-Encoding' not in m.keys():
            if m.get_content_charset() not in ('iso-8859-1', 'utf-8'):

                logger.warning("Could have some encode/decode issues.")

                from erpy.ipshell import ipshell
                ipshell('here encode/decode!')

                continue

        # ORIGINAL:
        # payload = unicode(m.get_payload(decode=False))

        if m.get_content_charset() == 'windows-1256':
            logger.warning('Need to figure this out one day...')
            continue
            #payload = m.get_payload(decode=True)

        else:
            #payload = unicode(m.get_payload(decode=False))
            payload = m.get_payload(decode=False)

        # except UnicodeDecodeError:
        #     pass  # Maintain original.
        
        # unicode understanding!
        # http://www.youtube.com/watch?v=sgHbC6udIqc

        # print m.get_content_charset()
        logger.debug('PAYLOAD:  %s...' % payload[:30])

        print payload
        from erpy.ipshell import ipshell
        ipshell('here')

        

        if content_type == 'text/plain':
            texts.append(payload)

        elif content_type == 'text/html':
            htmls.append(payload)

    if DEBUG:
        print

    if len(texts) or len(htmls):
        # msgs_text and msgs_html are lists, hence 'msgs' not 'msg'.
        # msg_subject and msg_date are simple strings.
        ret = {'msgs_text': texts,
               'msgs_html': htmls,
               'msg_subject': message['subject'],
               'msg_date': message['date']}
    else:
        ret = {}

    return ret


def process_msg(key, inbox, pybossa, problems):

    try:
        message = inbox[key]
    except email.Errors.MessageParseError:
        # TODO:  Delete, move or process this somehow? Send note to admin?
        return  # The message is malformed. Just leave it.

    ret = do_pybossa(message)
    if len(ret) == 0:
        return None

    # Debugging.
    if inbox == pybossa:
        return ret

    try:
        # Write copy to disk before removing original.
        # If there's a crash, you might duplicate a message, but
        # that's better than losing a message completely.
        pybossa.lock()
        pybossa.add(message)
        pybossa.flush()

    # Not sure yet what errors might appear but I know that we want to
    # err on the conservative side and not delete anything from inbox
    # if there is an error.
    except Exception, err:

        # TODO: Should probably try to add these to problems maildir...

        logger.exception('Make specific exception 1.\n%s' % err.message)
        return None

    finally:
        pybossa.unlock()


    try:
        # Remove original message.  This only removes the message from
        # local INBOX dir not from the remote server.
        inbox.lock()
        inbox.discard(key)
        inbox.flush()

    except Exception, err:
        # TODO: Should probably check ret and all now.
        logger.exception('Make specific exception 2.\n%s' % err.message)

    finally:
        inbox.unlock()

    return ret


def get_emails():

    msgs = []

    try:
        inbox = mailbox.Maildir(INBOX, factory=None, create=False)
    except mailbox.NoSuchMailboxError:
        logger.critical("You must run 'offlineimap.py' to sync email.")
        return msgs

    pybossa = mailbox.Maildir(PROCESSED_MESSAGES_DIR, factory=None, create=True)
    problems = mailbox.Maildir(PROBLEMS_MESSAGES_DIR, factory=None, create=True)

    # If ever mbox is desired...
    # pybossa_mbox = mailbox.mbox(PROCESSED_MESSAGES_DIR + '_mbox', 
    #                             factory=None, create=True)
    # problems_mbox = mailbox.mbox(PROBLEMS_MESSAGES_DIR + '_mbox', 
    #                              factory=None, create=True)

    #
    # Uncomment to use existing messages.
    #
    ## inbox = pybossa

    # Sort by date, but must parse date header to actual time object.
    date_keys = []
    for key, msg in inbox.iteritems():
        # http://docs.python.org/2/library/email.util.html
        date_keys.append((mktime_tz(parsedate_tz(msg['date'])), key))

    for date_key in sorted(date_keys, key=lambda x: x[0]):
        ret = process_msg(date_key[1], inbox, pybossa, problems)
        if ret:
            msgs.append(ret)

    inbox.close()
    pybossa.close()
    problems.close()

    return msgs
