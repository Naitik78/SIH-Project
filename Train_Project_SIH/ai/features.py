import pandas as pd

def extract_features(sim_env, stations, blocks, train, disaster_mode):
    """Extracts features for a given train from the simulation environment."""
    
    current_time = sim_env.now
    time_of_day = (current_time // 60) % 24
    day_of_week = (current_time // (60 * 24)) % 7

    num_trains_at_station_A = len(stations['A'].platforms.users)
    num_trains_at_station_B = len(stations['B'].platforms.users)
    
    # This logic generates the two missing features
    downstream_block_free = 1 if blocks['Block_B_C'].count == 0 else 0
    train_priority = train.priority

    feature_dict = {
        'time_of_day': [time_of_day],
        'day_of_week': [day_of_week],
        'num_trains_at_station_A': [num_trains_at_station_A],
        'num_trains_at_station_B': [num_trains_at_station_B],
        'stop_duration_B': [train.scheduled_stop_duration_b],
        'train_priority': [train_priority],
        'downstream_block_free': [downstream_block_free],
        'is_disaster_mode': [1 if disaster_mode else 0]
    }
    
    return pd.DataFrame(feature_dict)