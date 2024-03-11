import tensorflow.compat.v1 as tf
import tflearn
import argparse
import csv
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import sys
import time

import numpy as np

from pensieve.agent_policy import Pensieve, RobustMPC, BufferBased, FastMPC, CustomPensieve
from pensieve.a3c.a3c_jump import ActorNetwork

# new state reps
from pensieve.ppo2.network import Network

# new state reps
from .state_func.default import *
from .state_func.gpt35 import *
from .state_func.gpt4 import *

from pensieve.constants import (
    A_DIM,
    BUFFER_NORM_FACTOR,
    DEFAULT_QUALITY,
    M_IN_K,
    S_INFO,
    S_LEN,
    TOTAL_VIDEO_CHUNK,
    VIDEO_BIT_RATE,
)
from pensieve.utils import construct_bitrate_chunksize_map, linear_reward

RANDOM_SEED = 42
RAND_RANGE = 1000


def parse_args():
    """Parse arguments from the command line."""
    parser = argparse.ArgumentParser("Video Server")
    parser.add_argument('--description', type=str, default=None,
                        help='Optional description of the experiment.')
    # ABR related
    parser.add_argument('--abr', type=str, required=True,
                        choices=['RobustMPC', 'RL', 'BufferBased', 'FastMPC'],
                        help='ABR algorithm.')
    parser.add_argument('--actor-path', type=str, default=None,
                        help='Path to RL model.')
    # data io related
    parser.add_argument('--summary-dir', type=str,
                        help='directory to save logs.')
    parser.add_argument('--trace-file', type=str, help='Path to trace file.')
    parser.add_argument("--video-size-file-dir", type=str, required=True,
                        help='Dir to video size files')

    # networking related
    parser.add_argument('--ip', type=str, default='localhost',
                        help='ip address of ABR/video server.')
    parser.add_argument('--port', type=int, default=8333,
                        help='port number of ABR/video server.')

    return parser.parse_args()


def make_request_handler(server_states):
    """Instantiate HTTP request handler."""

    class Request_Handler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.server_states = server_states
            self.abr = server_states['abr']
            self.video_size = server_states['video_size']
            self.log_writer = server_states['log_writer']
            self.sess = server_states['sess']
            self.actor = server_states['actor']
            # for custom state rep
            self.model_type = server_states['model_type']
            self.network_type = server_states['network_type']
            self.bit_rate_kbps_list = [1e-6] * 8
            self.buffer_size_second_list = [1e-6] * 8
            self.delay_second_list = [1e-6] * 8
            self.video_chunk_size_bytes_list = [1e-6] * 8
            self.next_chunk_bytes_sizes = []
            self.video_chunk_remain_num = 0
            self.total_chunk_num = 0
            self.all_bit_rate_kbps = []
            print(f'Using model_type {self.model_type} for network type {self.network_type}')
            BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(
                content_length).decode('utf-8'))
            # print(self.server_states['video_chunk_count'],
            #       self.server_states['last_bit_rate'])
            print("\tlastRequest: {}\n\tlastquality: {}\n\t"
                  "lastChunkStartTime: {}\n\tlastChunkEndTime: {}\n\t"
                  "lastChunkSize: {}\n\tRebufferTime: {}s\n\tbuffer: {}s\n\t"
                  "bufferAdjusted: {}\n\tbandwidthEst: {}\n\t"
                  "nextChunkSize: {}".format(
                      post_data['lastRequest'],
                      post_data['lastquality'],
                      post_data['lastChunkStartTime'],
                      post_data['lastChunkFinishTime'],
                      post_data['lastChunkSize'],
                      post_data['RebufferTime'] / M_IN_K,
                      post_data['buffer'],
                      post_data['bufferAdjusted'],
                      post_data['bandwidthEst'],
                      post_data['nextChunkSize'],
                  ))
            # {'nextChunkSize': [2059512, 1358801, 885714, 581493, 372963,
            # 150616], 'lastquality': 5, 'buffer': 4.793656999999996,
            # 'bufferAdjusted': 0.24365699999999535, 'bandwidthEst':
            # 13319.003002506452, 'lastRequest': 16, 'RebufferTime': 752,
            # 'lastChunkFinishTime': 1611459172006, 'lastChunkStartTime':
            # 1611459170508, 'lastChunkSize': 2289689}
            # print(post_data)

            if ('pastThroughput' in post_data):
                # @Hongzi: this is just the summary of throughput/quality at
                # the end of the load so we don't want to use this information
                # to send back a new quality
                print("Summary: ", post_data)
            else:
                # option 1. reward for just quality
                # reward = post_data['lastquality']
                # option 2. combine reward for quality and rebuffer time
                #           tune up the knob on rebuf to prevent it more
                # reward = post_data['lastquality'] - 0.1 *
                # (post_data['RebufferTime'] -
                # self.input_dict['last_total_rebuf'])
                # option 3. give a fixed penalty if video is stalled
                #           this can reduce the variance in reward signal
                # reward = post_data['lastquality'] - 10 *
                # ((post_data['RebufferTime'] -
                # self.input_dict['last_total_rebuf']) > 0)

                # option 4. use the metric in SIGCOMM MPC paper
                rebuffer_time = float(
                    post_data['RebufferTime'] -
                    self.server_states['last_total_rebuf'])

                # --linear reward--
                reward = linear_reward(
                    VIDEO_BIT_RATE[post_data['lastquality']],
                    VIDEO_BIT_RATE[self.server_states['last_bit_rate']],
                    rebuffer_time / M_IN_K)
                # VIDEO_BIT_RATE[post_data['lastquality']] / M_IN_K \
                #     - REBUF_PENALTY * rebuffer_time / M_IN_K \
                #     - SMOOTH_PENALTY * np.abs(
                #     VIDEO_BIT_RATE[post_data['lastquality']] -
                #     self.last_bit_rate) / M_IN_K

                self.server_states['last_bit_rate'] = post_data['lastquality']
                self.server_states['last_total_rebuf'] = post_data['RebufferTime']

                # compute bandwidth measurement
                video_chunk_fetch_time = post_data['lastChunkFinishTime'] - \
                    post_data['lastChunkStartTime']
                # print('video chunk fetch time:', video_chunk_fetch_time)
                video_chunk_size = post_data['lastChunkSize']

                # compute number of video chunks left
                self.server_states['video_chunk_count'] += 1
                video_chunk_remain = TOTAL_VIDEO_CHUNK - \
                    self.server_states['video_chunk_count']

                next_video_chunk_sizes = []
                for i in range(A_DIM):
                    if 0 <= self.server_states['video_chunk_count'] < TOTAL_VIDEO_CHUNK:
                        next_video_chunk_sizes.append(
                            self.video_size[i][self.server_states['video_chunk_count']])
                    else:
                        next_video_chunk_sizes.append(0)

                # for custom state rep
                self.update_state(post_data, video_chunk_size, video_chunk_fetch_time, next_video_chunk_sizes)

                # this should be S_INFO number of terms
                try:
                    state0 = VIDEO_BIT_RATE[post_data['lastquality']
                                            ] / max(VIDEO_BIT_RATE)
                    state1 = post_data['buffer'] / BUFFER_NORM_FACTOR
                    # kilo byte / ms
                    state2 = video_chunk_size / video_chunk_fetch_time / M_IN_K
                    state3 = video_chunk_fetch_time / M_IN_K / BUFFER_NORM_FACTOR  # 10 sec

                    # mega byte
                    state4 = np.array(next_video_chunk_sizes) / M_IN_K / M_IN_K
                    state5 = min(video_chunk_remain,
                                 TOTAL_VIDEO_CHUNK) / TOTAL_VIDEO_CHUNK
                    # dequeue history record
                    self.server_states['state'] = np.roll(
                        self.server_states['state'], -1, -1)
                    self.server_states['state'][0, 0, -1] = state0
                    self.server_states['state'][0, 1, -1] = state1
                    self.server_states['state'][0, 2, -1] = state2
                    self.server_states['state'][0, 3, -1] = state3
                    self.server_states['state'][0, 4, :A_DIM] = state4
                    self.server_states['state'][0, 5, -1] = state5
                except ZeroDivisionError:
                    # this should occur VERY rarely (1 out of 3000), should be
                    # a dash issue in this case we ignore the observation and
                    # roll back to an eariler one
                    pass
                    # log wall_time, bit_rate, buffer_size, rebuffer_time,
                    # video_chunk_size, download_time, reward
                self.log_writer.writerow(
                    [time.time(), VIDEO_BIT_RATE[post_data['lastquality']],
                     post_data['buffer'], rebuffer_time / M_IN_K,
                     video_chunk_size, video_chunk_fetch_time, reward,
                     post_data['bandwidthEst'] / 1000,
                     self.server_states['future_bandwidth']])
                if isinstance(self.abr, Pensieve):
                    print('Not evaluating on 4g or 5g. Returning default state rep.')
                    state = self.server_states['state']
                    bit_rate = self.abr.select_action(state, last_bit_rate=self.server_states['last_bit_rate'])
                elif isinstance(self.abr, CustomPensieve):
                    state = self.get_state()
                    bit_rate = self.abr.select_action(state)
                elif isinstance(self.abr, RobustMPC):
                    last_index = int(post_data['lastRequest'])
                    future_chunk_cnt = min(self.abr.mpc_future_chunk_cnt,
                                           TOTAL_VIDEO_CHUNK - last_index - 1)
                    bit_rate, self.server_states['future_bandwidth'] = \
                        self.abr.select_action(
                        self.server_states['state'], last_index,
                        future_chunk_cnt, np.array(
                            [self.video_size[i]
                             for i in sorted(self.video_size)]),
                        post_data['lastquality'], post_data['buffer'])
                elif isinstance(self.abr, BufferBased):
                    bit_rate = self.abr.select_action(post_data['buffer'])
                elif isinstance(self.abr, FastMPC):
                    last_index = int( post_data['lastRequest'] )
                    future_chunk_cnt = min( self.abr.mpc_future_chunk_cnt ,
                                            TOTAL_VIDEO_CHUNK - last_index - 1 )
                    bit_rate ,self.server_states['future_bandwidth'] = \
                        self.abr.select_action(
                            self.server_states['state'] ,last_index ,
                            future_chunk_cnt ,np.array(
                                [self.video_size[i]
                                 for i in sorted( self.video_size )] ) ,
                            post_data['lastquality'] ,post_data['buffer'] )
                else:
                    raise TypeError("Unsupported ABR type.")
                # action_prob = self.actor.predict(
                #     np.reshape(state, (1, S_INFO, S_LEN)))
                # action_cumsum = np.cumsum(action_prob)
                # bit_rate = (action_cumsum > np.random.randint(
                #     1, RAND_RANGE) / float(RAND_RANGE)).argmax()
                # Note: we need to discretize the probability into 1/RAND_RANGE
                # steps, because there is an intrinsic discrepancy in passing
                # single state and batch states

                # send data to html side
                #self.last_bit_rate = bit_rate
                send_data = str(bit_rate)

                end_of_video = post_data['lastRequest'] == TOTAL_VIDEO_CHUNK
                if end_of_video:
                    # send_data = "REFRESH"
                    send_data = "stop"  # TODO: do not refresh the webpage and wait for timeout
                    self.server_states['last_total_rebuf'] = 0
                    self.server_states['last_bit_rate'] = DEFAULT_QUALITY
                    self.server_states['video_chunk_count'] = 0
                    self.server_states['state'] = np.zeros((1, S_INFO, S_LEN))
                    # so that in the log we know where video ends
                    # self.log_writer.writerow('\n')
                    print('Hit Last Video Chunk.')

                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Content-Length', str(len(send_data)))
                self.send_header('Access-Control-Allow-Origin', "*")
                self.end_headers()
                self.wfile.write(send_data.encode())
                print('Sent Response for Next Chunk: ', send_data)

                # record [state, action, reward]
                # put it here after training, notice there is a shift in reward
                # storage

        def update_state(self, post_data, video_chunk_size, video_chunk_fetch_time, next_video_chunk_sizes):
            self.bit_rate_kbps_list = self.bit_rate_kbps_list[1:] + [VIDEO_BIT_RATE[post_data['lastquality']]] # kbps
            self.buffer_size_second_list = self.buffer_size_second_list[1:] + [post_data['buffer']]  # seconds
            self.delay_second_list = self.delay_second_list[1:] + [video_chunk_fetch_time / 1000.0]  # seconds
            self.video_chunk_size_bytes_list = self.video_chunk_size_bytes_list[1:] + [video_chunk_size]  # bytes
            self.next_chunk_bytes_sizes = next_video_chunk_sizes  # bytes
            self.video_chunk_remain_num = TOTAL_VIDEO_CHUNK - self.server_states['video_chunk_count'] # scalar
            self.total_chunk_num = TOTAL_VIDEO_CHUNK  # scalar
            self.all_bit_rate_kbps = np.array(VIDEO_BIT_RATE)  # kbps

        def process_state(self, state):
            for i in range(len(state['normal_states'])):
                state['normal_states'][i] = np.array(state['normal_states'][i], dtype=np.float32)
            for i in range(len(state['time_series_states'])):
                state['time_series_states'][i] = np.array(state['time_series_states'][i], dtype=np.float32)
            return state


        def get_state(self):
            if self.model_type == 'gpt35':
                state_func = gpt35_4g_state_func if self.network_type == '4g' else gpt35_5g_state_func
                state = state_func(self.bit_rate_kbps_list, self.buffer_size_second_list, self.delay_second_list, self.video_chunk_size_bytes_list, self.next_chunk_bytes_sizes, self.video_chunk_remain_num, self.total_chunk_num, self.all_bit_rate_kbps)
            elif self.model_type == 'gpt4':
                state_func = gpt4_4g_state_func if self.network_type == '4g' else gpt4_5g_state_func
                state = state_func(self.bit_rate_kbps_list, self.buffer_size_second_list, self.delay_second_list, self.video_chunk_size_bytes_list, self.next_chunk_bytes_sizes, self.video_chunk_remain_num, self.total_chunk_num, self.all_bit_rate_kbps)
            else:
                state = default_state_func(self.bit_rate_kbps_list, self.buffer_size_second_list, self.delay_second_list, self.video_chunk_size_bytes_list, self.next_chunk_bytes_sizes, self.video_chunk_remain_num, self.total_chunk_num, self.all_bit_rate_kbps)
            # state = self.process_state(state)
            return [state]  # NOTE: models expect list

        def do_GET(self):
            print('GOT REQ')
            self.send_response(200)
            # self.send_header('Cache-Control', 'Cache-Control: no-cache,
            # no-store, must-revalidate max-age=0')
            self.send_header('Cache-Control', 'max-age=3000')
            self.send_header('Content-Length', '20')
            self.end_headers()
            self.wfile.write(b"console.log('here');")

        # def log_message(self, format, *args):
        #     return

    return Request_Handler


def get_init_state_dict(network_type, actor_path):
    if network_type == '4g':
        init_state_func = init_gpt35_4g_state_func if 'gpt35' in actor_path else init_gpt4_4g_state_func
    elif network_type == '5g':
        init_state_func = init_gpt35_5g_state_func if 'gpt35' in actor_path else init_gpt4_5g_state_func
    else:
        init_state_func = init_default_state_func
    return init_state_func()

def run_abr_server(abr, trace_file, summary_dir, actor_path,
                   video_size_file_dir, ip='localhost', port=8333):

    os.makedirs(summary_dir, exist_ok=True)
    log_file_path = os.path.join(
        summary_dir, 'log_{}_{}'.format(abr, os.path.basename(trace_file)))

    # Network type is only set for custom state rep
    network_type = None
    if '4g' in actor_path:
        network_type = '4g'
    elif '5g' in actor_path:
        network_type = '5g'

    g = tf.Graph()
    with g.as_default():
        with tf.Session() as sess ,open( log_file_path ,'wb' ) as log_file:
            # TODO: USE CUSTOM PENSIEVE HERE
            if network_type is None:
                # actor = ActorNetwork( sess ,
                #                     state_dim=[6 ,6] ,action_dim=3 ,
                #                     bitrate_dim=6)
                # sess.run( tf.initialize_all_variables() )
                # saver = tf.train.Saver()  # save neural net parameters
                actor = None
            else:
                sample_state_dict = get_init_state_dict(network_type, actor_path)
                actor = Network(sess, sample_state_dict, A_DIM, 1e-5)
                tflearn.is_training(False, session=sess)
                sess.run(tf.global_variables_initializer())
                saver = tf.train.Saver(tf.trainable_variables())             

            # restore neural net parameters
            nn_model = actor_path
            if actor is not None and nn_model is not None:  # nn_model is the path to file
                print(nn_model)
                saver.restore( sess ,nn_model )
                #print( "Model restored." )

            model_type = 'default'
            if abr == 'RobustMPC':
                abr = RobustMPC()
            elif abr == 'FastMPC':
                abr = FastMPC()
            elif abr == 'RL':
                assert actor_path is not None, "actor-path is needed for RL abr."
                # use to choose state representation
                if 'gpt35' in actor_path:
                    model_type = 'gpt35'
                elif 'gpt4' in actor_path:
                    model_type = 'gpt4'
                else:
                    model_type = 'default'
                # Init Pensieve or CustomPensieve
                if network_type is None:
                    abr = Pensieve(16, summary_dir, actor=actor)
                else:
                    abr = CustomPensieve(actor)
            elif abr == 'BufferBased':
                abr = BufferBased()
            else:
                raise ValueError("ABR {} is not supported!".format(abr))

            video_size = construct_bitrate_chunksize_map(video_size_file_dir)
            np.random.seed(RANDOM_SEED)

            assert len(VIDEO_BIT_RATE) == A_DIM

            # interface to abr_rl server

            log_writer = csv.writer(open(log_file_path, 'w', 1), delimiter='\t',
                                    lineterminator='\n')
            log_writer.writerow(
                ['timestamp', 'bit_rate', 'buffer_size', 'rebuffer_time',
                'video_chunk_size', 'download_time', 'reward',
                'bandwidth_estimation','future_bandwidth'])

            # variables and states needed to track among requests
            server_states = {
                'sess': sess,
                'actor': actor,
                'log_writer': log_writer,
                'abr': abr,
                'video_size': video_size,
                'video_chunk_count': 0,
                "last_total_rebuf": 0,
                'last_bit_rate': DEFAULT_QUALITY,
                'state': np.zeros((1, S_INFO, S_LEN)),
                'future_bandwidth': 0,
                'model_type': model_type,
                'network_type': network_type
            }
            handler_class = make_request_handler(server_states)

            server_address = (ip, port)
            httpd = HTTPServer(server_address, handler_class)
            print('Listening on ({}, {})'.format(ip, port))
            httpd.serve_forever()


def main():
    args = parse_args()
    run_abr_server(args.abr, args.trace_file, args.summary_dir,
                   args.actor_path, args.video_size_file_dir, args.ip,
                   args.port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Capture Keyboard interrupted.")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)