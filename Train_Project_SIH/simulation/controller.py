class NonAIController:
    def __init__(self, env, stations, blocks):
        self.env = env
        self.stations = stations
        self.blocks = blocks
        self.platform_allocations = {}

    def get_drive_mode(self, train):
        """Baseline controller always runs at full speed."""
        return "Full Speed"

    def request_block(self, train_id, block_name):
        return self.blocks[block_name].request()

    def release_block(self, block_name):
        if self.blocks[block_name].users:
            self.blocks[block_name].release(self.blocks[block_name].users[0])

    def request_platform(self, train, station_name):
        station = self.stations[station_name]
        req = station.platforms.request()
        self.platform_allocations[train.train_id] = req
        def get_platform_process():
            yield req
            return "Any" 
        return self.env.process(get_platform_process())

    def request_pass_through(self, train, station_name):
        def _pass_through_process():
            yield self.env.timeout(2)
        return self.env.process(_pass_through_process())

    def release_platform(self, train, station_name, platform_id=None):
        station = self.stations[station_name]
        if train.train_id in self.platform_allocations:
            station.platforms.release(self.platform_allocations[train.train_id])
            del self.platform_allocations[train.train_id]