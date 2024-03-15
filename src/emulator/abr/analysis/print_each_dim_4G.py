import os
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 14})

RESULTS_FOLDER = '../emu_results/4G/'
#RESULTS_FOLDER = '../Oboe_results/synthetic/'
TRACE_FOLDER = '../data/4G/'
NUM_BINS = 100
BITS_IN_BYTE = 8.0
MILLISEC_IN_SEC = 1000.0
M_IN_B = 1000000.0
VIDEO_LEN = 48
VIDEO_BIT_RATE = [1850, 2850, 4300, 12000, 24000, 53000]  # Kbps
K_IN_M = 1000.0
REBUF_P = 10
SMOOTH_P = 1
COLOR_MAP = plt.cm.jet #nipy_spectral, Set1,Paired 
SIM_DP = 'sim_dp'
SCHEMES = ['Default', 'GPT4', 'GPT35']
# SCHEMES = ['BufferBased', 'RL', 'RobustMPC']
# SCHEMES = ['BufferBased', 'GPT4', 'GPT35', 'Default' 'RobustMPC']


def compute_cdf(data):
    """ Return the cdf of input data.

    Args
        data(list): a list of numbers.

    Return
        sorted_data(list): sorted list of numbers.

    """
    length = len(data)
    sorted_data = sorted(data)
    cdf = [i / length for i, val in enumerate(sorted_data)]
    return sorted_data, cdf


def main():
    time_all = {}
    raw_bit_rate_all = {}
    raw_rebuf_all = {}
    bw_all = {}
    raw_reward_all = {}
    raw_smooth_all = {}
    total_rebuf_time={}
    rebuf_ratio = {}

    for scheme in SCHEMES:
        time_all[scheme] = {}
        raw_reward_all[scheme] = {}
        raw_bit_rate_all[scheme] = {}
        raw_rebuf_all[scheme] = {}
        bw_all[scheme] = {}
        raw_smooth_all[scheme] = {}

        total_rebuf_time[scheme] = {}
        rebuf_ratio[scheme] = {}

    log_files = os.listdir(RESULTS_FOLDER)
    for log_file in log_files:
        skip_log = False

        time_ms = []
        bit_rate = []
        buff = []
        bw = []
        reward = []
        rebuf = []

        smooth =[]

        #print(log_file)
        with open(RESULTS_FOLDER + log_file, 'r') as f:
            lines = f.readlines()
            if len(lines) < VIDEO_LEN:
                # skip logs where model fails to stream
                print('skipping', log_file)
                skip_log = True
                continue
            for i, line in enumerate(lines):
                if i == 0:
                    continue # skip the headers
                parse = line.split()
                if len(parse) <= 1:
                    break
                print(line)
                time_ms.append(float(parse[0]))
                bit_rate.append(int(parse[1]))
                buff.append(float(parse[2]))
                bw.append(float(parse[4]) / max(float(parse[5]), 1e-6) * BITS_IN_BYTE * MILLISEC_IN_SEC / M_IN_B)
                rebuf.append(float(parse[3]))
                smooth.append(float(parse[6]))
                reward.append(float(parse[7]))
            #print( reward, "--------------------" )
        if not skip_log:
            time_ms = np.array(time_ms)
            time_ms -= time_ms[0]

            # print log_file

            for scheme in SCHEMES:
                if scheme in log_file:
                    time_all[scheme][log_file[len('log_' + str(scheme) + '_'):]] = time_ms

                    raw_bit_rate_all[scheme][log_file[len('log_' + str(scheme) + '_'):]] = bit_rate
                    raw_rebuf_all[scheme][log_file[len('log_' + str(scheme) + '_'):]] = rebuf
                    bw_all[scheme][log_file[len('log_' + str(scheme) + '_'):]] = bw
                    raw_smooth_all[scheme][log_file[len('log_' + str(scheme) + '_'):]] = smooth
                    raw_reward_all[scheme][log_file[len('log_' + str(scheme) + '_'):]] = reward

                    # cal rebuf ratio
                    total_rebuf_time[scheme][log_file[len('log_' + str(scheme) + '_'):]] = 0

                    for i in raw_rebuf_all[scheme][log_file[len('log_' + str(scheme) + '_'):]]:
                        if i > 0.0:
                            total_rebuf_time[scheme][log_file[len('log_' + str(scheme) + '_'):]] += i

                    rebuf_ratio[scheme][log_file[len('log_' + str(scheme) + '_'):]] = \
                        (total_rebuf_time[scheme][log_file[len( 'log_' + str( scheme ) + '_' ):]] /  time_all[scheme][log_file[len('log_' + str(scheme) + '_'):]][-1])

                    break

        #print(rebuf_ratio)
    # ---- ---- ---- ----
    # Reward records
    # ---- ---- ---- ----


    N_TRACES = 9
    N_TRIALS = 3
    print('Traces passed: ', len(raw_bit_rate_all['GPT4'].keys())/(N_TRACES * N_TRIALS), '\n')
    print('Traces passed: ', len(raw_bit_rate_all['GPT35'].keys())/(N_TRACES * N_TRIALS), '\n')
    print('Traces passed: ', len(raw_bit_rate_all['Default'].keys())/(N_TRACES * N_TRIALS), '\n')

    all_failed = True
    for scheme in SCHEMES:
        if len(raw_bit_rate_all[scheme].keys()) > 0:
            all_failed = False
            break
    if all_failed:
        print('All schemes failed. No plots.')
        exit(0)

    log_file_all = []
    reward_all = {}
    bit_rate_all = {}
    rebuf_all = {}
    smooth_all = {}
    rebuf_ratio_all = {}

    for scheme in SCHEMES:
        reward_all[scheme] = []
        bit_rate_all[scheme] = []
        rebuf_all[scheme] = []
        smooth_all[scheme] = []
        rebuf_ratio_all[scheme] = []

    
    for scheme in SCHEMES:
        for l in raw_bit_rate_all[scheme].keys():
            reward_all[scheme].append(np.sum(raw_reward_all[scheme][l][1:VIDEO_LEN])/VIDEO_LEN)
            bit_rate_all[scheme].append(np.sum(raw_bit_rate_all[scheme][l][1:VIDEO_LEN])/VIDEO_LEN)
            rebuf_all[scheme].append(np.sum(raw_rebuf_all[scheme][l][1:VIDEO_LEN])/VIDEO_LEN)
            smooth_all[scheme].append(np.sum(raw_smooth_all[scheme][l][1:VIDEO_LEN])/VIDEO_LEN)
            rebuf_ratio_all[scheme].append((rebuf_ratio[scheme][l]))

    mean_rewards = {}
    error_bar = {}

    mean_bitrate = {}
    mean_rebuf={}
    mean_smooth ={}
    per_rebuf={}
    mean_rebuf_ratio={}

    for scheme in SCHEMES:
        mean_rewards[scheme] = np.mean(reward_all[scheme])
        mean_rewards[scheme] = round(mean_rewards[scheme], 3)
        error_bar[scheme] = np.var(reward_all[scheme])/100
        error_bar[scheme] = round(error_bar[scheme], 4)

        mean_bitrate[scheme] = round(np.mean(bit_rate_all[scheme])/K_IN_M, 2)
        mean_rebuf[scheme] = round(np.mean(rebuf_all[scheme]), 3)

        per_rebuf[scheme] = round(np.percentile(rebuf_all[scheme], 90), 3)
        mean_smooth[scheme] = round(np.mean(smooth_all[scheme]), 3)

        #mean_rebuf_ratio[scheme] = round(np.mean(rebuf_ratio_all[scheme]), 4)
        mean_rebuf_ratio [scheme] = round(np.percentile(rebuf_ratio_all[scheme], 90), 5)

    print(mean_rebuf_ratio, "--------mean_rebuf_ratio")

    fig = plt.figure()
    ax = fig.add_subplot(111)


    for scheme in SCHEMES:
        ax.plot(reward_all[scheme])

    SCHEMES_REW = []
    for scheme in SCHEMES:
        SCHEMES_REW.append(scheme + ': ' + 'bitrate: ' + str(mean_bitrate[scheme])
                           + '% ' + 'rebuf: ' + str(mean_rebuf_ratio[scheme]))

        # SCHEMES_REW.append(scheme + ': ' + str(mean_rewards[scheme]))


    # colors = [COLOR_MAP(i) for i in np.linspace(0, 1, len(ax.lines))]
    # for i,j in enumerate(ax.lines):
    #     j.set_color(colors[i])

    print(SCHEMES_REW)
    plot_metric_bar(reward_all, 'Mean QoE Score', 'State Design', './figs/4G', 'reward_4G.png')
    plot_metric_cdf(reward_all, 'QoE Score', './figs/4G', 'reward_cdf_4G.png')
    plot_metric_bar(bit_rate_all, 'Mean bitrate (Mbps)', 'State Design', './figs/4G', 'mean_bitrate_4G.png')
    plot_metric_cdf(bit_rate_all, 'bitrate (Mbps)', './figs/4G', 'bitrate_cdf_4G.png')
    plot_metric_bar(rebuf_all, 'Mean rebuf', 'State Design', './figs/4G', 'mean_rebuf_4G.png')
    plot_metric_cdf(rebuf_all, 'rebuf', './figs/4G', 'rebuf_cdf_4G.png')
    plot_metric_bar(smooth_all, 'Mean smoothness', 'State Design', './figs/4G', 'mean_smooth_4G.png')
    plot_metric_cdf(smooth_all, 'smoothness', './figs/4G', 'smooth_cdf_4G.png')

def plot_metric_bar(metric, ylabel, xlabel, directory, filename):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i, scheme in enumerate(SCHEMES):
        if 'bitrate' in ylabel or 'smooth' in ylabel:
            ax.bar(i, np.mean(metric[scheme]) / K_IN_M)
        else:
            ax.bar(i, np.mean(metric[scheme]), yerr=np.var(metric[scheme]))
    ax.set_xticks(np.arange(len(SCHEMES)))
    ax.set_xticklabels(SCHEMES, rotation=30)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    # create dir if not exist
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    plt.savefig(f'{directory}/{filename}', bbox_inches='tight', dpi=300)
    plt.clf()

def plot_metric_cdf(metric, xlabel, directory, filename):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i, scheme in enumerate(SCHEMES):
        val = np.array(metric[scheme])
        if 'bitrate' in xlabel or 'smooth' in xlabel:
            sorted_metric, cdf = compute_cdf(val / K_IN_M)
        else:
            sorted_metric, cdf = compute_cdf(val)
        ax.plot(sorted_metric, cdf, label=scheme)
    plt.ylabel('CDF')
    plt.xlabel(xlabel)
    plt.legend()
    # create dir if not exist
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    plt.savefig(f'{directory}/{filename}', bbox_inches='tight', dpi=300)
    plt.clf()

if __name__ == '__main__':
    main()
