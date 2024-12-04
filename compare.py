from outputGen import find_time
from CPF import CPF
from queueSequence import queue_sequence
from randomSequence import random_sequence
import copy
from experimentGen import generate_random_experiments
import time
import csv

def write_to_csv(makespan, computation_time, throughput, waittime, filename='metrics.csv'):
    # Fieldnames for CSV
    fieldnames = ['Metric', 'cpf', 'queue', 'random']

    # Writing to CSV
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Write header
        writer.writeheader()

        # Write each dictionary with its corresponding header
        writer.writerow({'Metric': 'makespan', **makespan})
        writer.writerow({'Metric': 'computation time', **computation_time})
        writer.writerow({'Metric': 'throughput', **throughput})
        writer.writerow({'Metric': 'robot movement', **waittime})

    print(f"CSV file '{filename}' has been created.")

win = {"cpf":0,"queue":0,"random":0}
for exp in [5]:
    experiments = {'exp1': ['B', 'D', 'A', 'C', 'D', 'C', 'D', 'B', 'A', 'C', 'B'], 'exp2': ['B', 'A', 'D', 'A', 'B', 'A', 'B', 'A', 'C', 'D', 'C', 'A'], 'exp3': ['A', 'B', 'C', 'B', 'D', 'C', 'B', 'D', 'B', 'A', 'B', 'D'], 'exp4': ['D', 'B', 'C', 'B', 'A', 'B', 'D', 'A', 'B', 'D', 'B', 'D'], 'exp5': ['A', 'D', 'A', 'C', 'A', 'C', 'B', 'C', 'B', 'D', 'A'], 'exp6': ['B', 'D', 'A', 'B', 'D', 'B', 'D', 'B', 'A', 'B', 'A', 'D'], 'exp7': ['A', 'C', 'D', 'B', 'C', 'A', 'D', 'A', 'B', 'D', 'C', 'D'], 'exp8': ['D', 'B', 'A', 'B', 'C', 'A', 'B', 'A', 'B', 'A', 'C', 'A'], 'exp9': ['C', 'D', 'A', 'D', 'B', 'C', 'B', 'C', 'D', 'C', 'B', 'A'], 'exp10': ['D', 'A', 'D', 'C', 'D', 'A', 'C', 'A', 'B', 'D', 'B', 'D'], 'exp11': ['A', 'C', 'A', 'B', 'D', 'A', 'C', 'A', 'B', 'A', 'C', 'B'], 'exp12': ['D', 'C', 'A', 'C', 'D', 'B', 'C', 'D', 'C', 'A', 'D']}
    number_of_workcell = 7
    # print(experiments)
    result={"cpf":0,"queue":0,"random":0}
    time_exp = {"cpf":0,"queue":0,"random":0}
    wait_time = {"cpf":0,"queue":0,"random":0}
    try:
        start_time = time.time()
        experiment_count = 100
        for _ in range(experiment_count):
            used_experiments = copy.deepcopy(experiments)
            makespan,wait = find_time(CPF(used_experiments))
            result['cpf']+= makespan
            wait_time['cpf']+= wait
        end_time = time.time()
        time_exp['cpf'] = end_time-start_time
        start_time = time.time()
        for _ in range(experiment_count):
            used_experiments = copy.deepcopy(experiments)
            makespan,wait = find_time(queue_sequence(used_experiments)) 
            result['queue']+= makespan
            wait_time['queue']+= wait
        end_time = time.time()
        time_exp['queue'] = end_time-start_time
        start_time = time.time()
        for _ in range(experiment_count):
            used_experiments = copy.deepcopy(experiments)
            makespan,wait = find_time(random_sequence(used_experiments)) 
            result['random']+= makespan
            wait_time['random']+= wait
        end_time = time.time()
        time_exp['random'] = end_time-start_time
        result = {k: v / experiment_count for k, v in result.items()}
        result = {k: v / 3600 for k, v in result.items()}
        wait_time = {k: v / experiment_count for k, v in wait_time.items()}
        wait_time = {k: v / (2*number_of_workcell) for k, v in wait_time.items()}
        min_key = min(result, key=result.get)
        win[min_key]+=1
        throughput = {k: len(experiments)/v for k, v in result.items()}
        throughput = {k: v*3600 for k, v in result.items()}
        write_to_csv(result, time_exp, throughput, wait_time,'metrics'+str(exp)+'.csv')
        # print(result, time_exp, throughput, wait_time)
    except Exception as e:
        print("failed",e)
        print(experiments)
        break
    # print("CPF",cpf_time/1000)
    # print("Queue",queue_time/1000)
    # print("Random",random_time/1000)
print(win)
    