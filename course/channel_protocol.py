import numpy as np
import enum
import time
from threading import Thread



class MessageStatus(enum.Enum):
    OK = enum.auto()
    LOST = enum.auto()


class Message:
    def __init__(self):
        self.data = ""
        self.status = MessageStatus.OK
        pass

    def copy(self):
        msg = Message()
        msg.data = self.data
        msg.status = self.status
        return msg

    def __str__(self):
        return f"({self.status}, {self.data})"


class MsgQueue:

    def __init__(self, loss_probability=0.3):
        self.msg_queue = []
        self.loss_probability = loss_probability
        pass

    def has_msg(self):
        if len(self.msg_queue) <= 0:
            return False
        else:
            return True

    def get_message(self):
        if self.has_msg():
            result = self.msg_queue[0]
            self.msg_queue.pop(0)
            return result
        else:
            return None

    def send_message(self, msg):
        tmp_msg = self.emulating_channel_problems(msg.copy())
        if tmp_msg.status == MessageStatus.LOST:
            self.msg_queue.append(tmp_msg)
            return
        self.msg_queue.append(tmp_msg)

    def emulating_channel_problems(self, msg):
        val = np.random.rand()
        if val <= self.loss_probability:
            msg.status = MessageStatus.LOST
            # print("Lost\n", end="")

        return msg


# подтверждения не теряются (дабы не создавалось дублирование и зависания)
class MsgPipe:
    def __init__(self):
        self.msg_queue = MsgQueue()
        self.ack_queue = MsgQueue()
        self.message_to_send = []

        self.window = 1  # всегда
        self.timeout = 1

        self.stop_flag = False
        self.loss_probability = 0.3
        self.msg_queue = MsgQueue(self.loss_probability)
        self.ack_queue = MsgQueue(0)
        self.sender_thread = Thread(target=self.send_message, args=())

    def send_message(self):
        while True:

            if self.stop_flag:
                return
            if len(self.message_to_send) == 0:
                continue

            message_data = self.message_to_send[0]

            message = Message()
            message.data = message_data

            send_time = time.time()
            self.msg_queue.send_message(message)
            # print(f"send{message}\n", end="")

            while True:

                if self.stop_flag:
                    return

                ack_message = self.ack_queue.get_message()
                if ack_message is not None:
                    self.message_to_send.pop(0)
                    # self.ack_queue.msg_queue.clear() ############/////////////////////////////////////////////
                    break

                curr_time = time.time()
                if curr_time - send_time > self.timeout:
                    self.msg_queue.send_message(message)
                    send_time = time.time()
                    # print(f"resend{message}\n", end="")

    def send(self, message):
        self.message_to_send.append(message)

    def start(self):
        self.sender_thread.start()

    def stop(self):
        self.stop_flag = True

    def get(self):
        new_message = self.msg_queue.get_message()
        # print(f"get: {new_message}\n", end="")
        if new_message is None:
            return
        if new_message.status == MessageStatus.LOST:
            # print(f"get{new_message}\n", end="")
            return
        # print(f"get{new_message}\n", end="")
        ack_msg = Message()
        ack_msg.data = "ack"
        self.ack_queue.send_message(ack_msg)

        return new_message.data

    pass


class Connection:

    def __init__(self):
        self.right_queue = MsgPipe()
        self.left_queue = MsgPipe()
        self.right_queue.start()
        self.left_queue.start()

    def __str__(self):
        return f"(->:{self.right_queue}\n<-:{self.right_queue})"

    def stop(self):
        self.right_queue.stop()
        self.left_queue.stop()
    @staticmethod
    def __get_message(queue):
        return queue.get_message()

    def get_message(self, direction=0):
        if direction == 0:
            res = self.right_queue.get()
            # print(f"get {direction}: {res}\n", end="")
            return res
        else:
            res = self.left_queue.get()
            # print(f"get {direction}: {res}\n", end="")
            return res

    def send_message(self, message, direction=0):
        if direction == 0:
            self.left_queue.send(message)
            # print(f"send <-: {message}\n")
            return
        else:
            self.right_queue.send(message)
            # print(f"send ->: {message}\n")
            return




