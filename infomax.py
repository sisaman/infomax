import os
import subprocess
import threading

import jdatetime as jd
import pandas as pd
import sys


class Infomax:
    def __init__(self, dataset, num_sources, time_window, stdout, onStop):
        self.dataset = dataset
        self.num_sources = num_sources
        self.time_window = time_window
        self.running = False
        self.proc = None
        self.stdout = stdout
        self.selected_users = []
        self.expected_influence = 0
        self.onStop = onStop

    def execute_command(self, cmd):
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        while True:
            line = self.proc.stdout.readline()
            if not line:
                break
            self.stdout.write(line)

    def clear_temp(self):
        self.stdout.write('Removing temporary files...')
        os.chdir('bin')
        try:
            files = os.listdir('.')
            for file in files:
                if file.endswith(".txt"):
                    os.remove(file)
            self.stdout.write('done\n')
        except Exception as e:
            self.running = False
            print(e)
        finally:
            os.chdir('..')

    def parse_xlsx(self):
        self.stdout.write('Reading dataset...')
        try:
            sheet = pd.read_excel(self.dataset)
            cascades = {}
            user_index = {}
            user_count = 0
            min_time = float('inf')
            for post in sheet.values:
                id = post[0]
                date = post[1].split('/')
                time = post[2]
                user = post[3]
                timestamp = jd.datetime(int(date[0]) + 1300, int(date[1]), int(date[2]), time.hour, time.minute,
                                        time.second).togregorian().timestamp()

                if user not in user_index:
                    user_index[user] = user_count
                    user_count += 1

                if id not in cascades:
                    cascades[id] = []

                cascades[id].append((timestamp, user_index[user]))
                min_time = min(timestamp, min_time)

            users = []
            for user, index in user_index.items():
                users.append((index, user))

            users.sort()
            with open('bin/example-cascades.txt', 'w') as out:
                for index, user in users:
                    out.write('%s,%s\n' % (index, user))
                out.write('\n')
                counter = 0
                for _, cascade in cascades.items():
                    out.write('%d;' % counter)
                    counter += 1
                    # time_counter = 0
                    string = ''
                    # user_set = set()
                    for timestamp, user in sorted(cascade):
                        # if user not in user_set:
                        #     user_set.add(user)
                        string += ',%s,%s' % (user, (timestamp - min_time) / 60)
                        # time_counter += 1
                    out.write(string[1:] + '\n')
            self.stdout.write('done\n')
        except Exception as e:
            self.running = False
            print(e)

    def infer_network(self):
        os.chdir('bin')
        try:
            with open('example-cascades.txt') as cascades_file, open("example-network.txt", "w") as network_file:
                cascades_lines = cascades_file.read().splitlines()
                for line in cascades_lines:
                    network_file.write(line + '\n')
                    if not line:
                        break

            cmd = "infer.exe -rm:3 -s:0"
            self.execute_command(cmd)
        except Exception as e:
            self.running = False
            print(e)
        finally:
            os.chdir('..')

    def influence_maximization(self):
        os.chdir('bin')
        try:
            with open("network.txt") as net_file, open("inferred-network.txt", "w") as infnet_file:
                net_lines = net_file.read().splitlines()
                index = net_lines.index('')
                for i in range(index + 1):
                    infnet_file.write(net_lines[i] + '\n')

                for line in net_lines[index + 1:]:
                    u, v, x, a = tuple(line.split(','))
                    infnet_file.write("%s,%s,%s\n" % (u, v, a))

            os.remove('example-network.txt')
            cmd = "influmax.exe -n:inferred-network.txt -s:" + str(self.num_sources) + " -t:" + str(self.time_window)
            self.execute_command(cmd)
        except Exception as e:
            self.running = False
            print(e)
        finally:
            os.chdir('..')

    def perform_task(self):
        self.running = True
        self.clear_temp()
        self.parse_xlsx()
        if self.running:
            self.infer_network()
        if self.running:
            self.influence_maximization()
        if self.running:
            self.save_results()
        self.onStop()

    def start(self):
        t = threading.Thread(target=self.perform_task, daemon=True)
        t.start()

    def stop(self):
        if self.running:
            self.running = False
            if self.proc is not None and self.proc.poll() is None:
                self.proc.kill()
            print('Job terminated before finish!')
            self.onStop()

    def save_results(self):
        # process influence-info-network.txt
        os.chdir('bin')
        try:
            # os.startfile('influence-info-network.txt')
            self.selected_users.clear()
            user_map = {}
            with open('example-cascades.txt') as inp:
                for line in inp:
                    line = line.strip()
                    if not line:
                        break
                    id, name = tuple(line.split(','))
                    user_map[id] = name
            with open('influence-info-network.txt') as inp:
                inp.readline()
                self.expected_influence = float(inp.readline())
                inp.readline()
                for line in inp:
                    line = line.strip()
                    if not line:
                        break
                    id,_,source = tuple(line.split(','))
                    if bool(int(source)):
                        self.selected_users.append(user_map[id])

            self.stdout.write('\n')
            self.stdout.write('Expected number of infected users: %.2f\n\n' % self.expected_influence)
            self.stdout.write('Selected users:\n')
            for user in self.selected_users:
                self.stdout.write(user + '\n')
        except Exception as e:
            self.running = False
            print(e)
        finally:
            os.chdir('..')


if __name__ == '__main__':
    infomax = Infomax('finalworktahvili.xlsx', 2, 60, sys.stdout)
    infomax.perform_task()
    # with open('bin/influence-info-network.txt') as inp:
    #     inp.readline()
    #     inp.readline()
    #     inp.readline()
    #     for line in inp:
    #         print(line)