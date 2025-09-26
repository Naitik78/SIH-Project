import simpy

class Station:
    """Represents a train station with a number of platforms."""
    
    def __init__(self, env, name, num_platforms):
        self.env = env
        self.name = name
        # Platforms are a shared resource for trains
        self.platforms = simpy.Resource(env, capacity=num_platforms)