import pandas as pd

def generate_train_summary_df(log_df, config):
    """Calculates detailed stats for each train and returns a styled DataFrame."""
    if log_df.empty:
        return pd.DataFrame()

    summary_data = []
    base_travel_time = 110 # 60 mins A->B + 50 mins B->C

    for train_id in sorted(log_df['train_id'].unique()):
        train_logs = log_df[log_df['train_id'] == train_id].sort_values('time')
        
        if train_logs.empty:
            continue

        start_time = train_logs.iloc[0]['time']
        end_log = train_logs[train_logs['event'] == 'arrive_final']
        
        if end_log.empty:
            # Train did not finish, provide partial data
            total_time = log_df['time'].max() - start_time
            delay = None
            wait_time_b = None
        else:
            end_time = end_log.iloc[0]['time']
            total_time = end_time - start_time
            
            # Calculate delay
            stop_at_b_log = train_logs[train_logs['event'] == 'at_platform']
            scheduled_stop_b = 0
            if not stop_at_b_log.empty:
                # Infer scheduled stop from a few options
                possible_stops = [5, 10, 15]
                depart_b_log = train_logs[train_logs['event'] == 'depart_station']
                if not depart_b_log.empty:
                    actual_duration = depart_b_log.iloc[0]['time'] - stop_at_b_log.iloc[0]['time']
                    scheduled_stop_b = min(possible_stops, key=lambda x:abs(x-actual_duration))

            scheduled_arrival = start_time + base_travel_time + scheduled_stop_b
            delay = max(0, end_time - scheduled_arrival)

            # Calculate wait time for platform B
            wait_time_b = 0
            arrive_station_b_log = train_logs[train_logs['event'] == 'arrive_station']
            if not arrive_station_b_log.empty and not stop_at_b_log.empty:
                wait_time_b = stop_at_b_log.iloc[0]['time'] - arrive_station_b_log.iloc[0]['time']

        summary_data.append({
            "Train ID": train_id,
            "Total Time (min)": f"{total_time:.1f}",
            "Delay (min)": f"{delay:.1f}" if delay is not None else "N/A",
            "Wait for Platform B (min)": f"{wait_time_b:.1f}" if wait_time_b is not None else "N/A"
        })

    summary_df = pd.DataFrame(summary_data)
    
    # Styling the DataFrame
    styled_df = summary_df.style.map(
        lambda val: 'color: red;' if pd.to_numeric(val, errors='coerce') > 0 else '', 
        subset=['Delay (min)', 'Wait for Platform B (min)']
    ).format(precision=1).set_properties(**{'text-align': 'center'})
    
    return styled_df