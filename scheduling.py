import pandas as pd
import os
import json
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import random
from binding import binding
import math

# Load CSV files
usage_times = pd.read_csv(os.getcwd()+'/Submission/useTime.csv')
move_times = pd.read_csv(os.getcwd()+'/Submission/move.csv', index_col=0)
distance_df = pd.read_csv(os.getcwd()+'/Submission/distance_times.csv', index_col=0, header=0)

# Equipment usage times
usage_dict = usage_times.set_index('Equipment')['Time'].to_dict()

distance_dict = distance_df.to_dict()

# Robot movement times
move_dict = move_times.to_dict()

first_exp_time=0

with open('./Submission/start_position.json') as f:
    start_position = json.load(f)

class TimeHashMap:
    def __init__(self):
        self.timeline = {}
        self.checkpoint = None
        self.base = None

    def input_time_interval(self, start, end, label):
        for time in range(start, end+1):
            if time in self.timeline:
                raise Exception()
        for time in range(start, end+1):
            self.timeline[time] = label
        return True

    def get_next_empty(self, current_time):
        while current_time in self.timeline:
            current_time += 1
        return current_time

    def create_checkpoint(self, base):
        self.checkpoint = self.timeline.copy()
        if base:
            self.base = self.timeline.copy()

    def restore_checkpoint(self, base):
        if base:
            self.timeline = self.base
            self.checkpoint = None
            self.base = None
        elif self.checkpoint is not None:
            self.timeline = self.checkpoint
            self.checkpoint = None


    def get_intervals(self):
        intervals = []
        # print(self.tmeline)
        if self.timeline:
            times = sorted(self.timeline.keys())
            # print(times)
            start = times[0]
            label = self.timeline[start]
            prevTime = min(times)
            for time in times[1:]:
                if self.timeline[time] != label or prevTime != time-1:
                    intervals.append((start, prevTime, label))
                    start = time
                    label = self.timeline[start]
                prevTime = time
            intervals.append((start, times[-1] + 1, label))
            # print("intervals printed",intervals)
        return intervals

    def remove_time(self, start, end):
        for time in range(start, end):
            if time in self.timeline:
                del self.timeline[time]
    
class RobotMovementTimeHashMap(TimeHashMap):
    def __init__(self, start_position='O'):
        super().__init__()
        self.equipment_start_times = {}  # Stores the start time of each equipment
        self.robot_position = {0: start_position}  # Initial robot position at time 0

    def input_time_interval(self, start, end, label):
        # Ensure that previous positions are filled
        last_known_time = max(self.robot_position.keys())
        
        # Fill any gaps in the robot's position before the new interval
        for time in range(last_known_time + 1, start):
            self.robot_position[time] = self.robot_position[last_known_time]

        # Try to add the interval to the timeline
        if super().input_time_interval(start, end, label):
            # Update robot position: start time is the previous position, rest is the new position
            self.robot_position[start] = self.robot_position[last_known_time]
            for time in range(start+1, end + 1):
                self.robot_position[time] = label
            
            # Ensure the time right before the movement holds the previous position
            if start > 0:
                self.robot_position[start - 1] = self.robot_position.get(start - 1, self.robot_position[max(self.robot_position)])
            
            return True
        raise Exception()

def move_from_to(start_time, fromE, toE, movement_timeline):
    end_time = move_time(fromE, toE, start_position,start_time,movement_timeline)+start_time
    return end_time

def move_time(prev_equip, equipment, prev_pos, start_time=0, movement_timeline=None):
    _, workcell, index = equipment.split('-')
    if prev_equip == "":
        prev_equip = prev_pos[f"workcell_{workcell}"]
    _, prev_workcell, prev_index = prev_equip.split('-')
    if workcell == prev_workcell:
        req = abs(int(index)-int(prev_index))
        if movement_timeline:
            movement_timeline[workcell].input_time_interval(start_time,req+start_time,equipment)
        return req
    else:
        req1 = int(prev_index)
        req2 = int(index)
        req3 = int(distance_dict["workcell_"+workcell]["workcell_"+prev_workcell])
        if movement_timeline:
            movement_timeline[prev_workcell].input_time_interval(start_time,req1+start_time,f"P-{prev_workcell}-0")
            try:
                movement_timeline[f"{prev_workcell}-{workcell}"].input_time_interval(req1+start_time,req1+start_time+req3,f"P-{workcell}-0")
            except:
                movement_timeline[f"{prev_workcell}-{workcell}"] = RobotMovementTimeHashMap()
                movement_timeline[f"{prev_workcell}-{workcell}"].input_time_interval(req1+start_time,req1+start_time+req3,f"P-{workcell}-0")
            movement_timeline[workcell].input_time_interval(req1+start_time+req3,req1+start_time+req3+req2,equipment)
        return req1+req2+req3

def create_checkpoint(equipment, movement_timeline, base=False):
    equipment.create_checkpoint(base)
    for mov in movement_timeline.values():
        mov.create_checkpoint(base)
    pass

def restore_checkpoint(equipment, movement_timeline, base=False):
    equipment.restore_checkpoint(base)
    # print(movement_timeline)

    # The input time didnt work, so it will wait, before wait apply re binding
    for mov in movement_timeline.values():
        mov.restore_checkpoint(base)
    pass

def calculate_critical(experiments):
    experiment_times = {}
    prev_pos = start_position
    prev_equip = ""
    for experiment_name, equipment_list in experiments.items():
        total_time = 0 
        for equipment in equipment_list:
            total_time += usage_dict[equipment[0]]
            total_time += move_time(prev_equip, equipment, prev_pos)
            prev_equip = equipment
        experiment_times[experiment_name] = total_time
    sorted_experiments = sorted(experiment_times.items(), key=lambda x: x[1], reverse=True)
    most_used_experiments = [experiment for experiment, _ in sorted_experiments]
    return most_used_experiments

assigned_color={}

def plot_all_timelines(timelines, labels):
    # Generate a color map with a distinct color for each timeline
    csfont = {'fontname':'Times New Roman'}
    
    colors = list(mcolors.CSS4_COLORS.values()) #list(mcolors.TABLEAU_COLORS.values())
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Ensure there are enough colors for the number of labels
    if len(labels) > len(colors):
        raise ValueError("Not enough colors for the number of labels. Add more colors to the color list.")

    max_time = 0  # To find the maximum end time across all timelines

    # Plot each timeline
    for i, (timeline, label) in enumerate(zip(timelines, labels)):
        intervals = timeline.get_intervals()
        # color = colors[i % len(colors)]  # Cycle through available colors

        for start, end, interval_label in intervals:
            if type(timeline) is RobotMovementTimeHashMap:
                color = colors[0]
            else:
                try:
                    color = assigned_color[interval_label]
                except:
                    color = colors[random.randint(1,len(colors)-1)]
                    assigned_color[interval_label] = color
            # Draw the bar for each interval with a separate outline
            ax.barh(label, width=end - start, left=start, color=color, capstyle='round', edgecolor=tuple([c * 0.7 for c in mcolors.to_rgb(color)]))

        # Update maximum time
        try:
            max_time = max(max_time, max(end for _, end, _ in intervals))
        except:
            continue

    # Add labels and legend
    # ax.set_yticklabels(labels, fontsize=18, **csfont)
    ax.tick_params(axis='both', labelsize=18)
    ax.set_xlabel("Time", fontsize=18, **csfont)
    # ax.set_title("Equipment Timelines", fontsize=20, **csfont)
    ax.set_xlim(0, max_time + 1)
    plt.tight_layout()
    plt.savefig("Outputs/timeline_new.pdf", format="png")
    plt.show()

def do_experiment(experiments, equipments_timeline, movement_timeline, try_count, exp):
    global first_exp_time
    global gamma
    global first_time
    prev_equip = ""
    time=movement_timeline[experiments[exp][0][2]].get_next_empty(0)
    try:
        create_checkpoint(equipments_timeline[experiments[exp][0]],movement_timeline,True)
    except:
        equipments_timeline[experiments[exp][0]] = TimeHashMap()
    for equip in experiments[exp]:
        while True:
            try:
                create_checkpoint(equipments_timeline[equip],movement_timeline)
                time = move_from_to(time, prev_equip, equip, movement_timeline)+1
                time_required = usage_dict[equip[0]] + time
                equipments_timeline[equip].input_time_interval(time, time_required,exp)
                time = time_required+1
                prev_equip = equip
                break
            except:
                restore_checkpoint(equipments_timeline[equip],movement_timeline)
                gamma[equip] = gamma.get(equip,1) + 1/usage_dict[equip[0]]
                # print(gamma)
                time=time+1
                
    if not first_exp_time:
        first_exp_time = time
        # print("Only first: ", first_exp_time)
        first_time.append(first_exp_time)
    return equipments_timeline, movement_timeline

def CPF(experiments):
    time=0
    equipments_timeline={}
    movement_timeline={}
    global first_exp_time
    global gamma
    global total_time
    first_exp_time = 0

    most_used_experiments = calculate_critical(experiments)

    unique_equipment_list = list({equipment for equipments in experiments.values() for equipment in equipments})

    for equip in unique_equipment_list:
        if equip not in equipments_timeline:
            equipments_timeline[equip] = TimeHashMap()
        if equip[2] not in movement_timeline:
            movement_timeline[equip[2]] = RobotMovementTimeHashMap() # Done

    for exp in most_used_experiments:
        equipments_timeline,movement_timeline = do_experiment(experiments, equipments_timeline,movement_timeline,0,exp)

    sets = []
    labels = []
    for exp,time in equipments_timeline.items():
        sets.append(time)
        labels.append(exp)
    for exp,time in movement_timeline.items():
        sets.append(time)
        labels.append("R_workcell_"+str(exp))
    maxtime = 0
    for equip in unique_equipment_list:
        input_dict = equipments_timeline[equip].get_intervals()
        for _,end,_ in input_dict:
            if end>maxtime:
                maxtime=end
    # plot_all_timelines(sets,labels)
    # print(maxtime)
    total_time.append(maxtime)
    difference = maxtime-first_exp_time
    return maxtime, sets, difference

def plot_graph():
    global total_time
    global first_time

    plt.plot(total_time, label="Total time")
    plt.plot(first_time, label="First exp end time")

    plt.title("Title")
    plt.xlabel("Iteration")
    plt.ylabel("time")
    plt.legend()

    plt.grid(True)
    plt.show()


# experiments = path
experiments = {"exp1": ["D", "A", "C", "A", "C", "A", "C", "B", "C", "B", "D", "C", "D"], "exp2": ["A", "D", "C", "D", "B", "D", "A", "B", "C", "D", "C", "A"], "exp3": ["D", "A", "B", "D", "B", "C", "B", "C", "D", "B", "D", "C", "B"], "exp4": ["C", "B", "C", "B", "C", "B", "A", "B", "D", "C", "A", "D", "A"], "exp5": ["B", "D", "A", "C", "D", "B", "D", "A", "D", "C", "B", "A", "C"], "exp6": ["A", "D", "B", "C", "D", "C", "D", "A", "D", "A", "B", "D", "B"], "exp7": ["C", "D", "A", "D", "A", "C", "D", "C", "A", "B", "C", "B", "C"], "exp8": ["B", "C", "B", "C", "D", "A", "C", "D", "C", "B", "D", "C"], "exp9": ["B", "A", "B", "D", "B", "D", "B", "A", "C", "A", "C", "A", "B"], "exp10": ["D", "B", "D", "B", "C", "D", "A", "D", "B", "A", "D", "B"], "exp11": ["B", "A", "B", "A", "D", "A", "B", "D", "C", "D", "C", "B", "C"], "exp12": ["A", "D", "B", "D", "A", "C", "D", "C", "A", "B", "C", "A", "C"]}
total_time = []
first_time = []
right = 0
sum = 0
iteration = 10
# experiments = generate_random_experiments(6)
# print(experiments)
min_time = math.inf
shortest = ""
for _ in range(iteration):
    # print(experiments)
    gamma = {}
    shortest_path, gamma = binding(experiments, gamma)
    time,_, diff = CPF(shortest_path)
    if min_time>time:
        min_time = time
print(min_time)
# plot_graph()
