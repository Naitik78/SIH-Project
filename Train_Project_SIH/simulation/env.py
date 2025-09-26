import simpy
import random
import pandas as pd
from simulation.station import Station
from simulation.train import Train
from simulation.controller import NonAIController
from simulation.ai_controller import AIController

def setup_simulation_environment(config, trains_in_sim):
    env = simpy.Environment()
    
    stations = {
        'A': Station(env, 'A', config['platforms_a']),
        'B': Station(env, 'B', config['platforms_b']),
        'C': Station(env, 'C', config['platforms_c'])
    }
    
    blocks = {
        'Block_A_B': simpy.Resource(env, capacity=1),
        'Block_B_C': simpy.Resource(env, capacity=1)
    }
    
    if config['is_ai_controlled']:
        controller = AIController(env, stations, blocks, config['ai_manager'], config['disaster_mode'])
    else:
        controller = NonAIController(env, stations, blocks)
        
    env.process(generate_trains(env, controller, config, trains_in_sim))
    
    return env, controller

def generate_trains(env, controller, config, trains_in_sim):
    train_count = 0
    stops_template = {
        'A': {'name': 'A'},
        'B': {'name': 'B', 'travel_time_from_prev': 60},
        'C': {'name': 'C', 'travel_time_from_prev': 50}
    }

    for i in range(config['num_trains']):
        train_count += 1
        train_id = f"T{train_count:02d}"
        stop_duration_b = random.choice([0, 5, 10, 15]) if config['num_trains'] > 1 else 10
        stops = stops_template.copy()
        stops['B']['stop_duration'] = stop_duration_b
        
        initial_delay = 0
        if config['what_if_train'] == train_id:
            initial_delay = config['what_if_delay']
        
        trains_in_sim.append(Train(env, train_id, controller, stops, initial_delay))
        
        if not config['disaster_mode']:
            yield env.timeout(random.uniform(5, 20))

def run_simulation(config, progress_bar, stop_time=1440):
    trains_in_sim = []
    env, controller = setup_simulation_environment(config, trains_in_sim)
    
    for t in range(1, stop_time + 1):
        env.run(until=t)
        if t % 10 == 0:
             progress_bar.progress(t / stop_time)

    progress_bar.progress(1.0)

    all_logs = [log for train in trains_in_sim for log in train.log]
    log_df = pd.DataFrame(all_logs)
    
    alerts = []
    if isinstance(controller, AIController):
        alerts = controller.alerts

    # Return the controller object along with logs and alerts
    return log_df, alerts, controller