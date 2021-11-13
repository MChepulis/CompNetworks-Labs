import numpy as np
import enum
import time
from threading import Thread

import topology as topology_class

class MsgType(enum.Enum):
    NEIGHBORS = enum.auto()
    GET_TOPOLOGY = enum.auto()
    SET_TOPOLOGY = enum.auto()
    OFF = enum.auto()
    PRINT_WAYS = enum.auto()


class Message:
    def __init__(self):
        self.data = None
        self.type = None

    def __str__(self):
        return f"({self.type}: {self.data})"


class Connection:

    # owner -> node # right
    # owner <- node # left
    def __init__(self):
        self.right_queue = []
        self.left_queue = []

    def __str__(self):
        return f"(->:{self.right_queue}\n<-:{self.right_queue})"

    @staticmethod
    def __get_message(queue, ):
        if len(queue) > 0:
            result = queue[0]
            queue.pop(0)
            return result
        else:
            return None

    def get_message(self, direction=0):
        if direction == 0:
            res = self.__get_message(self.right_queue)
            if res:
                #print(f"get  ->:{res}\n")
                pass
            return res
        else:
            res = self.__get_message(self.left_queue)
            if res:
                #print(f"get  <-:{res}\n")
                pass
            return res

    def send_message(self, message, direction=0):
        if direction == 0:
            self.left_queue.append(message)
            #print(f"send <-: {message}\n")
            return
        else:
            self.right_queue.append(message)
            #print(f"send ->: {message}\n")
            return


class Router:

    def __init__(self, conn, index):
        self.DR_connection = conn
        self.topology = topology_class.Topology()
        self.shortest_roads = None
        self.index = index
        self.neighbors = []

    def print_shortest_ways(self):
        shortest_ways = self.topology.get_shortest_ways(self.index)
        print(f"{self.index}: {shortest_ways}\n", end="")

    def send_neighbors(self):
        msg = Message()
        msg.type = MsgType.NEIGHBORS
        msg.data = self.neighbors.copy()
        self.DR_connection.send_message(msg)

    def get_topology(self):
        msg = Message()
        msg.type = MsgType.GET_TOPOLOGY
        self.DR_connection.send_message(msg)

    def router_start(self):
        self.send_neighbors()
        self.get_topology()

    def router_off(self):
        msg = Message()
        msg.type = MsgType.OFF
        self.DR_connection.send_message(msg)

    def add_node(self, index, neighbors):
        # print(f".{index}.")
        self.topology.add_new_node(index)
        for j in neighbors:
            self.topology.add_new_link(index, j)


    def delete_node(self, index):
        self.topology.delete_node(index)



    def proc_message(self):
        input_msg = self.DR_connection.get_message()


        if input_msg is None:
            return

        print(f"r({self.index}) : {input_msg}\n", end="")

        if input_msg.type == MsgType.NEIGHBORS:
            index = input_msg.data["index"]
            neighbors = input_msg.data["neighbors"]
            self.add_node(index, neighbors)

        elif input_msg.type == MsgType.SET_TOPOLOGY:
            new_topology = input_msg.data
            self.topology = new_topology

        elif input_msg.type == MsgType.OFF:
            index = input_msg.data
            self.delete_node(index)

        elif input_msg.type == MsgType.PRINT_WAYS:
            self.print_shortest_ways()

        else:
            print("DR: unexpected msf type:", input_msg.type)

    pass


class DesignatedRouter:

    def __init__(self):
        self.connections = []
        self.topology = topology_class.Topology()

    def add_connection(self):
        new_connection = Connection()
        new_index = len(self.connections)
        self.connections.append(new_connection)
        return new_connection, new_index

    def add_node(self, index, neighbors):
        self.topology.add_new_node(index)
        for j in neighbors:
            self.topology.add_new_link(index, j)

    def delete_node(self, index):
        self.topology.delete_node(index)

    def send_all_exclude_one(self, exclude_index,  msg):
        for conn_ind in range(len(self.connections)):
            conn = self.connections[conn_ind]
            if conn is None:
                continue
            if conn_ind == exclude_index:
                continue
            conn.send_message(msg, 1)

    def proc_msg_neighbors(self, conn_ind, input_msg):
        self.add_node(conn_ind, input_msg.data)

        msg = Message()
        msg.type = MsgType.NEIGHBORS
        msg.data = {"index": conn_ind,
                    "neighbors": input_msg.data
                    }

        self.send_all_exclude_one(conn_ind, msg)

    def proc_msg_off(self, conn_ind, input_msg):
        self.delete_node(conn_ind)

        msg = Message()
        msg.type = MsgType.OFF
        msg.data = conn_ind

        self.send_all_exclude_one(conn_ind, msg)

    def print_shortest_ways(self):
        msg = Message()
        msg.type = MsgType.PRINT_WAYS
        for conn in self.connections:
            conn.send_message(msg, 1)

    def proc_message(self):
        for conn_ind in range(len(self.connections)):
            conn = self.connections[conn_ind]
            if conn is None:
                continue

            input_msg = conn.get_message(1)

            if input_msg is None:
                continue

            print(f"dr({conn_ind}): {input_msg}\n", end="")

            if input_msg.type == MsgType.NEIGHBORS:
                self.proc_msg_neighbors(conn_ind, input_msg)

            elif input_msg.type == MsgType.GET_TOPOLOGY:
                msg = Message()
                msg.type = MsgType.SET_TOPOLOGY
                msg.data = self.topology.copy()
                conn.send_message(msg, 1)

            elif input_msg.type == MsgType.OFF:
                self.proc_msg_off(conn_ind, input_msg)

            else:
                print("DR: unexpected msf type:", input_msg.type)




designed_router: DesignatedRouter = None

stop_flag = False
printer_flag = False
blink_conn_arr = []



def router_run(neighbors):
    global designed_router
    global blink_conn_arr

    conn, index = designed_router.add_connection()
    router = Router(conn, index)
    router.neighbors = neighbors.copy()
    router.router_start()

    while True:
        router.proc_message()
        if blink_conn_arr[router.index]:
            router.router_off()
            time.sleep(2)
            router.router_start()
            blink_conn_arr[router.index] = False

        if stop_flag:
            break


def designed_router_run():
    global designed_router
    global printer_flag
    designed_router = DesignatedRouter()

    while True:
        designed_router.proc_message()
        if printer_flag:
            designed_router.print_shortest_ways()
            printer_flag = False
        if stop_flag:
            break


def stopper():
    global stop_flag
    time.sleep(10)
    stop_flag = True


def printer():
    global printer_flag
    while True:
        time.sleep(1)
        printer_flag = True
        if stop_flag:
            break

def connections_breaker():
    global blink_conn_arr
    time.sleep(2)
    threshold = 0.5
    while True:
        time.sleep(0.01)
        val = np.random.rand()
        if val >= threshold:
            index = np.random.randint(0, len(blink_conn_arr))
            blink_conn_arr[index] = True
            time.sleep(2)

        if stop_flag:
            break


def simulate(nodes, neighbors):
    global blink_conn_arr

    dr_thread = Thread(target=designed_router_run, args=())

    node_threads = [Thread(target=router_run, args=(neighbors[i],)) for i in range(len(nodes))]
    blink_conn_arr = [False for i in range(len(nodes))]

    dr_thread.start()
    for i in range(len(nodes)):
        node_threads[i].start()

    printer_thread = Thread(target=printer, args=())
    conn_breaker_thread = Thread(target=connections_breaker, args=())
    conn_breaker_thread.start()
    printer_thread.start()

    time.sleep(5)
    global stop_flag
    stop_flag = True
    for i in range(len(nodes)):
        node_threads[i].join()

    dr_thread.join()



def main():
    linear = {
        "nodes": [0, 1, 2, 3, 4],
        "neighbors": [[1], [0, 2], [1, 3], [2, 4], [3]]
    }
    circle = {
        "nodes": [0, 1, 2, 3, 4],
        "neighbors": [[4, 1], [0, 2], [1, 3], [2, 4], [3, 0]]
    }
    star = {
        "nodes": [0, 1, 2, 3, 4],
        "neighbors": [[2], [2], [1, 3, 4], [2], [2]]
    }

    circle = {
        "nodes": [0, 1, 2, 3, 4],
        "neighbors": [[1], [2], [3], [4], [0]]
    }
    cur_topology = linear
    simulate(cur_topology["nodes"], cur_topology["neighbors"])


    pass
if __name__ == '__main__':
    main()

