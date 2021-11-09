import numpy as np
import enum
import time
from threading import Thread
import matplotlib.pyplot as plt


class MessageStatus(enum.Enum):
    OK = enum.auto()
    LOST = enum.auto()


class Message:
    number = -1
    real_number = -1
    data = ""
    status = MessageStatus.OK

    def __init__(self):
        pass

    def copy(self):
        msg = Message()
        msg.number = self.number
        msg.data = self.data
        msg.status = self.status

    def __str__(self):
        return f"({self.real_number}({self.number}), {self.data}, {self.status})"


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

    def send_message(self, msg):
        tmp_msg = self.emulating_channel_problems(msg)
        self.msg_queue.append(tmp_msg)

    def emulating_channel_problems(self, msg):
        val = np.random.rand()
        if val <= self.loss_probability:
            msg.status = MessageStatus.LOST

        return msg

    def __str__(self):
        res_str = "[ "
        for i in range(len(self.msg_queue)):
            msg = self.msg_queue[i]
            res_str += f"({msg.number}, {msg.status}), "

        res_str += "]"
        return res_str


def GBN_sender(window_size, max_number, timeout):

    curr_number = 0
    last_ans_number = -1
    start_time = time.time()
    while last_ans_number < max_number:
        expected_number = (last_ans_number + 1) % window_size

        if answer_msg_queue.has_msg():
            ans = answer_msg_queue.get_message()
            if ans.number == expected_number:
                # последовательное подтверждение пакетов - всё ок
                last_ans_number += 1
                start_time = time.time()
            else:
                # произошёл сбой, нужно повторить отправку сообщений с последнего подтверждённого
                curr_number = last_ans_number + 1

        # долго нет ответа с последнего подтверждения
        if time.time() - start_time > timeout:
            # произошёл сбой, нужно повторить отправку сообщений с последнего подтверждённого
            curr_number = last_ans_number + 1
            start_time = time.time()

        if (curr_number < last_ans_number + window_size) and (curr_number <= max_number):
            #   отправляем не более window_size сообщений наперёд
            k = curr_number % window_size
            msg = Message()
            msg.number = k
            msg.real_number = curr_number
            send_msg_queue.send_message(msg)
            posted_msgs.append(f"{curr_number}({k})")

            curr_number += 1
        pass

    msg = Message()
    msg.data = "STOP"
    send_msg_queue.send_message(msg)


def GBN_receiver(window_size):

    expected_number = 0
    while True:
        if send_msg_queue.has_msg():
            curr_msg = send_msg_queue.get_message()
            #print(f"res: {curr_msg} | {expected_number}")
            if curr_msg.data == "STOP":
                break

            if curr_msg.status == MessageStatus.LOST:
                continue

            if curr_msg.number == expected_number:
                ans = Message()
                ans.number = curr_msg.number
                answer_msg_queue.send_message(ans)

                received_msgs.append(f"{curr_msg.real_number}({curr_msg.number})")
                expected_number = (expected_number + 1) % window_size

            else:
                continue





def SRP_sender(window_size, max_number, timeout):
    class WndMsgStatus(enum.Enum):
        BUSY = enum.auto()
        NEED_REPEAT = enum.auto()
        CAN_BE_USED = enum.auto()

    class WndNode:
        def __init__(self, number):
            self.status = WndMsgStatus.NEED_REPEAT
            self.time = 0
            self.number = number
            pass

        def __str__(self):
            return f"( {self.number}, {self.status}, {self.time})"


    wnd_nodes = [WndNode(i) for i in range(window_size)]

    curr_number = 0
    ans_count = 0

    while ans_count < max_number:

        res_str = "["
        for i in range(window_size):
            res_str += wnd_nodes[i].__str__()
        res_str += "]"
        # print("res:", res_str)

        if answer_msg_queue.has_msg():
            ans = answer_msg_queue.get_message()
            ans_count += 1
            wnd_nodes[ans.number].status = WndMsgStatus.CAN_BE_USED


        # долго нет ответа с последнего подтверждения
        curr_time = time.time()
        for i in range(window_size):
            if wnd_nodes[i].number > max_number:
                continue

            send_time = wnd_nodes[i].time
            if curr_time - send_time > timeout:
                # произошёл сбой, нужно повторить отправку этого сообщения
                wnd_nodes[i].status = WndMsgStatus.NEED_REPEAT

        # отправляем новые или повторяем, если необходимо
        for i in range(window_size):
            if wnd_nodes[i].number > max_number:
                continue

            if wnd_nodes[i].status == WndMsgStatus.BUSY:
                continue

            elif wnd_nodes[i].status == WndMsgStatus.NEED_REPEAT:

                wnd_nodes[i].status = WndMsgStatus.BUSY
                wnd_nodes[i].time = time.time()

                msg = Message()
                msg.number = i
                msg.real_number = wnd_nodes[i].number
                send_msg_queue.send_message(msg)
                posted_msgs.append(f"{msg.real_number}({msg.number})")
                #print(f"sen: {msg}")

            elif wnd_nodes[i].status == WndMsgStatus.CAN_BE_USED:
                wnd_nodes[i].status = WndMsgStatus.BUSY
                wnd_nodes[i].time = time.time()
                wnd_nodes[i].number = wnd_nodes[i].number + window_size

                if wnd_nodes[i].number > max_number:
                    continue

                msg = Message()
                msg.number = i
                msg.real_number = wnd_nodes[i].number
                send_msg_queue.send_message(msg)
                posted_msgs.append(f"{msg.real_number}({msg.number})")
                #print(f"sen: {msg}")




    msg = Message()
    msg.data = "STOP"
    send_msg_queue.send_message(msg)


def SRP_receiver(window_size):

    while True:
        if send_msg_queue.has_msg():
            curr_msg = send_msg_queue.get_message()
            # print(f"res: {curr_msg}")

            if curr_msg.data == "STOP":
                break

            if curr_msg.status == MessageStatus.LOST:
                continue

            ans = Message()
            ans.number = curr_msg.number
            answer_msg_queue.send_message(ans)
            received_msgs.append(f"{curr_msg.real_number}({curr_msg.number})")




send_msg_queue = MsgQueue()
answer_msg_queue = MsgQueue()

posted_msgs = []
received_msgs = []


def losing_test():
    global send_msg_queue
    global answer_msg_queue
    global posted_msgs
    global received_msgs

    window_size = 3
    timeout = 0.2
    max_number = 100
    loss_probability_arr = np.linspace(0, 0.9, 9)
    protocol_arr = ["GBN", "SRP"]

    print("p    | GBN             |SRP")
    print("     | t     |k        |t    |  k")

    gbn_time = []
    srp_time = []
    gbn_k = []
    srp_k = []
    for p in loss_probability_arr:
        table_row = f"{p:.1f}\t"
        send_msg_queue = MsgQueue(p)
        answer_msg_queue = MsgQueue(p)
        posted_msgs = []
        received_msgs = []

        for protocol in protocol_arr:
            if protocol == "GBN":
                sender_th = Thread(target=GBN_sender, args=(window_size, max_number, timeout))
                receiver_th = Thread(target=GBN_receiver, args=(window_size,))
            elif protocol == "SRP":
                sender_th = Thread(target=SRP_sender, args=(window_size, max_number, timeout))
                receiver_th = Thread(target=SRP_receiver, args=(window_size,))

            timer_start = time.time()
            sender_th.start()
            receiver_th.start()

            sender_th.join()
            receiver_th.join()
            timer_end = time.time()

            k = len(received_msgs) / len(posted_msgs)
            elapsed = timer_end - timer_start

            table_row += f" | {elapsed:2.2f}  | {k:.2f}   "
            if protocol == "GBN":
                gbn_time.append(elapsed)
                gbn_k.append(k)
            else:
                srp_time.append(elapsed)
                srp_k.append(k)

        print(table_row)

    fig, ax = plt.subplots()
    ax.plot(loss_probability_arr, gbn_k, label="Go-Back-N")
    ax.plot(loss_probability_arr, srp_k, label="Selective repeat")
    ax.set_xlabel('вероятность потери пакета')
    ax.set_ylabel('коэф. эффективности')
    ax.legend()
    fig.show()

    fig, ax = plt.subplots()
    ax.plot(loss_probability_arr, gbn_time, label="Go-Back-N")
    ax.plot(loss_probability_arr, srp_time, label="Selective repeat")
    ax.set_xlabel('вероятность потери пакета')
    ax.set_ylabel('время передачи, с')
    ax.legend()
    fig.show()

    print("p")
    print(loss_probability_arr)
    print("GBN")
    print(gbn_time)
    print("time")
    print("k")
    print(gbn_k)

    print("SRP")
    print(srp_time)
    print("time")
    print("k")
    print(srp_k)


def window_test():
    global send_msg_queue
    global answer_msg_queue
    global posted_msgs
    global received_msgs

    window_size_arr = range(2, 11)
    timeout = 0.2
    max_number = 100
    loss_probability_arr = 0.2
    send_msg_queue = MsgQueue(loss_probability_arr)
    answer_msg_queue = MsgQueue(loss_probability_arr)
    protocol_arr = ["GBN", "SRP"]

    print("w    | GBN             |SRP")
    print("     | t     |k        |t    |  k")

    gbn_time = []
    srp_time = []
    gbn_k = []
    srp_k = []
    for window_size in window_size_arr:
        table_row = f"{window_size:}\t"

        posted_msgs = []
        received_msgs = []

        for protocol in protocol_arr:
            if protocol == "GBN":
                sender_th = Thread(target=GBN_sender, args=(window_size, max_number, timeout))
                receiver_th = Thread(target=GBN_receiver, args=(window_size,))
            elif protocol == "SRP":
                sender_th = Thread(target=SRP_sender, args=(window_size, max_number, timeout))
                receiver_th = Thread(target=SRP_receiver, args=(window_size,))

            timer_start = time.time()
            sender_th.start()
            receiver_th.start()

            sender_th.join()
            receiver_th.join()
            timer_end = time.time()

            k = len(received_msgs) / len(posted_msgs)
            elapsed = timer_end - timer_start

            table_row += f" | {elapsed:2.2f}  | {k:.2f}   "
            if protocol == "GBN":
                gbn_time.append(elapsed)
                gbn_k.append(k)
            else:
                srp_time.append(elapsed)
                srp_k.append(k)

        print(table_row)

    fig, ax = plt.subplots()
    ax.plot(window_size_arr, gbn_k, label="Go-Back-N")
    ax.plot(window_size_arr, srp_k, label="Selective repeat")
    ax.set_xlabel('размер окна')
    ax.set_ylabel('коэф. эффективности')
    ax.legend()
    fig.show()

    fig, ax = plt.subplots()
    ax.plot(window_size_arr, gbn_time, label="Go-Back-N")
    ax.plot(window_size_arr, srp_time, label="Selective repeat")
    ax.set_xlabel('размер окна')
    ax.set_ylabel('время передачи, с')
    ax.legend()
    fig.show()


    print("w")
    print(window_size_arr)
    print("GBN")
    print(gbn_time)
    print("time")
    print("k")
    print(gbn_k)

    print("SRP")
    print(srp_time)
    print("time")
    print("k")
    print(srp_k)



def main():
    global send_msg_queue
    global answer_msg_queue

    window_size = 2
    max_number = 100
    timeout = 0.5
    loss_probability = 0.3
    protocol = "GBN"
    # protocol = "SRP"
    send_msg_queue = MsgQueue(loss_probability)
    answer_msg_queue = MsgQueue(loss_probability)

    # GBN_sender(window_size, max_number, timeout)
    # GBN_receiver(window_size)

    for p in np.linspace(0, 1, 10):
        window_size = 3


    if protocol == "GBN":

        sender_th = Thread(target=GBN_sender, args=(window_size, max_number, timeout))
        receiver_th = Thread(target=GBN_receiver, args=(window_size,))

    elif protocol == "SRP":
        sender_th = Thread(target=SRP_sender, args=(window_size, max_number, timeout))
        receiver_th = Thread(target=SRP_receiver, args=(window_size,))

    else:
        print("unknown protocol: ", protocol)
        return

    sender_th.start()
    receiver_th.start()

    sender_th.join()
    receiver_th.join()

    print(f"posted ({len(posted_msgs)}): \t", posted_msgs)
    print(f"received ({len(received_msgs)}):\t", received_msgs)



if __name__ == '__main__':
    print("------------------------------------------")
    print("losing")
    print("------------------------------------------")
    losing_test()


    print("------------------------------------------")
    print("window")
    print("------------------------------------------")
    # window_test()



