#!/usr/bin/python2

import sys
import pika
import json
import libvirt
import csv
import socket
import time
import uuid
from StringIO import StringIO
from daemon import Daemon
from virtconf import Virtconf
import ConfigParser
import os
import shutil

class NodeDaemon(Daemon):

    def answer(self, ch, message):
        ch.basic_publish(exchange='',
                      routing_key=self.routing_key,
                      body=json.dumps(message))


    def reindex(self):
        files = []
        with open(self.img_path + '/index.info', 'rb') as csvfile:
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
        ans_msg = {}
        ans_msg['params'] = {}

        try:
            if   message['action'] == "START"  :
                user_img_path = self.img_path+"/users/"+message['params']['user_id']
                if not os.path.exists(user_img_path):
                    os.makedirs(user_img_path)
                image_name=str(time.time())+message['params']['image']
                shutil.copyfile(self.img_path+"/"+message['params']['image'],user_img_path+"/"+image_name)
                print " [yy] Startcopying"
                sys.stdout.flush()

                vc = Virtconf(memory = message['params']['memory'],
                              image = user_img_path+"/"+image_name,
                              user_id = message['params']['user_id'])
                confstr = vc.xml_string()
                uuid = vc.get_uuid()
                convirt = libvirt.open("qemu:///system")
                convirt.createXML(confstr)
                
                dom = convirt.lookupByUUIDString(uuid)
                
                
                ans_msg['action'] = 'STARTED'
                ans_msg['params']['uuid'] = uuid
                ans_msg['params']['server_uuid'] = self.uuid
                ans_msg['params']['id'] = dom.ID()
                ans_msg['params']['user_id'] = message['params']['user_id']
                ans_msg['params']['vm_id'] = message['params']['vm_id']
                
                convirt.close()
                return ans_msg

            elif message['action'] == "STOP"   :
                convirt = libvirt.open("qemu:///system")
                dom = convirt.lookupByUUIDString(message['params']['uuid'])
                dom.shutdown()

                ans_msg['action'] = 'STOPPED'
                ans_msg['params']['uuid'] = message['params']['uuid']

                convirt.close()
                return ans_msg

            elif message['action'] == "SAVE"   :
                convirt = libvirt.open("qemu:///system")
                dom = convirt.lookupByUUIDString(message['params']['uuid'])
                filename = self.img_path+"/users/"+message['params']['user_id']+'/'+message['params']['uuid']+str(time.time())
                dom.save(filename)

                ans_msg['action'] = 'SAVED'
                ans_msg['params']['uuid'] = message['params']['uuid']
                ans_msg['params']['filename'] = filename

                convirt.close()
                return ans_msg

            elif message['action'] == "SAVEDSTART" :
                convirt = libvirt.open("qemu:///system")
                convirt.restore(message['params']['filename'])
                dom = convirt.lookupByUUIDString(message['params']['uuid'])
                
                ans_msg['action'] = 'SAVESTARTED'
                ans_msg['params']['uuid'] = message['params']['uuid']

                convirt.close()
                return ans_msg
                
            elif message['action'] == "INFO"   :
                print " [yy] TBA.INFO"
                sys.stdout.flush()

            elif message['action'] == "REINDEX":
                print " [yy] REINDEX"
                sys.stdout.flush()
                
                ans_msg['action'] = 'INDEX'
                ans_msg['items'] = self.reindex()

                return ans_msg
                
            else:
                print " [ERROR] wrong message"
                sys.stdout.flush()
                
                ans_msg['action'] = 'ERROR'
                ans_msg['params']['cause'] = 'WRONG MESSAGE ACTION'
                ans_msg['params']['on_action'] =  message['action']

                return ans_msg
                
        except KeyError as e:
            print " [ERROR] wrong message", e
            sys.stdout.flush()
            
            ans_msg['action'] = 'ERROR'
            ans_msg['params']['cause'] ='WRONG MESSAGE NOTATION'

            return ans_msg

        except:
            print " [ERROR] unexpected error", sys.exc_info()[0]
            sys.stdout.flush()
            
            ans_msg['action'] = 'ERROR'
            ans_msg['params']['cause'] ='UNEXPECTED ERROR'
            ans_msg['params']['on_action'] =  message['action']

            return ans_msg


    def callback(self, ch, method, properties, body):
        io = StringIO(body)
        message = json.load(io)
        print " [yy] GOT message ", message
        sys.stdout.flush()
        payload = json.dumps(self.switch_message(message))
        ch.basic_publish(exchange='',
                        routing_key=properties.reply_to,
                        properties=pika.BasicProperties(correlation_id = \
                                                     properties.correlation_id),
                        body=payload)
        ch.basic_ack(delivery_tag = method.delivery_tag)

    def run(self):
        print " [yy] Stat running"
        sys.stdout.flush()
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbithost,port = self.rabbitport))
        channel = connection.channel()
        channel.queue_declare(queue = self.queue_name)
        channel.basic_consume(self.callback,
                              queue = self.queue_name)
        channel.start_consuming()

if __name__ == "__main__":
    if len(sys.argv) == 3:
        config = ConfigParser.ConfigParser()
        config.read(sys.argv[2])
        rhost = config.get('RabbitMQ', 'host')
        rport = int(config.get('RabbitMQ', 'port'))
        Nuuid = str(uuid.uuid4())

        

        daemon = NodeDaemon('/tmp/enbarr-node-daemon.pid',
                            stdout = "/home/aleks/1.txt",
                            stderr = "/home/aleks/2.txt",
                            queue_name = "mng.to.node."+Nuuid,
                            routing_key = "mng.to.node."+Nuuid,
                            img_path = config.get('Images', 'path'),
                            rabbithost=rhost,
                            rabbitport=rport,
                            node_uuid = Nuuid
                            )
    
        if 'start' == sys.argv[1]:
            startmsg = {}
            startmsg['action'] = 'NEWSERVER'
            startmsg['params'] = {}
            startmsg['params']['ip'] = socket.gethostbyname(socket.gethostname())
            startmsg['params']['uuid'] = Nuuid

            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rhost,port = rport))
            channel = connection.channel()
            channel.basic_publish(exchange='',
                          routing_key='common.node.to.mng',
                          body=json.dumps(startmsg))
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart /path/to/config" % sys.argv[0]
        sys.exit(2)