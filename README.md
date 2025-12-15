# Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control

This project is a discrete-event simulation built with `simpy` and `streamlit` to demonstrate how an AI-powered controller can improve railway throughput, punctuality, and delay management compared to a standard rule-based system.

## 🎯 Features

-   **Dual Simulation**: Runs two parallel simulations (AI vs. Non-AI) for direct comparison.
-   **AI-Powered Control**: Uses mock `scikit-learn` models to predict delays and intelligently allocate platforms.
-   **Interactive Dashboard**: A `streamlit` GUI to control simulation parameters and visualize results.
-   **KPI Analysis**: Real-time metrics on punctuality, average delay, throughput, and platform utilization.
-   **Scenario Modeling**: Includes a "Disaster Mode" and "What-If" analysis to test system resilience.
-   **Modular Architecture**: Code is organized into distinct modules for simulation, AI, and dashboard logic.

## 🛠 Project Structure
