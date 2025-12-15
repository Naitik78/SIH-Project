import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def create_comparison_bar_chart(kpi_data_ai, kpi_data_non_ai, kpi_name):
    """Creates a bar chart comparing a single KPI for AI vs Non-AI."""
    fig = go.Figure(data=[
        go.Bar(name='Non-AI', x=[kpi_name], y=[kpi_data_non_ai[kpi_name]], marker_color='#636EFA'),
        go.Bar(name='AI', x=[kpi_name], y=[kpi_data_ai[kpi_name]], marker_color='#EF553B')
    ])
    fig.update_layout(
        title_text=f'{kpi_name} Comparison',
        yaxis_title="Value",
        barmode='group',
        legend_title="Control Type",
        margin=dict(l=20, r=20, t=40, b=20),
        height=300
    )
    return fig

def create_delay_line_chart(log_df_ai, log_df_non_ai):
    """Creates a line chart showing cumulative delays over time."""
    def get_cumulative_delay(log_df):
        delays = []
        base_travel_time = 110
        for train_id in sorted(log_df['train_id'].unique()):
            train_logs = log_df[log_df['train_id'] == train_id]
            final_arrival = train_logs[train_logs['event'] == 'arrive_final']
            if not final_arrival.empty:
                actual_arrival_time = final_arrival.iloc[0]['time']
                departure_time = train_logs.iloc[0]['time']
                # Simplified schedule for graphing
                stop_at_b = not train_logs[train_logs['event'] == 'at_platform'].empty
                stop_duration = 10 if stop_at_b else 0 # Assume avg stop for schedule
                scheduled_arrival = departure_time + base_travel_time + stop_duration
                delay = max(0, actual_arrival_time - scheduled_arrival)
                delays.append({'time': actual_arrival_time, 'delay': delay})
        if not delays:
            return pd.DataFrame(columns=['time', 'cumulative_delay'])
            
        delay_df = pd.DataFrame(delays).sort_values('time')
        delay_df['cumulative_delay'] = delay_df['delay'].cumsum()
        return delay_df

    delay_ai = get_cumulative_delay(log_df_ai)
    delay_non_ai = get_cumulative_delay(log_df_non_ai)
    
    fig = go.Figure()
    if not delay_non_ai.empty:
        fig.add_trace(go.Scatter(x=delay_non_ai['time'], y=delay_non_ai['cumulative_delay'],
                             mode='lines+markers', name='Non-AI', line=dict(color='#636EFA')))
    if not delay_ai.empty:
        fig.add_trace(go.Scatter(x=delay_ai['time'], y=delay_ai['cumulative_delay'],
                             mode='lines+markers', name='AI', line=dict(color='#EF553B')))

    fig.update_layout(
        title_text='Cumulative Delay Over Time',
        xaxis_title='Simulation Time (minutes)',
        yaxis_title='Total Cumulative Delay (minutes)',
        legend_title="Control Type",
        margin=dict(l=20, r=20, t=40, b=20),
        height=350
    )
    return fig

def create_train_animation(log_df):
    """
    Creates a robust Gantt chart by explicitly finding start and end events for major activities.
    """
    if log_df.empty:
        return go.Figure().update_layout(title="No train data to display", height=300)

    gantt_data = []
    # Loop through each train and build its activity timeline
    for train_id in sorted(log_df['train_id'].unique()):
        train_logs = log_df[log_df['train_id'] == train_id].sort_values(by='time')

        # --- Activity 1: Traveling on Track A -> B ---
        start_ab_log = train_logs[train_logs['details'] == 'Traveling from A to B']
        end_ab_log = train_logs[train_logs['details'] == 'Finished travel to B']
        if not start_ab_log.empty and not end_ab_log.empty:
            gantt_data.append(dict(
                Task="Track A-B", 
                Start=start_ab_log.iloc[0]['time'], 
                Finish=end_ab_log.iloc[0]['time'], 
                Resource=train_id
            ))

        # --- Activity 2: Waiting at Station B Platform ---
        start_b_log = train_logs[train_logs['event'] == 'at_platform']
        end_b_log = train_logs[train_logs['event'] == 'depart_station']
        if not start_b_log.empty and not end_b_log.empty:
            gantt_data.append(dict(
                Task="Station B", 
                Start=start_b_log.iloc[0]['time'], 
                Finish=end_b_log.iloc[0]['time'], 
                Resource=train_id
            ))
        
        # --- Activity 3: Traveling on Track B -> C ---
        start_bc_log = train_logs[train_logs['details'] == 'Traveling from B to C']
        end_bc_log = train_logs[train_logs['details'] == 'Finished travel to C']
        if not start_bc_log.empty and not end_bc_log.empty:
            gantt_data.append(dict(
                Task="Track B-C", 
                Start=start_bc_log.iloc[0]['time'], 
                Finish=end_bc_log.iloc[0]['time'], 
                Resource=train_id
            ))
            
    if not gantt_data:
        return go.Figure().update_layout(title="Not enough simulation events to build timeline.", height=300)

    df = pd.DataFrame(gantt_data)
    fig = px.timeline(
        df, x_start="Start", x_end="Finish", y="Resource", color="Task",
        title="Train Movement Timeline (Gantt Chart)",
        color_discrete_map={
            "Track A-B": "royalblue",
            "Station B": "firebrick",
            "Track B-C": "seagreen"
        }
    )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        xaxis_title="Simulation Time (minutes)",
        yaxis_title="Train ID",
        legend_title="Location/Activity",
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
    )
    return fig