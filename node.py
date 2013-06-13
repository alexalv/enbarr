#!/usr/bin/python2

import pika
import json
import libvirt
import csv
from StringIO import StringIO

def answer(ch,message):
    ch.basic_publish(exchange='',
                      routing_key='mng.to.ui2',
                      body=json.dumps(message))


def reindex():
    files = []
    with open('images/index.info', 'rb') as csvfile:
        indexreader = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in indexreader:
            try:
                item = {}
                item['file'] = row[0]
                item['name'] = row[1]
                item['description'] = row[2]
                files.append(item)
            except:
                print "More lines then items or incorrect line!"
    return files



def switch_message(self, message):
    #convirt = libvirt.open("qemu:///system")
    try:
        if   message['action'] == "START"  :
            print " [yy] TBA.START"
        elif message['action'] == "STOP"   :
            print " [yy] TBA.STOP"
        elif message['action'] == "SAVE"   :
            print " [yy] TBA.SAVE"
        elif message['action'] == "DELETE" :
            print " [yy] TBA.DELETE"
        elif message['action'] == "INFO"   :
            print " [yy] TBA.INFO"
        elif message['action'] == "REINDEX":
            print " [yy] TBA.REINDEX"
            index = {}
            index['action'] = 'INDEX'
            index['items'] = reindex()
            return index
            
        else:
            print " [ERROR] wrong message"
    except KeyError:
        print " [ERROR] wrong message"


def callback(ch, method, properties, body):
    io = StringIO(body)
    message = json.load(io)
    answer(ch,switch_message(message))

connection = pika.BlockingConnection(pika.ConnectionParameters(host='217.197.0.19'))
channel = connection.channel()
channel.queue_declare(queue = 'ui.to.mng')
print " [*] Waiting for messages. To exit press CTRL+C"
channel.basic_consume(callback,
                      queue = 'ui.to.mng',
                      no_ack= True)
channel.start_consuming()