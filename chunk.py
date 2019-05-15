import logging
import numpy as np

import env

class Chunk(object):  # {{{
    def __init__(self):
        self.size           = env.chunk_size
        self.recovery       = env.chunk_k
        self.correct        = env.chunk_d
        self.max            = env.chunk_n

        self.chunk          = 0
    
    def complete(self):
        return self.chunk == self.max

    def to_complete(self):
        return self.max - self.chunk
    
    def add(self):
        self.chunk += 1
        if self.chunk > self.max:
            self.chunk = self.max
        return self.chunk
    
    def remove(self):
        self.chunk -= 1
        if self.chunk < 0:
            self.chunk = 0
        return self.chunk

    def get_d(self):
        return self.correct

# }}}
