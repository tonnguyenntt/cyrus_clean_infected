#!/usr/bin/env python3
# -*- coding: utf-8 -*-  

import getpass, sys, pprint, logging, os, re
from imapclient import IMAPClient

#logging.basicConfig(
#    format='%(asctime)s - %(levelname)s: %(message)s',
#    level=logging.DEBUG
#)

def check_input():
  try:
    imapHost, imapUsername, infectedList = sys.argv[1:]
  except ValueError:
    print ('Usage: %s HOST USERNAME INPUTFILE' % sys.argv[0])
    sys.exit(2)
  return [imapHost, imapUsername, infectedList]


def proceed_inputlist(inputFile):
  if not os.path.exists(inputFile):
    print('File does not exist')
    sys.exit(1)
  fileObj = open(inputFile,"r")
  inputList = []
  for line in fileObj:
   mailBox = re.sub('\/var\/spool\/imap','Shared Folders', re.search('(^.*)(\/)', line).group(1)) 
   msgUid = re.search('(^.*/)([0-9].*)\.:\ ', line).group(2)
   inputList.append([mailBox, msgUid])
  return inputList


def connect_imap(imapHost, imapUsername):
  imapObj = IMAPClient(imapHost, use_uid=True, ssl=True)
  try:
    imapObj.login(imapUsername, getpass.getpass())
    print("Connecting to mailbox via IMAP...")
    return imapObj
  except imapObj.Error:
    print("Login failed!!!")
    sys.exit(1)


def disconnect_imap(imapObj):
  print("Closing connection & logging out...")
  imapObj.logout()
  print("Connection closed!")
  return


def check_message(imapObj,mailBox,msgUid):
  if imapObj.folder_exists(mailBox):
    imapFolder = imapObj.select_folder(mailBox)
    if msgUid in imapObj.search():
      for msgUid, msgData in imapObj.fetch(msgUid, ['ENVELOPE']).items():
        msgEnvelope = msgData[b'ENVELOPE']
        imapStatus = "'" + msgEnvelope.subject.decode() + "'" + " received " + str(msgEnvelope.date)
    else:
      imapStatus = "Message does not exist"
  else:
    imapStatus = "Mailbox does not exist"
  imapObj.close_folder()
  return imapStatus


def delete_message(imapObj,mailBox,msgUid):
  imapObj.select_folder(mailBox, readonly=False)
  imapObj.delete_messages(msgUid)
  imapObj.close_folder()

  imapObj.select_folder(mailBox)
  if msgUid not in imapObj.search():
    delResult = "DELETED"
  else:
    delResult ="FAILED"
  imapObj.close_folder()
  return delResult


def proceed_delete(imapObj,mailBox,msgUid):
  msgStatus=check_message(imapObj, mailBox, msgUid)
  if msgStatus != "Message does not exist" and msgStatus != "Mailbox does not exist":
    delResponse=delete_message(imapObj, mailBox, msgUid)
  else:
    delResponse="-"
  return [msgStatus, delResponse]; 


if __name__ == '__main__':
  inputArray = check_input()
  affectedList = proceed_inputlist(inputArray[2])
  imapObj = connect_imap(inputArray[0], inputArray[1])
  for affectedRecord in affectedList:
    mailBox = affectedRecord[0]
    msgUid = int(affectedRecord[1])
    delRes = proceed_delete(imapObj,mailBox,msgUid)
    print('%s|%d.|%s|%s' % (mailBox, msgUid, delRes[0], delRes[1]))
#  imapObj = connect_imap(inputObj[0], inputObj[1])
#  mailBox = 'Sent'
#  msgUid = 7
#  delRes = proceed_delete(imapObj,mailBox,msgUid)
#  print('%s/%d.|%s|%s' % (mailBox, msgUid, delRes[0], delRes[1]))
#  disconnect_imap(imapObj)
