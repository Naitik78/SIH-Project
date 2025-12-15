import streamlit as st
import pandas as pd
from dashboard import kpi, graphs, tables

def setup_sidebar():
    """Sets up the Streamlit sidebar with user controls and scenario presets."""
    st.sidebar.header("📋 Scenario Presets")
    st.sidebar.markdown("Click to load a scenario that tests each controller's strengths.")
    col1, col2 = st.sidebar.columns(2)

    if col1.button("📏 Favor Baseline", use_container_width=True, help="Low-conflict scenario where the baseline's simple FCFS rule is highly effective."):
        st.session_state.num_trains = 12
        st.session_state.platforms_a = 3
        st.session_state.platforms_b = 3
        st.session_state.platforms_c = 3
        st.session_state.disaster_mode = False
        st.session_state.what_if_enabled = False
        st.rerun()

    if col2.button("🧠 Showcase AI", use_container_width=True, help="High-congestion bottleneck designed to highlight the AI's ability to manage chaos."):
        st.session_state.num_trains = 40
        st.session_state.platforms_a = 2
        st.session_state.platforms_b = 1 # The critical bottleneck
        st.session_state.platforms_c = 2
        st.session_state.disaster_mode = True
        st.session_state.what_if_enabled = False
        st.rerun()

    st.sidebar.header("⚙️ Manual Controls")
    
    num_trains = st.sidebar.slider("Number of Trains", 2, 50, 15, key="num_trains")
    
    st.sidebar.subheader("Platforms")
    platforms_a = st.sidebar.slider("Station A Platforms", 1, 5, 2, key="platforms_a")
    platforms_b = st.sidebar.slider("Station B Platforms", 1, 5, 2, key="platforms_b")
    platforms_c = st.sidebar.slider("Station C Platforms", 1, 5, 2, key="platforms_c")
    
    st.sidebar.subheader("Scenarios")
    disaster_mode = st.sidebar.toggle("💥 Disaster Mode", key="disaster_mode", help="All trains depart at once.")
    
    st.sidebar.subheader("What-If Analysis")
    what_if_enabled = st.sidebar.toggle("Enable What-If", key="what_if_enabled")
    
    train_list = [f"T{i:02d}" for i in range(1, num_trains + 1)]
    
    what_if_train = st.sidebar.selectbox("Select Train to Delay", train_list, key="what_if_train", disabled=not what_if_enabled)
    what_if_delay = st.sidebar.slider("Inject Delay (minutes)", 0, 60, 10, key="what_if_delay", disabled=not what_if_enabled)

    if not what_if_enabled:
        what_if_train, what_if_delay = None, 0

    run_button = st.sidebar.button("🚀 Run Simulation", type="primary")
    
    config = {
        "num_trains": num_trains, "platforms_a": platforms_a, "platforms_b": platforms_b, "platforms_c": platforms_c,
        "disaster_mode": disaster_mode, "what_if_train": what_if_train, "what_if_delay": what_if_delay,
        "travel_time_ab": 60, "travel_time_bc": 50
    }
    return config, run_button

def display_kpi_dashboard(kpi_data, title):
    """Displays a set of KPIs in metric cards."""
    st.subheader(title)
    cols = st.columns(5)
    cols[0].metric("Avg Delay (min)", f"{kpi_data['Average Delay']:.1f}")
    cols[1].metric("⚡Total Energy", f"{kpi_data['Total Energy']:.0f}")
    cols[2].metric("Throughput (trains/hr)", f"{kpi_data['Throughput']:.1f}")
    cols[3].metric("Max Delay (min)", f"{kpi_data.get('Max Delay', 0):.1f}")
    
    if "Delay Reduction" in kpi_data:
        cols[4].metric("✅ Delay Reduction", f"{kpi_data.get('Delay Reduction', 0):.1f}%", help="The percentage reduction in average delay compared to the baseline.")
    else:
        cols[4].metric("✅ Delay Reduction", "N/A")


def display_main_dashboard(results, config):
    """The main function to render the dashboard layout after simulation."""
    log_df_non_ai = results['non_ai']['logs']
    log_df_ai = results['ai']['logs']
    alerts_ai = results['ai']['alerts']
    decisions = results['ai']['decisions']
    
    kpis_non_ai = kpi.calculate_kpis(log_df_non_ai, config['num_trains'], 24, config['platforms_b'])
    kpis_ai = kpi.calculate_kpis(log_df_ai, config['num_trains'], 24, config['platforms_b'])

    # --- NEW: EXECUTIVE SUMMARY SECTION ---
    st.header("🏆 Executive Summary")
    
    delay_reduction = 0
    if kpis_non_ai['Average Delay'] > 0:
        delay_reduction = ((kpis_non_ai['Average Delay'] - kpis_ai['Average Delay']) / kpis_non_ai['Average Delay']) * 100
    
    energy_saved = 0
    if kpis_non_ai['Total Energy'] > 0:
        energy_saved = ((kpis_non_ai['Total Energy'] - kpis_ai['Total Energy']) / kpis_non_ai['Total Energy']) * 100

    summary_cols = st.columns(3)
    summary_cols[0].metric("✅ Avg. Delay Reduction", f"{delay_reduction:.1f}%", delta_color="inverse")
    summary_cols[1].metric("⚡ Energy Saved", f"{energy_saved:.1f}%", delta_color="inverse")
    summary_cols[2].metric("📈 Throughput Change", f"{kpis_ai['Throughput'] - kpis_non_ai['Throughput']:.2f} trains/hr")
    st.markdown("---")


    # --- KPI Dashboards ---
    st.header("📊 Simulation Results")
    kpis_ai['Delay Reduction'] = delay_reduction # Add to dict for display

    col1, col2 = st.columns(2)
    with col1:
        display_kpi_dashboard(kpis_non_ai, "Baseline (Non-AI)")
    with col2:
        display_kpi_dashboard(kpis_ai, "Optimized (AI-Powered)")

    # --- (Performance Comparison, Alerts, etc. remain the same) ---
    st.markdown("---")
    st.header("📈 Performance Comparison")
    tab1, tab2, tab3, tab4 = st.tabs(["⚡ Energy", "Throughput", "Average Delay", "Max Delay"])
    # ... (graphing code remains the same)
    with tab1:
        st.plotly_chart(graphs.create_comparison_bar_chart(kpis_ai, kpis_non_ai, 'Total Energy'), use_container_width=True, key="energy_chart")
    with tab2:
        st.plotly_chart(graphs.create_comparison_bar_chart(kpis_ai, kpis_non_ai, 'Throughput'), use_container_width=True, key="throughput_chart")
    with tab3:
        st.plotly_chart(graphs.create_comparison_bar_chart(kpis_ai, kpis_non_ai, 'Average Delay'), use_container_width=True, key="delay_chart")
    with tab4:
        st.plotly_chart(graphs.create_comparison_bar_chart(kpis_ai, kpis_non_ai, 'Max Delay'), use_container_width=True, key="max_delay_chart")
        
    st.markdown("---")
    st.header("🤖 AI Interventions & Alerts")
    if alerts_ai:
        alerts_html = "".join([f"<p style='margin: 0; padding: 2px;'>{alert}</p>" for alert in alerts_ai[-15:]])
        st.markdown(f"<div style='height: 150px; overflow-y: scroll; border: 1px solid #ddd; border-radius: 5px; padding: 10px;'>{alerts_html}</div>", unsafe_allow_html=True)
    else:
        st.info("No AI interventions were recorded.")
    
    st.markdown("---")
    st.header("💡 Key AI Decisions & Reasoning")
    if not decisions:
        st.info("No major AI decisions were logged.")
    else:
        # Sort decisions by type to group them nicely
        sorted_decisions = sorted(decisions, key=lambda x: x.get('type', ''))
        
        for d in sorted_decisions:
            decision_type = d.get('type', 'General')
            color = {"Intervention": "orange", "Energy": "blue", "Allocation": "green"}.get(decision_type, "gray")

            with st.expander(f"**Time {d['time']:.0f}:** AI action for **{d['train_id']}**"):
                st.markdown(f"**Action:** <span style='color:{color}; font-weight:bold;'>{d['action']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Reasoning:** {d['reason']}")
                
                # --- NEW: Enhanced Explainable AI section ---
                if d.get('data_used'):
                    st.markdown("**Data Used for Decision:**")
                    data_str = " | ".join([f"**{key}:** {value}" for key, value in d['data_used'].items()])
                    st.markdown(f"> {data_str}")
    
    # --- NEW: EXPORT RESULTS SECTION ---
    st.markdown("---")
    st.header("📁 Download Simulation Logs")
    export_cols = st.columns(2)
    with export_cols[0]:
        st.download_button(
            label="Download Baseline Logs (.csv)",
            data=log_df_non_ai.to_csv(index=False).encode('utf-8'),
            file_name='baseline_simulation_logs.csv',
            mime='text/csv',
            use_container_width=True
        )
    with export_cols[1]:
        st.download_button(
            label="Download AI-Powered Logs (.csv)",
            data=log_df_ai.to_csv(index=False).encode('utf-8'),
            file_name='ai_simulation_logs.csv',
            mime='text/csv',
            use_container_width=True
        )