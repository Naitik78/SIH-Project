import pandas as pd
import numpy as np

def calculate_kpis(log_df, num_trains, simulation_duration_hours, num_platforms_b):
    if log_df.empty:
        return {"Punctuality": 0, "Average Delay": 0, "Throughput": 0, "Platform B Utilization": 0, "Total Energy": 0, "Max Delay": 0}

    # Energy KPI
    energy_logs = log_df[log_df['event'] == 'final_energy']
    total_energy = energy_logs['details'].str.extract(r'(\d+)').astype(float).sum().iloc[0] if not energy_logs.empty else 0

    # Throughput
    final_arrivals = log_df[log_df['event'] == 'arrive_final']
    actual_simulation_end_time = log_df['time'].max()
    actual_duration_hours = actual_simulation_end_time / 60 if pd.notna(actual_simulation_end_time) and actual_simulation_end_time > 0 else simulation_duration_hours
    
    throughput = round(len(final_arrivals) / actual_duration_hours, 2) if actual_duration_hours > 0 else 0

    # Delay, Punctuality, and Max Delay Calculation
    total_delay, punctual_trains = 0, 0
    all_train_delays = []
    base_travel_time = 110 # A->B (60) + B->C (50)
    unique_train_ids = log_df['train_id'].unique()
    
    platform_b_occupied_time = 0
    
    for train_id in unique_train_ids:
        train_logs = log_df[log_df['train_id'] == train_id].sort_values(by='time')
        
        depart_a_time = train_logs[train_logs['event'] == 'depart']['time'].min()
        arrive_c_time = train_logs[train_logs['event'] == 'arrive_final']['time'].max()
        
        if pd.notna(depart_a_time) and pd.notna(arrive_c_time):
            actual_total_journey_time = arrive_c_time - depart_a_time
            
            scheduled_stop_duration_b = 0
            if not train_logs[train_logs['event'] == 'at_platform'].empty:
                 scheduled_stop_duration_b = 10

            scheduled_journey_time = base_travel_time + scheduled_stop_duration_b
            delay = max(0, actual_total_journey_time - scheduled_journey_time)
            all_train_delays.append(delay)
            total_delay += delay
            if delay <= 10: 
                punctual_trains += 1
        
        platform_b_entry_time = train_logs[train_logs['event'] == 'at_platform']['time'].min()
        platform_b_exit_time = train_logs[train_logs['event'] == 'depart_station']['time'].min()
        
        if pd.notna(platform_b_entry_time) and pd.notna(platform_b_exit_time):
            platform_b_occupied_time += (platform_b_exit_time - platform_b_entry_time)

    avg_delay = round(total_delay / len(unique_train_ids), 1) if unique_train_ids.any() else 0
    punctuality = round((punctual_trains / num_trains) * 100, 1) if num_trains > 0 else 0
    max_delay = round(max(all_train_delays), 1) if all_train_delays else 0

    total_available_platform_time = actual_duration_hours * 60 * num_platforms_b
    platform_b_utilization = round((platform_b_occupied_time / total_available_platform_time) * 100, 1) if total_available_platform_time > 0 else 0

    return {
        "Punctuality": punctuality, 
        "Average Delay": avg_delay,
        "Throughput": throughput, 
        "Platform B Utilization": platform_b_utilization, 
        "Total Energy": total_energy,
        "Max Delay": max_delay
    }