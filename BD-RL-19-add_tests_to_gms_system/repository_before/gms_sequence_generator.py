class SequenceGenerator:
    def __init__(self, db_connection):
        self.db = db_connection
        self.current_id = 0
        self.max_id_in_lease = 0

    def get_next_id(self):
        # If we ran out of IDs in our current lease, get a new block
        if self.current_id >= self.max_id_in_lease:
            # DB returns the start of a new block of 100 IDs
            new_start = self.db.get_next_block_start(block_size=100)

            self.current_id = new_start
            self.max_id_in_lease = new_start + 100

        self.current_id += 1
        return self.current_id
