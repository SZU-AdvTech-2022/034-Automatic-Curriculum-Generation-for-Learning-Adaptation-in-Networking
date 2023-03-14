import os
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 14})

RESULTS_FOLDER = '../sigcomm_artifact/norway/'
TRACE_FOLDER = '../data/mahimahi_trace/norway_mahimahi/'
NUM_BINS = 100
BITS_IN_BYTE = 8.0
MILLISEC_IN_SEC = 1000.0
M_IN_B = 1000000.0
VIDEO_LEN = 48
VIDEO_BIT_RATE = [300, 750, 1200, 1850, 2850, 4300]  # Kbps
K_IN_M = 1000.0
REBUF_P = 10
SMOOTH_P = 1
COLOR_MAP = plt.cm.jet #nipy_spectral, Set1,Paired 
SIM_DP = 'sim_dp'
SCHEMES = ['sim_udr_real', 'sim_udr_1', 'sim_udr_2', 'sim_udr_3', 'sim_adr']


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
    bit_rate_all = {}
    buff_all = {}
    bw_all = {}
    raw_reward_all = {}

    for scheme in SCHEMES:
        time_all[scheme] = {}
        raw_reward_all[scheme] = {}
        bit_rate_all[scheme] = {}
        buff_all[scheme] = {}
        bw_all[scheme] = {}

    log_files = os.listdir(RESULTS_FOLDER)
    for log_file in log_files:

        time_ms = []
        bit_rate = []
        buff = []
        bw = []
        reward = []

        #print(log_file)

        with open(RESULTS_FOLDER + log_file, 'r') as f:
            if SIM_DP in log_file:
                last_t = 0
                last_b = 0
                last_q = 1
                lines = []
                for line in f:
                    lines.append(line)
                    parse = line.split()
                    if len(parse) >= 6:
                        time_ms.append(float(parse[3]))
                        bit_rate.append(VIDEO_BIT_RATE[int(parse[6])])
                        buff.append(float(parse[4]))
                        bw.append(float(parse[5]))

                for line in reversed(lines):
                    parse = line.split()
                    r = 0
                    if len(parse) > 1:
                        t = float(parse[3])
                        b = float(parse[4])
                        q = int(parse[6])
                        if b == 4:
                            rebuff = (t - last_t) - last_b
                            assert rebuff >= -1e-4
                            r -= REBUF_P * rebuff

                        r += VIDEO_BIT_RATE[q] / K_IN_M
                        r -= SMOOTH_P * np.abs(VIDEO_BIT_RATE[q] - VIDEO_BIT_RATE[last_q]) / K_IN_M
                        reward.append(r)

                        last_t = t
                        last_b = b
                        last_q = q

            else:
                for line in f:
                    parse = line.split()
                    if len(parse) <= 1:
                        break
                    time_ms.append(float(parse[0]))
                    bit_rate.append(int(parse[1]))
                    buff.append(float(parse[2]))
                    bw.append(float(parse[4]) / float(parse[5]) * BITS_IN_BYTE * MILLISEC_IN_SEC / M_IN_B)
                    reward.append(float(parse[-1]))
                #print( reward, "--------------------" )


        if SIM_DP in log_file:
            time_ms = time_ms[::-1]
            bit_rate = bit_rate[::-1]
            buff = buff[::-1]
            bw = bw[::-1]

        time_ms = np.array(time_ms)
        time_ms -= time_ms[0]

        # print log_file

        for scheme in SCHEMES:
            if scheme in log_file:
                time_all[scheme][log_file[len('log_' + str(scheme) + '_'):]] = time_ms
                bit_rate_all[scheme][log_file[len('log_' + str(scheme) + '_'):]] = bit_rate
                buff_all[scheme][log_file[len('log_' + str(scheme) + '_'):]] = buff
                bw_all[scheme][log_file[len('log_' + str(scheme) + '_'):]] = bw
                raw_reward_all[scheme][log_file[len('log_' + str(scheme) + '_'):]] = reward
                break

    # ---- ---- ---- ----
    # Reward records
    # ---- ---- ---- ----

    log_file_all = []
    reward_all = {}
    for scheme in SCHEMES:
        reward_all[scheme] = []


    for l in time_all[SCHEMES[0]]:
        # what is l here?
        # l will be something like "norway_ferry_7", representing the name of a trace
        # print(l)

        # assume that the schemes are okay, then flip the flag if they are not
        schemes_check = True

        # all schemes must pass the check
        for scheme in SCHEMES:
            # print(l not in time_all[scheme])
            # check 1: l is a trace name. is the trace name found in every scheme? if not, we fail
            # check 2: is the length of the log for trace "l" less than the video length? if not, we fail
            if l not in time_all[scheme] or len(time_all[scheme][l]) < VIDEO_LEN:
                # print all the bad ls
                # print(l)
                # print(scheme)
                schemes_check = False
                break
        if schemes_check:
            log_file_all.append(l)
            for scheme in SCHEMES:
                #print(raw_reward_all[scheme], "----------------------")
                reward_all[scheme].append(np.sum(raw_reward_all[scheme][l][1:VIDEO_LEN])/VIDEO_LEN)
    #print(reward_all[scheme], scheme)


    mean_rewards = {}
    error_bar = {}
    for scheme in SCHEMES:
        mean_rewards[scheme] = np.mean(reward_all[scheme])
        mean_rewards[scheme] = round(mean_rewards[scheme], 3)
        error_bar[scheme] = np.var(reward_all[scheme])/100
        error_bar[scheme] = round(error_bar[scheme], 4)

    SCHEMES_REW = []
    for scheme in SCHEMES:
        SCHEMES_REW.append(scheme + ': ' + str(mean_rewards[scheme])  + '% ' + str(error_bar[scheme]))
        # SCHEMES_REW.append(scheme + ': ' + str(mean_rewards[scheme]))

    print(SCHEMES_REW)

    column_wid = 0.7
    capsize_wid = 8
    eline_wid = 2

    x = [1, 2, 3, 4, 5]


    labels = ['RL1', 'RL2', 'RL3', 'RL-real', 'Genet']

    #['sim_udr_real: 0.487% 0.0204', 'sim_udr_1: 0.009% 0.0294', 'sim_udr_2: 0.372% 0.0198', 'sim_udr_3: 0.368% 0.0193', 'sim_adr: 0.585% 0.0152']

    norway_BBA = [0.1]
    norway_MPC = [0.3]
    norway_UDR_1 = mean_rewards['sim_udr_1'] # [0.01]
    norway_UDR_2 = mean_rewards['sim_udr_2'] # [0.37]
    norway_UDR_3 = mean_rewards['sim_udr_3'] # [0.368]
    norway_UDR_real = mean_rewards['sim_udr_real'] # [0.487]

    norway_genet = mean_rewards['sim_adr'] # [0.585]

    norway_BBA_err = [0.017]
    norway_MPC_err = [0.021]

    norway_UDR_1_err = error_bar['sim_udr_1'] # [0.029]
    norway_UDR_2_err = error_bar['sim_udr_2'] # [0.019]
    norway_UDR_3_err = error_bar['sim_udr_3'] # [0.019]
    norway_UDR_real_err = error_bar['sim_udr_real'] # [0.02]

    norway_genet_err = error_bar['sim_adr'] # [0.015]

    # ax2.bar( x[0] ,norway_BBA ,yerr=norway_BBA_err ,width=column_wid ,error_kw=dict( lw=eline_wid ,capsize=capsize_wid ) ,color='C0' )
    # ax2.bar( x[1] ,MPC ,yerr=norway_MPC_err ,width=column_wid ,error_kw=dict( lw=eline_wid ,capsize=capsize_wid ) ,color='C0' ,
    #          hatch='x' )

    fig ,ax2 = plt.subplots()

    ax2.bar( x[0] ,norway_UDR_1 ,yerr=norway_UDR_1_err ,width=column_wid ,error_kw=dict( lw=eline_wid ,capsize=capsize_wid ) ,
             color='C0',hatch='/' )
    ax2.bar( x[1] ,norway_UDR_2 ,yerr=norway_UDR_2_err ,width=column_wid ,error_kw=dict( lw=eline_wid ,capsize=capsize_wid ) ,
            color='C0' ,alpha=1 ,hatch='\\')
    ax2.bar( x[2] ,norway_UDR_3 ,yerr=norway_UDR_3_err ,width=column_wid ,error_kw=dict( lw=eline_wid ,capsize=capsize_wid ) ,
             color='C0' ,alpha=1 ,hatch='x' )
    ax2.bar( x[3] ,norway_UDR_real ,yerr=norway_UDR_real_err ,width=column_wid ,error_kw=dict( lw=eline_wid ,capsize=capsize_wid ) ,
             color='C0' ,alpha=1 ,hatch='o' )

    ax2.bar( x[4] ,norway_genet ,yerr=norway_genet_err ,width=column_wid ,error_kw=dict( lw=eline_wid ,capsize=capsize_wid ) ,
             color='C2' ,alpha=1 )
    ax2.set_xticks( x )
    #ax2.set_title( "Norway trace" )
    ax2.set_ylabel( 'Test reward' )
    ax2.set_xticklabels( labels ,rotation=20 )

    ax2.spines['right'].set_visible( False )
    ax2.spines['top'].set_visible( False )

    ax2.tick_params(
        axis='x' ,  # changes apply to the x-axis
        which='both' ,  # both major and minor ticks are affected
        bottom=False ,  # ticks along the bottom edge are off
        top=False )  # ticks along the top edge are off

    # svg_file = os.path.join( SAVE_ROOT ,'norway_test.svg' )
    # pdf_file = os.path.join( SAVE_ROOT ,'norway_test.pdf' )
    # fig.savefig( svg_file ,bbox_inches='tight' )
    # os.system( "inkscape {} --export-pdf={}".format( svg_file ,pdf_file ) )
    # os.system( "pdfcrop --margins 1 {} {}".format( pdf_file ,pdf_file ) )

    plt.savefig('fig13_abr_norway.png')



if __name__ == '__main__':
    main()
