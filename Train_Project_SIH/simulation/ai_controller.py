from ai.features import extract_features
import random

class AIController:
    def __init__(self, env, stations, blocks, ai_manager, disaster_mode):
        self.env = env
        self.stations = stations
        self.blocks = blocks
        self.ai_manager = ai_manager
        self.disaster_mode = disaster_mode
        self.platform_allocations = {}
        self.alerts = []
        self.decision_logs = []

    def get_drive_mode(self, train):
        """Asks the AI model for the best drive mode and logs the decision."""
        features_df = extract_features(self.env, self.stations, self.blocks, train, self.disaster_mode)
        mode_code = self.ai_manager.predict_drive_mode(features_df)
        drive_mode = "Eco-Coast" if mode_code == 2 else "Full Speed"
        
        if drive_mode == "Eco-Coast":
            reason = "AI predicts upcoming congestion; switching to Eco-Coast to save energy."
            data_used = {
                'Trains at B': features_df['num_trains_at_station_B'].iloc[0],
                'Downstream Free': 'Yes' if features_df['downstream_block_free'].iloc[0] == 1 else 'No'
            }
            self.decision_logs.append({
                "time": self.env.now, "train_id": train.train_id,
                "action": "Switched to Eco-Coast mode", "reason": reason,
                "type": "Energy", "data_used": data_used
            })
        return drive_mode

    def request_platform(self, train, station_name):
        def _get_platform_process():
            features_df = extract_features(self.env, self.stations, self.blocks, train, self.disaster_mode)
            predicted_delay = self.ai_manager.predict_delay(features_df)
            predicted_platform = self.ai_manager.predict_platform(features_df)
            
            data_used = {
                'Trains at B': features_df['num_trains_at_station_B'].iloc[0],
                'Downstream Free': 'Yes' if features_df['downstream_block_free'].iloc[0] == 1 else 'No',
                'Predicted Delay': f"{predicted_delay:.1f} min"
            }

            if predicted_delay > 15 and train.priority == 2:
                hold_time = random.uniform(1, 5)
                action = f"Held Local train for {hold_time:.1f} min"
                reason = f"High predicted delay and downstream congestion detected."
                self.alerts.append(f"⚠️ AI Intervention: {train.train_id} ({action}) to ease congestion.")
                self.decision_logs.append({"time": self.env.now, "train_id": train.train_id, "action": action, "reason": reason, "type": "Intervention", "data_used": data_used})
                yield self.env.timeout(hold_time)

            action = f"Assigned to Platform {predicted_platform}"
            reason = f"AI model chose Platform {predicted_platform} as optimal for this Local train, considering current station and track occupancy."
            self.alerts.append(f"✅ AI Decision: {train.train_id} -> P{predicted_platform} @ {station_name}")
            self.decision_logs.append({"time": self.env.now, "train_id": train.train_id, "action": action, "reason": reason, "type": "Allocation", "data_used": data_used})

            req = self.stations[station_name].platforms.request()
            self.platform_allocations[train.train_id] = (req, predicted_platform)
            yield req
            return predicted_platform
        
        return self.env.process(_get_platform_process())
        
    def request_pass_through(self, train, station_name):
        def _pass_through_process():
            features_df = extract_features(self.env, self.stations, self.blocks, train, self.disaster_mode)
            num_at_b = features_df['num_trains_at_station_B'].iloc[0]
            downstream_free = features_df['downstream_block_free'].iloc[0]

            data_used = {
                'Trains at B': num_at_b,
                'Downstream Free': 'Yes' if downstream_free == 1 else 'No'
            }

            if num_at_b >= self.stations[station_name].platforms.capacity or not downstream_free:
                wait_time = random.uniform(2, 6)
                action = f"Held Express train for {wait_time:.1f} min"
                reason = "Station B is congested or downstream block is occupied. Holding to prevent gridlock."
                self.alerts.append(f"⚠️ AI Intervention: {train.train_id} ({action}).")
                self.decision_logs.append({"time": self.env.now, "train_id": train.train_id, "action": action, "reason": reason, "type": "Intervention", "data_used": data_used})
                yield self.env.timeout(wait_time)
            else:
                action = "Cleared for direct pass-through"
                reason = "Station B and downstream track are clear, prioritizing Express train."
                self.decision_logs.append({"time": self.env.now, "train_id": train.train_id, "action": action, "reason": reason, "type": "Allocation", "data_used": data_used})
                yield self.env.timeout(2)

        return self.env.process(_pass_through_process())

    # request_block, release_block, and release_platform remain the same
    def request_block(self, train_id, block_name):
        return self.blocks[block_name].request()

    def release_block(self, block_name):
        if self.blocks[block_name].users:
            self.blocks[block_name].release(self.blocks[block_name].users[0])

    def release_platform(self, train, station_name, platform_id):
        station = self.stations[station_name]
        if train.train_id in self.platform_allocations:
            req, _ = self.platform_allocations[train.train_id]
            station.platforms.release(req)
            del self.platform_allocations[train.train_id]