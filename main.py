### python server.py
### python main.py -n 20 -t 100

from Crypto.Hash import SHA3_256
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from abc import ABC, abstractmethod
from multiprocessing import Process, Value, Array
from flask import Flask, request
from flask_restful import Resource, Api
from threading import Thread
import queue
import asyncio
import subprocess
import os
import math
import time
import zmq
import re
import sys, getopt
import random
import requests
import json
import string

Server_URL = "http://127.0.0.1:2000"
nodes = []
info = []
info_server = []
x = []

def process_i(h_time,p_id,n,ell,r):

    sign_key = ECC.generate(curve='NIST P-256')
    verify_key = sign_key.public_key()
    signer = DSS.new(sign_key, 'fips-186-3')
    verifier = DSS.new(verify_key, 'fips-186-3')
    
    push_port = str(random.randint(5000, 6000))
    pushURL = "tcp://127.0.0.1:" + push_port

    SendToServer(p_id,push_port,verify_key)
    time.sleep(3)
    peerData,port = Get_FromServer()
    
    Ran = random.randrange(0, 2**40-1) 

    t = Thread(target=Push_Random, args=(h_time,Ran,p_id,push_port,pushURL,n,port,verify_key,signer))
    t.start()
    t.join(4*n)
    
    proposer = x[0]   
    if (p_id == proposer):                                                  # proposer call block creator
        block = createBlock(ell,r,p_id,signer)

##        for j in range(0, r):
##            block = ""
##            f = open('sample_block_'+str(p_id)+"_"+str(j)+'.log','rt')
##            block = f.readlines()                                           # read the block  
            #push_BlockToValidators()
            #waiteFor_receive_2K()

##    else :                                                                  # validator waits for block

        # wait for blocks in a while loop from proposer
        # while loop till get 2K verified Block
            # verified ?
                # sign it and write a file
                # push_to other peers
                # pull_from other validator

                
            
            

        
        
        

    
##  main.py -n 5 -t 100 -l 10 -r 5 

##  main.py -n 10 -t 100 -l 10 -r 5

##  main.py -n 20 -t 100 -l 10 -r 5
            
def Push_Random(h_time,R,p_id,push_port,pushURL,n,port,verify_key,signer):
    context = zmq.Context()    
    socket_push = context.socket(zmq.PUSH)    

    for i in range (1,3*n):                # push Random Number
        socket_push.connect(pushURL)        
        socket_push.send_json(R)
    print('Pushed Random Number on port: ',pushURL , ': ',R )
    time.sleep(n)
    rand_list=[]
    rand_list.append(R)
    
    for i in (port):                        # pull Random Number
        if (i != push_port):
            url = "tcp://127.0.0.1:"+str(i)
            context = zmq.Context()
            socket_pull = context.socket(zmq.PULL)
            while True:
                try:
                    socket_pull.bind(url)
                    break
                except:
                    time.sleep(2)
                    print('Connecting, please wait...') 
            rand = socket_pull.recv_json()
            socket_pull.close()
            rand_list.append(rand)
    x.append(proposerFinder(rand_list,h_time,n))

    print('\npeer ',p_id,' : ',rand_list,'proposer: ',x[0])


def proposerFinder(rand_list,h_time,n):
    Rx = 0
    for i in (rand_list):
        Rx = Rx ^ int(i)
        
    digest = SHA3_256.new(Rx.to_bytes(32, byteorder='big'))
    for i in range(int(h_time)-1):
        digest = SHA3_256.new(digest.digest())
    proposer = int.from_bytes(digest.digest(), "big")% int(n)
    return proposer
    

def WriteToLog(h_time,n,p_id,rand_list,verify_key,signer):

    Rx = 0  
    for i in (rand_list):
        Rx = Rx ^ int(i)        
    digest = SHA3_256.new(Rx.to_bytes(32, byteorder='big'))
    for i in range(int(h_time)-1):
        digest = SHA3_256.new(digest.digest())
    P_proser = int.from_bytes(digest.digest(), "big")% int(n) 
    print('Proser ID by peer ' ,p_id,' is :', P_proser)
    rand_list.sort()
    filename = "election_"+str(p_id)+".log"
    file1 = open(filename,"w")

    newlisttowrite = ''   
    for i in (rand_list):
        newlisttowrite = newlisttowrite+str(i)+'\n'
    file1.write(newlisttowrite)
    file1.write(str(P_proser)+"\n")
    file1.close()
    file1 = open(filename, "r")
    message = file1.readlines()
    message_str = [str(line) for line in message]
    h = SHA3_256.new("".join(message_str).encode('utf-8'))
    signature = signer.sign(h)
    file1.close()

    file1 = open(filename, "a")
    file1.write(str(int.from_bytes(signature,"big"))+"\n")
    file1.write(verify_key.export_key(format='OpenSSH'))
    file1.close()
    
    
## Each Peers send requset to server to register pID, PortNum And Pub_Key

def createBlock(ell,r,p_id,signer):
    h_prev = SHA3_256.new("".encode('utf-8'))   # set to hash of the empty string as it is the first block
    for j in range(0, r):
        block = ""
        for i in range(ell):
            tau = "".join([random.choice(string.ascii_letters + string.digits) for n in range(64)])  
            block += (tau + "\n")      # be careful with the new line character at the end of each line    
        h = SHA3_256.new(block.encode('utf-8')+h_prev.digest()) # hash value must be of "bytes" 
        signature = signer.sign(h)     # sign the hash of the block   
        h_prev = h                     # the current hash now becomes the previous hash for the next block 
        
        f = open('sample_block_'+str(p_id)+"_"+str(j)+'.log','wt')   # Open the file (see the naming convention for the log file)
        f.write(block)                                              # write the block first 
        signature = {'pid': p_id, 'signature': str(int.from_bytes(signature, "big"))}    
        f.write(json.dumps(signature))                              # use json to write the signature and peer id    
        f.close


def Get_FromServer():
    dataRecieved = requests.get((Server_URL + "/peer"))
    rec_data = dataRecieved.json()
    peer_info = []
    port_list = []
    for i in range(len(rec_data)):
        port_list.append(rec_data[i]['port'])
        
    for i in range(len(rec_data)):
        tmp = {"p_ID": rec_data[i]['p_id'], "port": rec_data[i]['port'], "publicKey": rec_data[i]['pub_key']}
        peer_info.append(tmp)
        
    return peer_info,port_list

    
def SendToServer(p_id , port , pub_key):
    peer_info = {"p_ID": str(p_id), "port": str(port), "publicKey": str(pub_key)}
    response = requests.post((Server_URL + "/peer"), json = (peer_info))
    if response.status_code == 201:
        print ('Peer_',p_id ,' Registration Succeeds')
    else:
        print ('Registration peer_',p_id ,' Failed!')
        
def getParam():
    script_name = str(sys.argv[0])
    peer = str(sys.argv[1])
    try:
        peer_num = int(sys.argv[2])
    except:
        peer_num = 0
    arg = sys.argv[3:]
    t = arg[0][:]
    try:
        h_time = int(arg[1][:])
        ell = int(arg[3][:])
        r = int(arg[5][:])
    except:
        h_time = 0
        ell = 0
        r = 0

    if ((peer=="-n") and (t =="-t") and (peer_num!=0) and (h_time!=0)and (ell!=0)and (r!=0)):
        
        return peer, peer_num, t, h_time,ell,r
    else:
        print('\nCommand pattern is not correct!'+
              '\nSample: "main.py -n 5 -t 100 -l 10 -r 5 "\n')

def start(h_time,n,ell,r):
    for i in range(0,n):
        p_id = random.randint(0,2**24-1)
        peer = Process(target = process_i , args= (h_time,i,n,ell,r))
        nodes.append(peer)
    for node in nodes :
        node.start()
    for item in nodes :
        item.join()
    
 
if __name__=='__main__':
    peer, peer_num, t, h_time,ell,r= getParam()
    print('\nParameters are Ok!\nPeer: ', peer_num,'\nhash time: ', h_time, '\nell:',ell,'\nround:',r)
##    proc = subprocess.Popen(["python" , "server.py"], stdout=subprocess.PIPE)
##      time.sleep(5)
    start(h_time,peer_num,ell,r)
