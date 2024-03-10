import numpy as np

class CustomPensieve():
    def __init__(self, actor):
        self.net = actor


    def select_action(self, state):
        action_prob = self.net.predict(state)
        bit_rate = np.argmax(np.log(action_prob))
        return bit_rate




