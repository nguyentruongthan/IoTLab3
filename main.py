import time
import Tasks


if __name__ == "__main__":
  time.sleep(3)
  Tasks.tasks.add_task(Tasks.read_uart_task)
  Tasks.tasks.add_task(Tasks.handleQueueRequestTask)
  while 1:
    Tasks.tasks.update()
    Tasks.tasks.dispatch()

    time.sleep(0.1) #time unit is 100ms

    