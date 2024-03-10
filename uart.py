import serial.tools.list_ports
from enum import Enum
import Tasks
import random
import MQTTClient
class State(Enum):
  INIT = 0
  SEND_HANDSHAKE = 1
  WAIT_HANDSHAKE = 2
  SEND_DATA = 3
  WAIT_RESPONSE = 4
  ERROR = 5
  FINISH = 6
state = State.INIT 
count_timeout_handshake = 3
keyHandShakeSend = 0
keyHandshakeRecv = 0
count_timeout_response = 3


class Header(Enum):
  HANDSHAKE = 1
  POST = 2

class Frame:
  
  def __init__(self, header, topic, content):
    self.header = int(header)
    self.topic = topic
    self.content = content
  def getMessage(self):
    return f"{self.header}:{self.topic}:{self.content}"

#init Serial Communication object
ser = serial.Serial(port = "COM7", baudrate=115200)

def processData(data, client):
    global state
    #parameter client is object of MQTT Client

    #replace charactor ! and # at start and end of data
    data = data[1:]
    data = data[:-1]
    #spilit data to array with spilt charactor is ":" 
    data_split = data.split(":")
    if(len(data_split) != 3):
      print("Error data format")
      return
    frame = Frame(data_split[0], data_split[1], data_split[2])

    
    if(frame.header == Header.HANDSHAKE.value):
      #handshake
      if ((int(frame.content) == keyHandshakeRecv)
          and (state == State.WAIT_HANDSHAKE) 
          and (frame.topic == MQTTClient.queueResquest.getFirstRequest().split(":")[0])):
        #key recv from device and topic correct 
        state = State.SEND_DATA
        Tasks.tasks.remove_task(Tasks.waitting_handshake_task)
        print("Handshake success")
      else:
        print("Error handshake")
    if(frame.header == Header.POST.value):
      if ((state == State.WAIT_RESPONSE) 
            and (frame.topic == MQTTClient.queueResquest.getFirstRequest().split(":")[0])):
        #topic recv from device correct 
        state = State.FINISH
        print("Receive response")
      else:
        print("Error response")



mess = ""

def readSerial(client):
    #	Get the number of bytes in the input buffer
    bytesToRead = ser.inWaiting()
    if (bytesToRead > 0):
        global mess
        #read all data in serial and assign to mess
        mess = mess + ser.read(bytesToRead).decode("UTF-8")
        #Format of data is "!<content>#" 
        while ("!" in mess) and ("#" in mess):
            print(f"From Serial: {mess}")
            start = mess.find("!")
            end = mess.find("#")
            processData(mess[start:end + 1], client)
            if (end == len(mess)):
                mess = ""
            else:
                mess = mess[end+1:]



def handle_wait_handshake_timeout():
  global state, count_timeout_handshake
  
  count_timeout_handshake -= 1
  if(count_timeout_handshake == 0):
    print("Timeout handshake 3 times, set state to ERROR")
    count_timeout_handshake = 3
    state = State.ERROR
  else:  
    state = State.SEND_HANDSHAKE

def handle_wait_response_timeout():
  global state, count_timeout_response
  count_timeout_response -= 1
  if(count_timeout_response == 0):
    print("Timeout response 3 times, set state to ERROR")
    count_timeout_response = 3
    state = State.ERROR
  else:  
    state = State.SEND_DATA

def sendData(data):
  global keyHandshakeRecv, keyHandShakeSend, state
  if(state == State.INIT):
    state = State.SEND_HANDSHAKE
    return
  elif(state == State.SEND_HANDSHAKE):
    #create random number for keyHandShakeSend
    random.seed()
    keyHandShakeSend = int(random.random()*255)
    #create Frame for handshake
    frame = Frame(
            header = Header.HANDSHAKE.value, 
            topic = data.split(":")[0], 
            content = keyHandShakeSend)
    
    #Caculate key of handshake which we will compare with response handshake from device
    keyHandshakeRecv = int(int(keyHandShakeSend)/16) + keyHandShakeSend%16
    print(f"keyHandShakeSend: {keyHandShakeSend}; keyHandshakeRecv: {keyHandshakeRecv}")

    dataHandshake = frame.getMessage()
    print(f"Write to Serial: {dataHandshake}")

    ser.write(dataHandshake.encode("UTF-8"))
    state = State.WAIT_HANDSHAKE

    #Create timeout
    Tasks.waitting_handshake_task = Tasks.Task(delay = 100, period = 100, duration = 0, func = handle_wait_handshake_timeout)
    Tasks.tasks.add_task(Tasks.waitting_handshake_task)
    return
  elif(state == State.WAIT_HANDSHAKE):
    pass
  elif(state == State.SEND_DATA):
    #TODO: send data here
    frame = Frame(
      header = Header.POST.value,
      topic = data.split(":")[0],
      content = data.split(":")[1]
    )
    data = frame.getMessage()
    print(f"To Serial: {data}")
    ser.write(data.encode("UTF-8"))
    state = State.WAIT_RESPONSE

    #Create timeout
    Tasks.waitting_response_task = Tasks.Task(delay = 100, period = 100, duration = 0, func = handle_wait_response_timeout)
    Tasks.tasks.add_task(Tasks.waitting_response_task)
    return
  elif(state == State.WAIT_RESPONSE):
    pass
  elif(state == State.ERROR):
    Tasks.tasks.remove_task(Tasks.sendDataTask)
    MQTTClient.queueResquest.removeRequest()
    print("SEND FAILD")
  elif(state == State.FINISH):
    Tasks.tasks.remove_task(Tasks.waitting_response_task)
    Tasks.tasks.remove_task(Tasks.sendDataTask)
    MQTTClient.queueResquest.removeRequest()
    print("SEND SUCCESS")
