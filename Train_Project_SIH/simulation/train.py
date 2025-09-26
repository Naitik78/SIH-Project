import simpy

class Train:
    def __init__(self, env, train_id, controller, stops, initial_delay=0):
        self.env = env
        self.train_id = train_id
        self.controller = controller
        
        self.stops = stops
        self.scheduled_stop_duration_b = stops.get('B', {}).get('stop_duration', 0)
        self.travel_time_ab = stops.get('B', {}).get('travel_time_from_prev', 60)
        self.travel_time_bc = stops.get('C', {}).get('travel_time_from_prev', 50)
        self.priority = 1 if self.scheduled_stop_duration_b == 0 else 2
        
        # NEW: Energy and Speed state
        self.energy_consumed = 0
        self.drive_mode = "Full Speed" # Can be "Full Speed" or "Eco-Coast"

        self.initial_delay = initial_delay
        self.log = []
        self.action = env.process(self.run())

    def run(self):
        if self.initial_delay > 0:
            yield self.env.timeout(self.initial_delay)
            self._add_log("start_delayed", f"Starts with {self.initial_delay} min delay")

        self._add_log("depart", "Departed from Station A")
        
        yield self.env.process(self.travel_segment("Block_A_B", self.travel_time_ab))

        self._add_log("arrive_station", "Arrived at vicinity of Station B")
        if self.scheduled_stop_duration_b > 0:
            platform_request_process = self.controller.request_platform(self, 'B')
            yield platform_request_process
            platform_id = platform_request_process.value
            self._add_log("at_platform", f"Docked at Station B Platform {platform_id}")
            yield self.env.timeout(self.scheduled_stop_duration_b)
            self.controller.release_platform(self, 'B', platform_id)
            self._add_log("depart_station", "Departed from Station B")
        else:
            yield self.controller.request_pass_through(self, 'B')
            self._add_log("pass_through", "Passing through Station B")

        yield self.env.process(self.travel_segment("Block_B_C", self.travel_time_bc))
        
        self._add_log("arrive_final", "Arrived at final destination Station C")
        self._add_log("final_energy", f"Total energy consumed: {self.energy_consumed:.0f} units")

    def travel_segment(self, block_name, total_travel_time):
        """Simulates travel over a block, checking for drive mode and calculating energy."""
        self._add_log("travel_start", f"Traveling on {block_name}")
        yield self.controller.request_block(self.train_id, block_name)
        
        time_traveled = 0
        while time_traveled < total_travel_time:
            # Ask controller for drive mode
            self.drive_mode = self.controller.get_drive_mode(self)
            
            energy_rate = 0
            time_step = 1 # Simulate 1 minute at a time
            
            if self.drive_mode == "Full Speed":
                energy_rate = 5 # High consumption
            elif self.drive_mode == "Eco-Coast":
                energy_rate = 1.5 # Low consumption, travels slower
                total_travel_time += 0.25 # Coasting adds a 15-second penalty per minute
            
            self.energy_consumed += energy_rate * time_step
            yield self.env.timeout(time_step)
            time_traveled += time_step
        
        self.controller.release_block(block_name)
        self._add_log("travel_end", f"Finished travel on {block_name}")

    def _add_log(self, event, details):
        self.log.append({
            'time': self.env.now,
            'train_id': self.train_id,
            'event': event,
            'details': details
        })