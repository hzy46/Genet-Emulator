import numpy as np
# scipy.stats could be used for z-score standardization if we were allowed to import it.

def init_gpt4_4g_state_func():
    return {
        "normal_states": [
            np.array([0.]),  # normed_last_bit_rate
            np.array([0.]),  # normed_last_buffer_size
            np.array([0.]),  # remaining_chunk_percentage
            np.array([0.]),  # smoothness_metric
        ],
        "time_series_states": [
            np.array([0.] * 8),  # norm_throughput_MBps_list
            np.array([0.] * 8),  # normed_delay_list
            np.array([0.] * 6),  # future_chunk_size_ratio
            np.array([0.]),  # ema_throughput
            np.array([0.]),  # ema_delay
            np.array([0.] * 7),  # buffer_size_trend
        ],
    }

def gpt4_4g_state_func(
    bit_rate_kbps_list,
    buffer_size_second_list,
    delay_second_list,
    video_chunk_size_bytes_list,
    next_chunk_bytes_sizes,
    video_chunk_remain_num,
    total_chunk_num,
    all_bit_rate_kbps,
):
    # Constants for normalization
    buffer_norm_factor = 10.
    delay_norm_factor = 10.
    max_bit_rate = np.max(all_bit_rate_kbps)
    history_window = min(8, len(bit_rate_kbps_list))  # min to handle shorter lists

    # Normal states
    normed_last_bit_rate = bit_rate_kbps_list[-1] / float(max_bit_rate)
    normed_last_buffer_size = buffer_size_second_list[-1] / buffer_norm_factor
    remaining_chunk_percentage = float(video_chunk_remain_num) / total_chunk_num
    
    # Bit rate change variance (smoothness metric)
    bit_rate_changes = np.diff(bit_rate_kbps_list[-history_window:]) / max_bit_rate
    smoothness_metric = np.var(bit_rate_changes)
    
    # Future chunk size ratio
    last_chunk_size_MB = video_chunk_size_bytes_list[-1] / (1000. * 1000.)
    future_chunk_size_ratio = [x / (last_chunk_size_MB * 1000. * 1000.) for x in next_chunk_bytes_sizes]
    
    # Normal states list
    normal_states = [
        [normed_last_bit_rate],
        [normed_last_buffer_size],
        [remaining_chunk_percentage],
        [smoothness_metric],
    ]
    
    # Time series states
    # Throughput in near history (standardized)
    throughput_MBps_list = np.array([
        video_chunk_size_bytes_list[-(history_window - i)] / (delay_second_list[-(history_window - i)] * 1000. * 1000.)
        for i in range(history_window)
    ])
    norm_throughput_MBps_list = (throughput_MBps_list - np.mean(throughput_MBps_list)) / np.std(throughput_MBps_list)

    # Download time (delay) in near history (standardized)
    normed_delay_list = (np.array(delay_second_list[-history_window:]) / delay_norm_factor - 1)

    # Exponential Moving Average of throughput and delay
    ema_throughput = np.average(throughput_MBps_list, weights=np.exp(np.arange(history_window)))
    ema_delay = np.average(normed_delay_list, weights=np.exp(np.arange(history_window)))
    
    # Buffer size trend
    buffer_size_trend = np.diff(buffer_size_second_list[-(history_window + 1):]) / buffer_norm_factor

    # Time series states list
    time_series_states = [
        norm_throughput_MBps_list.tolist(),
        normed_delay_list.tolist(),
        future_chunk_size_ratio,
        [ema_throughput],
        [ema_delay],
        buffer_size_trend.tolist(),
    ]

    # Return the states
    return {
        "normal_states": normal_states,
        "time_series_states": time_series_states,
    }

def init_gpt4_5g_state_func():
    return {
        "normal_states": [
            np.array([0.]),  # normed_last_bit_rate
            np.array([0.]),  # normed_last_buffer_size
            np.array([0.]),  # remaining_chunk_percentage
        ],
        "time_series_states": [
            np.array([0.] * 8),  # normed_bitrate_history
            np.array([0.] * 7),  # buffer_size_diffs
            np.array([0.] * 8),  # throughput_MBps_list
            np.array([0.] * 8),  # normed_delay_list
            np.array([0.] * 6),  # next_chunk_sizes_norm
            np.array([0.]),  # throughput_variance
        ],
    }


def gpt4_5g_state_func(
    bit_rate_kbps_list,
    buffer_size_second_list,
    delay_second_list,
    video_chunk_size_bytes_list,
    next_chunk_bytes_sizes,
    video_chunk_remain_num,
    total_chunk_num,
    all_bit_rate_kbps,
):
    # Constants for normalization
    buffer_norm_factor = 10.0
    delay_norm_factor = 10.0
    bitrate_norm_factor = np.max(all_bit_rate_kbps)
    size_norm_factor = 1000.0 * 1000.0  # for converting bytes to MB
    
    # Normalized last bit rate
    normed_last_bit_rate = bit_rate_kbps_list[-1] / bitrate_norm_factor
    # Normalized last buffer size (clipped to max 10 seconds)
    normed_last_buffer_size = np.clip(buffer_size_second_list[-1], 0, buffer_norm_factor) / buffer_norm_factor
    # Percentage of remaining video chunks
    remaining_chunk_percentage = video_chunk_remain_num / total_chunk_num

    # Normal state list
    normal_states = [
        [normed_last_bit_rate],
        [normed_last_buffer_size],
        [remaining_chunk_percentage],
    ]
    
    # Historical states for bit rates and buffer size differences
    history_window = 8  # for time series state
    
    normed_bitrate_history = [br / bitrate_norm_factor for br in bit_rate_kbps_list[-history_window:]]
    buffer_size_diffs = np.diff(buffer_size_second_list[-history_window - 1:]) / buffer_norm_factor
    buffer_size_diffs = np.clip(buffer_size_diffs, -1, 1).tolist()  # clip to ensure it stays in range [-1, 1]

    # Estimated throughput in near history normalized
    throughput_MBps_list = [(video_chunk_size_bytes_list[-(history_window - i)] / size_norm_factor) / delay_second_list[-(history_window - i)] for i in range(history_window)]
    
    # The normed download time (delay) in near history
    normed_delay_list = [(x / delay_norm_factor) for x in delay_second_list[-history_window:]]

    # Throughput stability (variance)
    throughput_variance = np.var(throughput_MBps_list) / np.var(all_bit_rate_kbps)

    # Sizes for the next chunk normalized
    next_chunk_sizes_norm = [size / size_norm_factor for size in next_chunk_bytes_sizes]

    # Time series states list
    time_series_states = [
        normed_bitrate_history,
        buffer_size_diffs,
        throughput_MBps_list,
        normed_delay_list,
        next_chunk_sizes_norm,
        [throughput_variance],  # included as a single-element list for consistency
    ]

    return {
        "normal_states": normal_states,
        "time_series_states": time_series_states,
    }
