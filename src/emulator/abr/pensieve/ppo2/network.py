import math
import numpy as np
import tensorflow.compat.v1 as tf
import os
import time
import tflearn

'''
state_dict is something like:

state_dict = {
    "normal_states": [
        np.array([0.1]),
        np.array([0.2]),
        np.array([4, 6, 2, 8, 9]),
    ],
    "time_series_states": [
        np.array([1, 8, 9, 1, 7, 9, 0, 2]),
        np.array([1, 0, 1, 0, 1, 0, 1, 0]),
        np.array([0, 1, 0, 1, 0, 1, 0, 1]),
    ],
}

state_dict is a list of such kind of state_dict
'''

class Network():
    def create_inputs_and_network(self):
        state_dict = self.sample_state_dict
        feature_num = self.feature_num
        a_dim = self.a_dim

        for state in state_dict["normal_states"]:
            # assert 1d shape
            assert len(np.array(state).shape) == 1
        for state in state_dict["time_series_states"]:
            # assert 1d shape
            assert len(np.array(state).shape) == 1

        normal_state_dim_list = [np.array(state).shape[0] for state in state_dict["normal_states"]]
        ts_state_dim_list = [np.array(state).shape[0] for state in state_dict["time_series_states"]]

        normal_input_list = [
           tf.placeholder(tf.float32, [None, state_dim]) for state_dim in normal_state_dim_list
        ]

        ts_input_list = [
           tf.placeholder(tf.float32, [None, state_dim]) for state_dim in ts_state_dim_list 
        ]

        with tf.variable_scope('actor'):
            normal_features = [
                tflearn.fully_connected(normal_input, feature_num, activation='relu')
                for normal_input in normal_input_list
            ]
            ts_features = [
                tflearn.flatten(tflearn.conv_1d(
                    tf.expand_dims(ts_input, axis=1), 
                    feature_num, 1, activation='relu'
                ))
                for ts_input in ts_input_list
            ]
            merged_features = tflearn.merge(normal_features + ts_features, "concat")
            pi_features = tflearn.fully_connected(merged_features, feature_num, activation='relu')
            pi = tflearn.fully_connected(pi_features, a_dim, activation='softmax')

        with tf.variable_scope('critic'):
            normal_features = [
                tflearn.fully_connected(normal_input, feature_num, activation='relu')
                for normal_input in normal_input_list
            ]
            ts_features = [
                tflearn.flatten(tflearn.conv_1d(
                    tf.expand_dims(ts_input, axis=1), 
                    feature_num, 1, activation='relu'
                ))
                for ts_input in ts_input_list
            ]
            merged_features = tflearn.merge(normal_features + ts_features, "concat")
            value_features = tflearn.fully_connected(merged_features, feature_num, activation='relu')
            value = tflearn.fully_connected(value_features, 1, activation='linear')

        self.normal_input_list = normal_input_list
        self.ts_input_list = ts_input_list
        self.pi = pi
        self.val = value
        # for t_var in tf.trainable_variables():
        #     print(t_var)


    def create_inputs_and_network_from_text(self, network_text):
        self.network_text = network_text

        state_dict = self.sample_state_dict
        a_dim = self.a_dim

        for state in state_dict["normal_states"]:
            # assert 1d shape
            assert len(np.array(state).shape) == 1
        for state in state_dict["time_series_states"]:
            # assert 1d shape
            assert len(np.array(state).shape) == 1

        normal_state_dim_list = [np.array(state).shape[0] for state in state_dict["normal_states"]]
        ts_state_dim_list = [np.array(state).shape[0] for state in state_dict["time_series_states"]]

        normal_input_list = [
           tf.placeholder(tf.float32, [None, state_dim]) for state_dim in normal_state_dim_list
        ]

        ts_input_list = [
           tf.placeholder(tf.float32, [None, state_dim]) for state_dim in ts_state_dim_list 
        ]

        x = {}
        exec(network_text, x)
        self.network_func = x['network_func']
        pi, value = self.network_func(normal_input_list, ts_input_list, a_dim)
        self.normal_input_list = normal_input_list
        self.ts_input_list = ts_input_list
        self.pi = pi
        self.val = value


            
    def get_network_params(self):
        return self.sess.run(self.network_params)

    def set_network_params(self, input_network_params):
        self.sess.run(self.set_network_params_op, feed_dict={
            i: d for i, d in zip(self.input_network_params, input_network_params)
        })

    def r(self, pi_new, pi_old, acts):
        return tf.reduce_sum(tf.multiply(pi_new, acts), reduction_indices=1, keepdims=True) / \
                tf.reduce_sum(tf.multiply(pi_old, acts), reduction_indices=1, keepdims=True)

    def __init__(self, sess, sample_state_dict, action_dim, learning_rate, feature_num=128, action_eps=1e-4, gamma=0.99, ppo2_eps=0.2, entropy_discount_factor=1.0, use_network_text=False, network_text=""):
        self.sample_state_dict = sample_state_dict
        self.feature_num = feature_num
        self.action_eps = action_eps
        self.gamma = gamma
        self.ppo2_eps = ppo2_eps

        self.a_dim = action_dim
        self.lr_rate = learning_rate
        self.sess = sess
        self.entropy_discount_factor = entropy_discount_factor
        self._entropy_weight = np.log(self.a_dim) * self.entropy_discount_factor
        self.H_target = 0.1

        self.R = tf.placeholder(tf.float32, [None, 1])
        self.old_pi = tf.placeholder(tf.float32, [None, self.a_dim])
        self.acts = tf.placeholder(tf.float32, [None, self.a_dim])
        self.entropy_weight = tf.placeholder(tf.float32)
        if use_network_text is False:
            self.create_inputs_and_network()
        else:
            self.create_inputs_and_network_from_text(network_text)
        self.real_out = tf.clip_by_value(self.pi, self.action_eps, 1. - self.action_eps)
        
        self.entropy = -tf.reduce_sum(tf.multiply(self.real_out, tf.log(self.real_out)), reduction_indices=1, keepdims=True)
        self.adv = tf.stop_gradient(self.R - self.val)
        self.ppo2loss = tf.minimum(self.r(self.real_out, self.old_pi, self.acts) * self.adv, 
                            tf.clip_by_value(self.r(self.real_out, self.old_pi, self.acts), 1 - self.ppo2_eps, 1 + self.ppo2_eps) * self.adv
                        )
        self.dual_loss = tf.where(tf.less(self.adv, 0.), tf.maximum(self.ppo2loss, 3. * self.adv), self.ppo2loss)

        # Get all network parameters
        self.network_params = \
            tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='actor')
        self.network_params += \
            tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='critic')

        # Set all network parameters
        self.input_network_params = []
        for param in self.network_params:
            self.input_network_params.append(
                tf.placeholder(tf.float32, shape=param.get_shape()))
        self.set_network_params_op = []
        for idx, param in enumerate(self.input_network_params):
            self.set_network_params_op.append(
                self.network_params[idx].assign(param))
        
        self.policy_loss = - tf.reduce_sum(self.dual_loss) - self.entropy_weight * tf.reduce_sum(self.entropy)
        self.policy_opt = tf.train.AdamOptimizer(self.lr_rate).minimize(self.policy_loss)
        self.val_loss = tflearn.mean_square(self.val, self.R)
        self.val_opt = tf.train.AdamOptimizer(self.lr_rate * 10.).minimize(self.val_loss)

    def get_feed_dict(self, state_dict_list):
        feed_dict = {}
        for idx, normal_input in enumerate(self.normal_input_list):
            one_inputs = []
            for state_dict in state_dict_list:
                one_inputs.append(np.array(state_dict["normal_states"][idx]))
            feed_dict[normal_input] = np.array(one_inputs)

        for idx, ts_input in enumerate(self.ts_input_list):
            one_inputs = []
            for state_dict in state_dict_list:
                one_inputs.append(np.array(state_dict["time_series_states"][idx]))
            feed_dict[ts_input] = np.array(one_inputs)
        return feed_dict


    def predict(self, state_dict_list):
        feed_dict = self.get_feed_dict(state_dict_list)
        action = self.sess.run(self.real_out, feed_dict=feed_dict)
        return action[0]
    
    def train(self, state_dict_list, a_batch, p_batch, v_batch, epoch):
        feed_dict = self.get_feed_dict(state_dict_list)
        feed_dict[self.acts] = a_batch
        feed_dict[self.R] = v_batch
        feed_dict[self.old_pi] = p_batch
        feed_dict[self.entropy_weight] = self._entropy_weight
        self.sess.run([self.policy_opt, self.val_opt], feed_dict=feed_dict)
        # adaptive entropy weight
        # https://arxiv.org/abs/2003.13590
        p_batch = np.clip(p_batch, self.action_eps, 1. - self.action_eps)
        _H = np.mean(np.sum(-np.log(p_batch) * p_batch, axis=1))
        _g = _H - self.H_target
        self._entropy_weight -= self.lr_rate * _g * 0.1 * self.entropy_discount_factor

    def compute_v(self, state_dict_list, a_batch, r_batch, terminal):
        feed_dict = self.get_feed_dict(state_dict_list) 
        ba_size = len(state_dict_list)
        R_batch = np.zeros([len(r_batch), 1])

        if terminal:
            R_batch[-1, 0] = 0  # terminal state
        else:    
            v_batch = self.sess.run(self.val, feed_dict=feed_dict)
            R_batch[-1, 0] = v_batch[-1, 0]  # boot strap from last state
        for t in reversed(range(ba_size - 1)):
            R_batch[t, 0] = r_batch[t] + self.gamma * R_batch[t + 1, 0]

        return list(R_batch)