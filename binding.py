import networkx as nx
import csv
import pandas as pd
import json
import matplotlib.pyplot as plt

def load_workcell_distance(csv_file):
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        workcells = next(reader)[1:] 
        workcell_distance = {}
        for row in reader:
            from_workcell = row[0]
            times = list(map(float, row[1:]))
            workcell_distance[from_workcell] = {workcells[i]: times[i] for i in range(len(workcells))}
    return workcell_distance

def parse_node(node):
    instrument, workcell, distance_from_t, _ = node.split('-')
    return instrument, workcell, int(distance_from_t)

def calculate_movement_time(node1, node2):
    global delta
    _, workcell1, dist1 = parse_node(node1)
    _, workcell2, dist2 = parse_node(node2)
    result = 0
    node = '-'.join(node2.split('-')[:-1])
    if workcell1 == workcell2:
        result = abs(dist1 - dist2) * delta[node]
    else:
        move_to_t_1 = dist1
        move_to_t_2 = dist2
        transition_time = workcell_distance["workcell_"+workcell1]["workcell_"+workcell2]
        result = (move_to_t_1 + transition_time + move_to_t_2) * delta[node]
    return result

def create_graph(layers):
    G = nx.DiGraph()
    
    for layer in range(0, len(layers)-1):
        current_layer_nodes = layers[layer]
        next_layer_nodes = layers[layer + 1]
        
        for node1 in current_layer_nodes:
            for node2 in next_layer_nodes:
                movement_time = calculate_movement_time(node1, node2)
                G.add_edge(node1, node2, weight=movement_time)
    return G

def get_shortest_path(layers):
    
    G = create_graph(layers)
    
    start_node = "start"
    end_node = "end"

    for node in layers[0]:
        G.add_edge(start_node, node, weight=0)
    
    last_layer = len(layers)-1
    for node in layers[last_layer]:
        G.add_edge(node, end_node, weight=0)

    shortest_path = nx.dijkstra_path(G, source=start_node, target=end_node)

    shortest_path = shortest_path[1:-1]
    shortest_path = ['-'.join(s.split('-')[:-1]) for s in shortest_path]

    update_gamma(shortest_path)

    return shortest_path

def get_criticality(experiments):
    critical = {}
    for key,value in experiments.items():
        for v in value:
            try:
                critical[key]+=v
            except:
                critical[key]=v
    sorted_keys = [k for k, v in sorted(critical.items(), key=lambda item: item[1])]
    return sorted_keys

def get_layers(experiment):
    result = {}
    layers = []
    instruments = list(set(experiment))
    for target_letter in instruments:
        for workcell, letters in workcells.items():
            workcell_num = workcell.split("_")[-1]
            for idx, letter in enumerate(letters):
                if letter == target_letter:
                    try:
                        result[target_letter].append(f"{target_letter}-{workcell_num}-{idx}")
                    except:   
                        result[target_letter] = [f"{target_letter}-{workcell_num}-{idx}"]
    for i in range(len(experiment)):
        exp = experiment[i]
        temp=[]
        for l in result[exp]:
            temp.append(l+"-"+str(i))
        layers.append(temp)
    return layers

def calculate_delta(layers):
    global delta
    global gamma
    new_delta = {}
    alpha = 0.2
    for layer in layers:
        for inst in layer:
            instrument = '-'.join(inst.split('-')[:-1])
            if instrument not in new_delta:
                new_delta[instrument] = alpha*delta.get(instrument,1)+(1-alpha)*gamma.get(instrument,1)
    delta = new_delta

def update_gamma(path):
    global gamma
    new_gamma = {}
    for node in path:
        new_gamma[node] = gamma.get(node,1)+1
    gamma.update(new_gamma)

def binding(experiments, _gamma = {}):
    criticality = get_criticality(experiments)
    path = {}
    gamma = _gamma
    for exp in criticality:
        layers = get_layers(experiments[exp])
        calculate_delta(layers)
        path[exp] = get_shortest_path(layers)
        # path[exp] = path[exp][1:-1]
        # path[exp] = ['-'.join(s.split('-')[:-1]) for s in path[exp]]
    return path, gamma


delta = {}
gamma = {}

# Inputs

workcell_distance_file = './Submission/distance_times.csv'
workcell_distance = load_workcell_distance(workcell_distance_file)

instruments_df = pd.read_csv('./Submission/useTime.csv', index_col=0)
instrument_times = instruments_df.to_dict(orient="index")

with open('./Submission/equipments.json') as f:
    workcells = json.load(f)

# experiments = {
#         "exp1": ["A", "B", "C", "D", "E", "F", "D", "E", "F", "A", "B", "C", "D", "E", "F"],
#         "exp2": ["D", "E", "F", "A", "B", "C", "D", "E", "F"],
#         "exp3": ["A", "B", "C", "D", "E", "F", "D", "E", "F"],
#         "exp4": ["D", "E", "F", "A", "B", "C", "D"],
#         "exp5": ["A", "B", "C", "D", "E", "F", "D", "E", "F", "A"],
#         "exp6": ["B", "C", "D", "E", "F", "A", "B"],
#         "exp7": ["D", "E", "F", "A", "B", "C", "D", "E", "F"],
#         "exp8": ["A", "B", "C", "D", "E", "F"],
#         "exp9": ["D", "E", "F", "A", "B", "C", "D"],
#         "exp10": ["A", "B", "C", "D", "E", "F", "D", "E", "F"]
#     }

# path = binding(experiments)
# print("Shortest path:", path)
