import streamlit as st
import pandas as pd
from ai.model import AIManager
from simulation.env import run_simulation
from dashboard.ui import setup_sidebar, display_main_dashboard
from dashboard.kpi import calculate_kpis

st.set_page_config(page_title="AI Train Traffic Control", page_icon="🚄", layout="wide")

st.title("🚄 AI-Powered Train Traffic Control Simulator")
st.markdown("Use the controls on the left to configure and run a simulation. The full results will be displayed once the simulation is complete.")

@st.cache_resource
def get_ai_manager(platforms_b):
    ai_manager = AIManager(n_platforms_b=platforms_b)
    ai_manager.train_models()
    return ai_manager

def main():
    config, run_button = setup_sidebar()
    ai_manager = get_ai_manager(config['platforms_b'])

    if 'simulation_results' not in st.session_state:
        st.session_state.simulation_results = None
    
    progress_placeholder = st.empty()
    results_placeholder = st.empty()

    if run_button:
        st.session_state.simulation_results = None
        
        with progress_placeholder.container():
            with st.spinner('Running full simulation... this may take a moment.'):
                st.write("Running Baseline (Non-AI) Simulation...")
                non_ai_progress = st.progress(0)
                config_non_ai = {**config, 'is_ai_controlled': False, 'ai_manager': None}
                log_df_non_ai, _, _ = run_simulation(config_non_ai, non_ai_progress)
                
                st.write("Running Optimized (AI) Simulation...")
                ai_progress = st.progress(0)
                config_ai = {**config, 'is_ai_controlled': True, 'ai_manager': ai_manager}
                log_df_ai, alerts_ai, controller_ai = run_simulation(config_ai, ai_progress)

        with st.spinner("Calculating KPIs and generating reports..."):
            # CORRECTED: Added the missing config['platforms_b'] argument to both calls
            kpis_non_ai = calculate_kpis(log_df_non_ai, config['num_trains'], 24, config['platforms_b'])
            kpis_ai = calculate_kpis(log_df_ai, config['num_trains'], 24, config['platforms_b'])
            
            st.session_state.simulation_results = {
                "non_ai": {"logs": log_df_non_ai, "kpis": kpis_non_ai},
                "ai": {
                    "logs": log_df_ai, "kpis": kpis_ai, 
                    "alerts": alerts_ai,
                    "decisions": controller_ai.decision_logs
                }
            }
        
        progress_placeholder.empty()
        st.success("✅ Simulation Complete! View the results below.")
    
    if st.session_state.simulation_results:
        with results_placeholder.container():
             display_main_dashboard(st.session_state.simulation_results, config)
    else:
        st.info("ℹ️ Set your parameters and click 'Run Simulation' to begin.")

if __name__ == "__main__":
    main()