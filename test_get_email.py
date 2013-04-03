#!/usr/bin/env python
"""Scrape email for PyBossa project.

Based on http://docs.python.org/2/library/mailbox.html#examples.
"""


#------------------------------------------------------------------------------
# Authorship
#------------------------------------------------------------------------------
__author__ = ("Ryan Woodard",)
__email__ = ("rw@timehaven.org",)
__version__ = "0.0.1"


#------------------------------------------------------------------------------
# Logging--formatters, handlers, etc. added below in set_logging().
#------------------------------------------------------------------------------
import logging
logger = logging.getLogger()  # Get unnamed root logger.


#------------------------------------------------------------------------------
# Built-in modules
#------------------------------------------------------------------------------
import argparse
import os
import sys
import mailbox
import email.Errors
from email import message_from_file


#------------------------------------------------------------------------------
# Third party modules
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# Our modules
#------------------------------------------------------------------------------
from rw_io import default_parser
from rw_io import set_logging


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

DEBUG = False


#------------------------------------------------------------------------------
# Command line parsing and usage
#------------------------------------------------------------------------------
def process_command_line(argv):
    parser = default_parser(__doc__)
    args = parser.parse_args(argv)
    return args


#------------------------------------------------------------------------------
# Internal functions & classes
#------------------------------------------------------------------------------
def do_pybossa(message):

    logger.debug('SUBJECT:  %s' % message['subject'])
    logger.debug('DATE:  %s' % message['date'])

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

        payload = unicode(m.get_payload(decode=False))

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
               'subject': message['subject'],
               'date': message['date']}
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
        return

    return

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
        logger.exception('Make specific exception 1.\n%s' % err.message)
        return

    finally:
        pybossa.unlock()


    try:
        # Remove original message.  This only removes the message from
        # local INBOX dir not from the remote server.
        inbox.lock()
        inbox.discard(key)
        inbox.flush()

    except Exception, err:
        logger.exception('Make specific exception 2.\n%s' % err.message)
        return

    finally:
        inbox.unlock()
    

#------------------------------------------------------------------------------
# Main routine
#------------------------------------------------------------------------------
def main(args=None):

    # Useful if this function used as module, called from other function.
    if args is None:
        args = process_command_line(sys.argv[1:])

    try:
        inbox = mailbox.Maildir(INBOX, factory=None, create=False)
    except mailbox.NoSuchMailboxError:
        logger.critical("You must run 'offlineimap.py' to sync email.")
        return

    pybossa = mailbox.Maildir(PROCESSED_MESSAGES_DIR, factory=None, create=True)
    problems = mailbox.Maildir(PROBLEMS_MESSAGES_DIR, factory=None, create=True)

    # If ever mbox is desired...
    # pybossa_mbox = mailbox.mbox(PROCESSED_MESSAGES_DIR + '_mbox', 
    #                             factory=None, create=True)
    # problems_mbox = mailbox.mbox(PROBLEMS_MESSAGES_DIR + '_mbox', 
    #                              factory=None, create=True)

    logger.info('Processing %d messages.' % len(inbox))
    for key in inbox.iterkeys():
        process_msg(key, inbox, pybossa, problems)

    inbox.close()
    pybossa.close()
    problems.close()


#------------------------------------------------------------------------------
# Import or standalone test
#------------------------------------------------------------------------------
if __name__ == '__main__':
    args = process_command_line(sys.argv[1:])
    set_logging(args, logger)
    DEBUG = 'DEBUG' == logging.getLevelName(logger.level)
    main(args)
