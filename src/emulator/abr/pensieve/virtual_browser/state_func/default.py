import numpy as np

def init_default_state_func():
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
        ],
    }

def default_state_func(
    # historical bit rates in kbps, candidate values can be [300., 750., 1200., 1850., 2850., 4300.]
    # bit_rate_kbps_list[-1] is the most recent bit rate.
    # For example, [300, 750, ..., 1200, 1850, 4300, 4300] means the last two chunks we downloaded is 4300kbps.
    bit_rate_kbps_list,
    # historical buffer size (buffered video length) in second
    # buffer_size_second_list[-1] is the most recent buffer size.
    buffer_size_second_list,
    # historical delay (download time of the chunk) in second
    # delay_second_list[-1] is the download time of the most recent downloaded chunk.
    delay_second_list,
    # historical downloaded video chunk sizes in bytes
    # video_chunk_size_bytes_list[-1] is the size of the most recent downloaded chunk.
    # Thus video_chunk_size_bytes_list[-1] / delay_second_list[-1] is the download throughtput of the most recent chunks
    video_chunk_size_bytes_list,
    # The sizes of the next one chunk in different bit rate levels.
    # For example, this can be [181801, 450283, 668286, 1034108, 1728879, 2354772],
    # which means the next chunk will be 181801 bytes if we select 300kbps (all_bit_rate_kbps[0]); is 450283 bytes if we select 750kbps(all_bit_rate_kbps[1])
    # We always have len(next_chunk_bytes_sizes) = len(all_bit_rate_kbps)
    next_chunk_bytes_sizes,
    # How many remaining video chunks there are. It is a single number
    video_chunk_remain_num,
    # A single number. total_chunk_num is 48 in most cases.
    total_chunk_num,
    # all_bit_rate_kbps=[300., 750., 1200., 1850., 2850., 4300.] in most cases
    all_bit_rate_kbps,
):
    # normal state 1: The normed last bit rate
    normed_last_bit_rate = bit_rate_kbps_list[-1] / float(np.max(all_bit_rate_kbps))
    # normal state 2: The normed last buffer size second (buffered video second)
    buffer_norm_factor = 10.
    normed_last_buffer_size = buffer_size_second_list[-1] / buffer_norm_factor # in 10-second
    # normal state 3: The percentage of the remaining video chunks.
    remaining_chunk_percentage = float(video_chunk_remain_num / total_chunk_num)
    # Finally, the normal states. Each entry in normal_states should be a list.
    normal_states = [
        [normed_last_bit_rate],
        [normed_last_buffer_size],
        [remaining_chunk_percentage],
    ]

    # time series states
    # use 8 as the time series length for time series state 1 and 2
    history_window = 8
    # time series state 1: Estimated throughput in near history
    # use the unit mega byte per second (it is equiv to kilo byte / ms)
    throughput_MBps_list = []
    for i in range(history_window):
        history_chunk_size_bytes = video_chunk_size_bytes_list[-(history_window - i)]
        history_delay_second = delay_second_list[-(history_window - i)]
        throughput_MBps_list.append(history_chunk_size_bytes / 1000. / 1000. / history_delay_second)
    # time series state 2: The normed download time (delay) in near history
    delay_norm_factor = 10.
    normed_delay_list = [x / delay_norm_factor for x in delay_second_list]
    # time series state 3: Treat next chunk sizes in MB as ts states, too. We use Mega Byte since Byte is too large for NN.
    next_chunk_bytes_MB = [x / 1000. / 1000. for x in next_chunk_bytes_sizes]
    # Finally, the time series states. Each entry in timeseries_states should be a list.
    time_series_states = [
        throughput_MBps_list,
        normed_delay_list,
        next_chunk_bytes_MB,
    ]

    # Return the states
    return {
        "normal_states": normal_states,
        "time_series_states": time_series_states,
    }