from Adafruit_IO import MQTTClient
import sys
# from global_variable import tasks, sendDataTask
import uart
import Tasks

  
class QueueRequest:
  def __init__(self):
    self.queue = []
    self.isHandling = False
  def addRequest(self, feed_id, payload):
    data = f"{feed_id}:{payload}"
    self.queue.append(data)
  def handleRequest(self):
    if(self.isHandling == True):
      return
    if(len(self.queue) > 0):
      data = self.queue[0]
      
      uart.state = uart.State.INIT
      Tasks.sendDataTask = Tasks.Task(delay = 0, period = 1, duration = -1, func = uart.sendData, args = data)
      Tasks.tasks.add_task(Tasks.sendDataTask)
      self.isHandling = True

  def removeRequest(self):
    if(len(self.queue) > 0):
      self.queue.pop(0)
    self.isHandling = False
  def getFirstRequest(self):
    if(len(self.queue) > 0):
      return self.queue[0]
    return None
queueResquest = QueueRequest()

class mqtt_client:
  AIO_FEED_IDs = ['nutnhan1', 'nutnhan2']
  AIO_USERNAME = 'nguyentruongthan'
  AIO_KEY = 'aio_Lbnt49k6QFGB2m2X0u4vfPCSjn4z'
  
  def __init__(self):
    self.client = MQTTClient(self.AIO_USERNAME, self.AIO_KEY)
    self.client.on_connect = self.connected
    self.client.on_disconnect = self.disconnected
    self.client.on_message = self.message
    self.client.on_subscribe = self.subscribe

    self.client.connect()
    self.client.loop_background()

  
  def connected(self, client, ):
    print('Connected successful ...')
    for topic in self.AIO_FEED_IDs:
      client.subscribe(topic)

  def subscribe(self, client, userdata, mid, granted_qos):
    print('Subscribe successful ...')

  def disconnected(self, client):
    print('Disconnect ...')
    sys.exit(1)

  def message(self, client, feed_id, payload):
    print(f'From MQTT Subscribe: {payload}, feed id: {feed_id}')
    queueResquest.addRequest(feed_id, payload)
    

  def publish(self, feed_id, message):
    self.client.publish(feed_id, message)

client = mqtt_client()
