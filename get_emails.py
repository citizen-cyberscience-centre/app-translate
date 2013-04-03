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

if 0:
    DEBUG = True
    logger.setLevel(10)
else:
    DEBUG = False

#------------------------------------------------------------------------------
# Constants
#------------------------------------------------------------------------------
THISDIR = os.path.abspath(os.curdir)

# We create 'SyriaSpeakingGmail' part of path...
SYRIASPEAKINGGMAIL = os.path.join(THISDIR, 'SyriaSpeakingGmail')
if not os.path.exists(SYRIASPEAKINGGMAIL):
    os.makedirs(SYRIASPEAKINGGMAIL)

# ...but offlineimap.py creates 'INBOX' part of path.
INBOX = os.path.join(SYRIASPEAKINGGMAIL, 'INBOX')

# Save messages that have been sent to PyBossa.
PROCESSED_MESSAGES_DIR = os.path.join(SYRIASPEAKINGGMAIL, 'PYBOSSA')

# Save messages that have been sent to PyBossa.
PROBLEMS_MESSAGES_DIR = os.path.join(SYRIASPEAKINGGMAIL, 'PROBLEMS')


def do_pybossa(message):

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

        if content_type == 'multipart/alternative':
            continue
            
        assert not m.is_multipart()
        
        payload = m.get_payload(decode=True)
        logger.debug('PAYLOAD:  %s...' % payload[:30])

        if content_type == 'text/plain':
            texts.append(payload)

        elif content_type == 'text/html':
            htmls.append(payload)

    if DEBUG:
        print

    if len(texts) or len(htmls):
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

    for key in inbox.iterkeys():
        ret = process_msg(key, inbox, pybossa, problems)
        if ret:
            msgs.append(ret)

    inbox.close()
    pybossa.close()
    problems.close()

    return msgs
