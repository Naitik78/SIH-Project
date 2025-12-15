import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import os

class AIManager:
    def __init__(self, historical_data_path='data/historical.csv', n_platforms_b=3):
        self.data_path = historical_data_path
        self.delay_model = None
        self.platform_model = None
        self.drive_mode_model = None # New model for energy efficiency
        self.n_platforms_b = n_platforms_b
        self.is_trained = False

    def train_models(self):
        if not os.path.exists(self.data_path):
            return

        df = pd.read_csv(self.data_path)
        
        features = [
            'time_of_day', 'day_of_week', 'num_trains_at_station_A', 
            'num_trains_at_station_B', 'stop_duration_B', 'train_priority',
            'downstream_block_free', 'is_disaster_mode'
        ]
        X = df[features]

        # Train Delay Model
        y_delay = df['delay_minutes']
        self.delay_model = Pipeline([('scaler', StandardScaler()), ('regressor', RandomForestRegressor(n_estimators=50, random_state=42))])
        self.delay_model.fit(X, y_delay)

        # Train Platform Model
        platform_data = df[df['assigned_platform_B'] > 0]
        if not platform_data.empty:
            self.platform_model = Pipeline([('scaler', StandardScaler()), ('classifier', RandomForestClassifier(n_estimators=50, random_state=42))])
            self.platform_model.fit(platform_data[features], platform_data['assigned_platform_B'])
        
        # NEW: Train Drive Mode Model
        y_drive_mode = df['optimal_drive_mode']
        self.drive_mode_model = Pipeline([('scaler', StandardScaler()), ('classifier', RandomForestClassifier(n_estimators=50, random_state=42))])
        self.drive_mode_model.fit(X, y_drive_mode)
        
        self.is_trained = True
        print("✅ AI models (including new Drive Mode model) trained successfully.")

    def predict_delay(self, features_df):
        if not self.is_trained: return 2
        return max(0, self.delay_model.predict(features_df)[0])

    def predict_platform(self, features_df):
        if not self.is_trained or self.platform_model is None: return 1
        prediction = self.platform_model.predict(features_df)
        return int(max(1, min(prediction[0], self.n_platforms_b)))

    def predict_drive_mode(self, features_df):
        """Predicts the optimal drive mode (1=Full Speed, 2=Eco-Coast)."""
        if not self.is_trained: return 1 # Default to Full Speed
        return self.drive_mode_model.predict(features_df)[0]