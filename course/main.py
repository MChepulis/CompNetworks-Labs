import numpy as np
import matplotlib.pyplot as plt

from threading import Thread
import channel_protocol
from old_functions import get_intersect_line_and_circle

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"({self.x}, {self.y})"



class Screen:

    def __init__(self, w, h, x, y, r):
        self.width = w
        self.height = h
        self.radius = r
        self.centre = Point(x, y)
    pass

    def draw(self, ax):

        x_min = - self.width / 2
        x_max = + self.width / 2
        y_min = - self.height / 2
        y_max = + self.height / 2

        ax.plot([x_min, x_max, x_max, x_min, x_min], [y_max, y_max, y_min, y_min, y_max])

        sections = 630
        x = [self.centre.x + self.radius * np.cos(2 * np.pi * i / sections) for i in range(sections)]
        y = [self.centre.y + self.radius * np.sin(2 * np.pi * i / sections) for i in range(sections)]
        x.append(x[0])
        y.append(y[0])
        ax.plot(x, y)


class General:
    def __init__(self, index):
        self.connections = []
        self.conn_dirs = []
        self.conn_indexes = []
        self.is_corrupted = False
        self.index = index
        self.byzantine_result = None
        self.threshold = 0

    def add_connections(self, conn, conn_dir, index):
        self.connections.append(conn)
        self.conn_dirs.append(conn_dir)
        self.conn_indexes.append(index)

    def get_my_value_s1(self):
        return self.index

    @staticmethod
    def get_corrupted_value(n):
        return np.random.randint(n)

    @staticmethod
    def get_corrupted_tuples(n):
        return [np.random.randint(n) for i in range(n)]

    def byzantine(self, screen):
        #step 1
        # for all send my_value
        my_value = self.get_my_value_s1()
        n = len(self.connections) + 1

        for i in range(len(self.connections)):
            conn = self.connections[i]
            conn_dir = self.conn_dirs[i]
            index = self.conn_indexes[i]

            if self.is_corrupted:
                my_value = self.get_corrupted_value(n)
            conn.send_message(my_value, conn_dir)

        # for all get values
        values = [None] * (len(self.connections) + 1)
        for i in range(len(self.connections)):
            conn = self.connections[i]
            conn_dir = self.conn_dirs[i]
            index = self.conn_indexes[i]

            new_value = None
            while new_value is None:
                new_value = conn.get_message(conn_dir)

            values[index] = new_value
        values[self.index] = my_value
        print(f"{self.index}: {values}\n", end="")
        #step 2
        # make tuple(..., value_i, ...)
        #step 3
        # for all send tuple
        for i in range(len(self.connections)):
            conn = self.connections[i]
            conn_dir = self.conn_dirs[i]
            index = self.conn_indexes[i]

            if self.is_corrupted:
                values = self.get_corrupted_tuples(len(values))

            conn.send_message(values, conn_dir)

        # for all get tuples
        values_arr = [None] * (len(self.connections) + 1)
        for i in range(len(self.connections)):
            conn = self.connections[i]
            conn_dir = self.conn_dirs[i]
            index = self.conn_indexes[i]

            new_values = None
            while new_values is None:
                new_values = conn.get_message(conn_dir)

            values_arr[index] = new_values
        values_arr[self.index] = values

        print(f"{self.index}: {values_arr}\n", end="")

        #step 4
        # for tuples compute true values

        # этап голосования
        result_values = [None] * len(values_arr)
        for i in range(len(values_arr)):
            other_values = []
            for j in range(len(values_arr)):
                other_values.append(values_arr[j][i])

            unique_vals = set()
            for val in other_values:
                unique_vals.add(val)

            tmp_res = {}
            for val in unique_vals:
                count = other_values.count(val)
                tmp_res[val] = count

            max_count = -1
            max_val = None
            for val in tmp_res:
                if tmp_res[val] > max_count:
                    max_count = tmp_res[val]
                    max_val = val
            if max_count >= self.threshold:
                result_values[i] = max_val

        # print(f"{self.index}:{result_values}\n", end="")
        self.byzantine_result = result_values

    def get_byzantine_result(self):
        return self.byzantine_result

    def stop_connections(self):
        for conn in self.connections:
            conn.stop()






def main():
    screen = Screen(12, 12, 0, 0, 3)
    pos = [3, 3]
    generals = []
    general_ths = []
    for i in range(4):
        generals.append(General(i))

    generals[3].is_corrupted = True
    for i in range(len(generals)):
        generals[i].threshold = len(generals) - 1 - 1

    for i in range(len(generals)):
        for j in range(i+1, len(generals)):
            connection = channel_protocol.Connection()
            generals[i].add_connections(connection, 0, j)
            generals[j].add_connections(connection, 1, i)

    for camera in generals:
        general_ths.append(Thread(target=camera.byzantine, args=(screen,)))

    for cam_th in general_ths:
        cam_th.start()

    for cam_th in general_ths:
        cam_th.join()

    for i in range(len(generals)):
        generals[i].stop_connections()

    print("byzantine_result")
    for camera in generals:
        result_values = camera.get_byzantine_result()
        print(f"{camera.index}: {result_values}\n", end="")

    pass



def test():
    con = channel_protocol.Connection()

    con.send_message("tttt", 1)
    con.send_message("111", 1)
    con.send_message("222", 1)
    con.send_message("t333", 1)

    print(f"{con.get_message(0)}\n", end="")

    while True:
        mes = con.get_message(0)
        if mes is not None:
            print(f"{mes}\n", end="")

if __name__ == "__main__":
    main()



