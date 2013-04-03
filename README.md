PyBossa application for translating messages
============================================

The application allows you to translate messages from one language to another
one.

The application comes with an e-mail parser that will download the messages
sent to a given e-mail account and parse the content to create a task in
PyBossa.

This application has three files:

*  createTasks.py: for creating the application in PyBossa, and fill it with some tasks.
*  template.html: the view for every task and deal with the data of the answers.

Testing the application
=======================

You need to install the pybossa-client first (use a virtualenv):

```bash
    $ pip install pybossa-client
```
Then, you can follow the next steps:

*  Create an account in PyBossa
*  Copy under your account profile your API-KEY
*  Run python createTasks.py -u http://crowdcrafting.org -k API-KEY
*  Open with your browser the Applications section and choose the FlickrPerson app. This will open the presenter for this demo application.

Please, check the full documentation here:

http://docs.pybossa.com/en/latest/user/create-application-tutorial.html

[Photo/Icon by Brett Wienstein](http://www.flickr.com/photos/nrbelex/454711486/)
[Photo License](http://creativecommons.org/licenses/by-sa/2.0/deed.en)
