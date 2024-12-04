from scheduling import TimeHashMap, RobotMovementTimeHashMap, CPF

equipmentTimelines, movementTimeline = CPF()

# Workcell distances (movement time between them)
workcell_distances = {
    ("workcell_1", "workcell_2"): 5,
    ("workcell_1", "workcell_3"): 10,
    ("workcell_2", "workcell_3"): 5,
    ("workcell_4", "workcell_5"): 5,
    ("workcell_4", "workcell_6"): 10,
    ("workcell_5", "workcell_6"): 5,
    ("workcell_1", "workcell_4"): 15,  # Moving between lines
    ("workcell_2", "workcell_5"): 15,
    ("workcell_3", "workcell_6"): 15
}

def move_robot(bot_id, from_wc, to_wc, start_time):
    """
    Simulates the movement of a robot from one workcell to another, checking for collisions.
    """
    # Get the movement time between workcells
    move_time = workcell_distances.get((from_wc, to_wc), workcell_distances.get((to_wc, from_wc), None))
    if move_time is None:
        raise ValueError(f"No known distance between {from_wc} and {to_wc}")
    
    end_time = start_time + move_time
    
    # Check for collision with another robot moving in the same line (workcell 1,2,3 or workcell 4,5,6)
    for other_bot, timeline in robot_timelines.items():
        if other_bot == bot_id:
            continue  # Skip checking the same robot
        
        # Get the timeline of other bots
        other_intervals = timeline.get_intervals()
        
        for (other_start, other_end, label) in other_intervals:
            other_from, other_to = label
            
            # If both robots are moving in the same line, check for collision
            if in_same_line(from_wc, to_wc) and in_same_line(other_from, other_to):
                if not (end_time <= other_start or start_time >= other_end):
                    print(f"Collision detected between {bot_id} and {other_bot} from {start_time} to {end_time}")
                    return False
    
    # If no collision, update the robot's timeline
    robot_timelines[bot_id].input_time_interval(start_time, end_time, (from_wc, to_wc))
    print(f"{bot_id} moved from {from_wc} to {to_wc} from {start_time} to {end_time}")
    return True

def in_same_line(wc1, wc2):
    """Check if two workcells are on the same line."""
    line_1 = {"workcell_1", "workcell_2", "workcell_3"}
    line_2 = {"workcell_4", "workcell_5", "workcell_6"}
    
    return (wc1 in line_1 and wc2 in line_1) or (wc1 in line_2 and wc2 in line_2)

def plan_robot_movements():
    """Plan movements for the robots."""
    # Example movement plan
    start_time_bot_1 = 0
    move_robot("bot_1", "workcell_1", "workcell_2", start_time_bot_1)
    
    start_time_bot_2 = 5
    move_robot("bot_2", "workcell_4", "workcell_5", start_time_bot_2)
    
    # More robot movements can be planned as needed

# Plan the movements
plan_robot_movements()
