import numpy as np
from scipy import stats

def init_gpt35_4g_state_func():
    return {
        "normal_states": [
            np.array([0.]),  # normed_last_bit_rate
            np.array([0.]),  # normed_last_buffer_size
            np.array([0.]),  # remaining_chunk_percentage
        ],
        "time_series_states": [
            np.array([0.] * 8),  # throughput_MBps_list
            np.array([0.] * 8),  # normed_delay_list
            np.array([0.] * 6),  # next_chunk_bytes_MB
            np.array([0.]),  # qoe
            np.array([0.] * 2),  # throughput_variance, delay_variance
            np.array([0.] * 2),  # throughput_trend, delay_trend
        ],
    }

def gpt35_4g_state_func(
    bit_rate_kbps_list,
    buffer_size_second_list,
    delay_second_list,
    video_chunk_size_bytes_list,
    next_chunk_bytes_sizes,
    video_chunk_remain_num,
    total_chunk_num,
    all_bit_rate_kbps,
):
    # Current code remains unchanged for normal states
    normed_last_bit_rate = bit_rate_kbps_list[-1] / float(np.max(all_bit_rate_kbps))
    buffer_norm_factor = 10.
    normed_last_buffer_size = buffer_size_second_list[-1] / buffer_norm_factor
    remaining_chunk_percentage = float(video_chunk_remain_num / total_chunk_num)
    normal_states = [
        [normed_last_bit_rate],
        [normed_last_buffer_size],
        [remaining_chunk_percentage],
    ]

    # Time series state 1: Estimated throughput in near history
    history_window = 8
    throughput_MBps_list = []
    for i in range(history_window):
        history_chunk_size_bytes = video_chunk_size_bytes_list[-(history_window - i)]
        history_delay_second = delay_second_list[-(history_window - i)]
        throughput_MBps_list.append(history_chunk_size_bytes / 1000. / 1000. / history_delay_second)

    # Time series state 2: The normed download time (delay) in near history
    delay_norm_factor = 10.
    normed_delay_list = [x / delay_norm_factor for x in delay_second_list]

    # Time series state 3: Treat next chunk sizes in MB as ts states, too.
    next_chunk_bytes_MB = [x / 1000. / 1000. for x in next_chunk_bytes_sizes]

    # New normal state: Quality of Experience (QoE)
    qoe = (normed_last_bit_rate * normed_last_buffer_size) / np.mean(normed_delay_list)

    # New time series state 4: Variability in throughput and delay
    throughput_variance = np.var(throughput_MBps_list)
    delay_variance = np.var(normed_delay_list)

    # New time series state 5: Trend of throughput and delay
    throughput_trend = stats.linregress(np.arange(history_window), throughput_MBps_list).slope
    delay_trend = stats.linregress(np.arange(history_window), normed_delay_list).slope

    time_series_states = [
        throughput_MBps_list,
        normed_delay_list,
        next_chunk_bytes_MB,
        [qoe],
        [throughput_variance, delay_variance],
        [throughput_trend, delay_trend]
    ]

    return {
        "normal_states": normal_states,
        "time_series_states": time_series_states,
    }

def init_gpt35_5g_state_func():
    return {
        "normal_states": [
            np.array([0.]),  # normed_last_bit_rate
            np.array([0.]),  # normed_last_buffer_size
            np.array([0.]),  # remaining_chunk_percentage
            np.array([0.]),  # throughput_variance
            np.array([0., 0., 0.]),  # predicted_throughput
            np.array([0., 0.]),  # mean_delay, std_buffer_size
        ],
        "time_series_states": [
            np.array([0.] * 8),  # throughput_MBps_list
            np.array([0.] * 8),  # normed_delay_list
            np.array([0.] * 6),  # next_chunk_bytes_MB
        ],
    }

def gpt35_5g_state_func(
    bit_rate_kbps_list,
    buffer_size_second_list,
    delay_second_list,
    video_chunk_size_bytes_list,
    next_chunk_bytes_sizes,
    video_chunk_remain_num,
    total_chunk_num,
    all_bit_rate_kbps,
):
    # existing normal states
    normed_last_bit_rate = bit_rate_kbps_list[-1] / float(np.max(all_bit_rate_kbps))
    buffer_norm_factor = 10.
    normed_last_buffer_size = buffer_size_second_list[-1] / buffer_norm_factor
    remaining_chunk_percentage = float(video_chunk_remain_num / total_chunk_num)
    normal_states = [
        [normed_last_bit_rate],
        [normed_last_buffer_size],
        [remaining_chunk_percentage],
    ]
    
    # existing time series states
    history_window = 8
    throughput_MBps_list = []
    for i in range(history_window):
        history_chunk_size_bytes = video_chunk_size_bytes_list[-(history_window - i)]
        history_delay_second = delay_second_list[-(history_window - i)]
        throughput_MBps_list.append(history_chunk_size_bytes / 1000. / 1000. / history_delay_second)
    delay_norm_factor = 10.
    normed_delay_list = [x / delay_norm_factor for x in delay_second_list]
    next_chunk_bytes_MB = [x / 1000. / 1000. for x in next_chunk_bytes_sizes]
    time_series_states = [
        throughput_MBps_list,
        normed_delay_list,
        next_chunk_bytes_MB,
    ]
    
    # new features: variance in throughput
    throughput_variance = np.var(throughput_MBps_list)
    normal_states.append([throughput_variance])
    
    # new features: prediction of future throughput
    # Utilize a prediction model to estimate future throughput and normalize the result
    predicted_throughput = [0.2, 0.3, 0.4]  # Placeholder for predicted values
    predicted_throughput_normed = [x / float(np.max(throughput_MBps_list)) for x in predicted_throughput]
    normal_states.append(predicted_throughput_normed)
    
    # new features: statistical features of network conditions
    # Incorporate statistical features such as mean and standard deviation of delay and buffer size
    mean_delay = np.mean(delay_second_list)
    std_buffer_size = np.std(buffer_size_second_list)
    normal_states.append([mean_delay, std_buffer_size])
    
    return {
        "normal_states": normal_states,
        "time_series_states": time_series_states,
    }


def init_gpt35_starlink_state_func():
    return {
        "normal_states": [
            np.array([0., 0., 0., 0.]),  # normed_last_bit_rate, normed_last_buffer_size, remaining_chunk_percentage, normed_bit_rate_change
        ],
        "time_series_states": [
            np.array([0.] * 8),  # normed_network_throughput
        ],
    }


def gpt35_starlink_state_func(
    bit_rate_kbps_list,
    buffer_size_second_list,
    delay_second_list,
    video_chunk_size_bytes_list,
    next_chunk_bytes_sizes,
    video_chunk_remain_num,
    total_chunk_num,
    all_bit_rate_kbps,
):
    # Current state features
    normed_last_bit_rate = bit_rate_kbps_list[-1] / float(np.max(all_bit_rate_kbps))
    buffer_norm_factor = 10.
    normed_last_buffer_size = buffer_size_second_list[-1] / buffer_norm_factor
    remaining_chunk_percentage = float(video_chunk_remain_num / total_chunk_num)

    # New state features
    # Normalized bitrate change over the last few chunks
    bit_rate_change = (bit_rate_kbps_list[-1] - bit_rate_kbps_list[-2]) / float(np.max(all_bit_rate_kbps))
    # Network throughput in near history
    network_throughput_MBps = []
    for i in range(len(bit_rate_kbps_list)):
        throughput = video_chunk_size_bytes_list[i] / 1000. / 1000. / delay_second_list[i]
        network_throughput_MBps.append(throughput)

    # Normalized new state features
    normed_bit_rate_change = bit_rate_change / float(np.max(all_bit_rate_kbps))
    normed_network_throughput = [x / (1000.0 * np.max(all_bit_rate_kbps)) for x in network_throughput_MBps]

    normal_states = [
        [normed_last_bit_rate, normed_last_buffer_size, remaining_chunk_percentage, normed_bit_rate_change]
    ]
    time_series_states = [
        normed_network_throughput
    ]

    return {
        "normal_states": normal_states,
        "time_series_states": time_series_states,
    }
