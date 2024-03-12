import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.style.use('seaborn-deep')
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 32
plt.rcParams['axes.labelsize'] = 32
plt.rcParams['axes.titlesize'] = 32
plt.rcParams['legend.fontsize'] = 32
plt.rcParams["figure.figsize"] = (9,5)
plt.rcParams['svg.fonttype'] = 'none'

SAVE_ROOT = "figs/"

def main():
    os.makedirs( SAVE_ROOT ,exist_ok=True )


    # ['sim_BBA: bitrate: 1.2% rebuf: 0.0585' ,'sim_RobustMPC: bitrate: 1.22% rebuf: 0.033' ,
    #  'sim_udr_1: bitrate: 1.2% rebuf: 0.0338' ,'sim_udr_2: bitrate: 1.04% rebuf: 0.0195' ,
    #  'sim_udr_3: bitrate: 1.1% rebuf: 0.0237' ,'sim_adr: bitrate: 1.11% rebuf: 0.0148']

    # ['BufferBased: bitrate: 30.14% rebuf: 0.03972', 
    #  'RL: bitrate: 21.65% rebuf: 0.04773', 
    #  'RobustMPC: bitrate: 29.82% rebuf: 0.00097']

    # ['Default: bitrate: 2.47% rebuf: 0.04477', 
    # 'GPT4: bitrate: 16.75% rebuf: 0.17186', 
    # 'GPT35: bitrate: 20.66% rebuf: 0.25374']

    plt.rcParams['font.size'] = 32
    plt.rcParams['axes.labelsize'] = 32
    plt.rcParams['axes.titlesize'] = 32
    plt.rcParams['legend.fontsize'] = 32
    fig1, ax1 = plt.subplots(figsize=(9, 5))

    fourg_default_bitrate, fourg_default_rebuf  = 2.47, 0.04477
    fourg_gpt4_bitrate, fourg_gpt4_rebuf = 16.75, 0.171786
    fourg_gpt35_bitrate, fourg_gpt35_rebuf = 20.66, 0.25374

    msize = 200

    ax1.scatter( [fourg_default_rebuf],[fourg_default_bitrate] ,marker='d' ,color='C0' ,s=msize ,label='Default' )
    ax1.scatter( [fourg_gpt4_rebuf] ,[fourg_gpt4_bitrate] ,marker='v' ,color='darkorange' ,s=msize ,label='GPT4' )
    ax1.scatter( [fourg_gpt35_rebuf] ,[fourg_gpt35_bitrate] ,marker='>' ,color='C1' ,s=msize ,label='GPT35' )

    # ax1.annotate('BBA', ( fourg_bb_bitrate, fourg_bb_bitrate-0.03))
    # ax1.annotate('MPC', ( fourg_mpc_bitrate, fourg_mpc_bitrate-0.01))
    # ax1.annotate('RL-GPT35', (fourg_mpc_bitrate+0.004, fourg_mpc_bitrate-0.025))

    # ax1.scatter( [fcc_bba_rebuf],[fcc_bba_bitrate] ,marker='d' ,color='C0' ,s=msize ,label='BBA' )
    # ax1.scatter( [fcc_mpc_rebuf] ,[fcc_mpc_bitrate] ,marker='>' ,color='C1' ,s=msize ,label='MPC' )
    # ax1.scatter( [fcc_oboe_rebuf] ,[fcc_oboe_bitrate] ,marker='v' ,color='darkorange' ,s=msize ,label='Oboe' )
    # ax1.scatter( [fcc_udr1_rebuf] , [fcc_udr1_bitrate] ,marker='^' ,color='C3' ,s=msize ,label='RL1' )
    # ax1.scatter( [fcc_udr2_rebuf] ,[fcc_udr2_bitrate] ,marker='<' ,color='C4' ,s=msize ,label='RL2' )
    # ax1.scatter( [fcc_udr3_rebuf] , [fcc_udr3_bitrate] , marker='p' ,color='C5' ,s=msize ,label='RL3' )
    # ax1.scatter( [fcc_genet_rebuf] ,[fcc_genet_bitrate] ,s=msize ,color='C2' ,label='Genet' )

    # ax1.annotate('BBA', ( fcc_bba_rebuf, fcc_bba_bitrate-0.03))
    # ax1.annotate('MPC', ( fcc_mpc_rebuf, fcc_mpc_bitrate-0.01))
    # ax1.annotate('Oboe', (fcc_oboe_rebuf+0.004, fcc_oboe_bitrate-0.025))
    # ax1.annotate('RL1', (fcc_udr1_rebuf+0.002, fcc_udr1_bitrate-0.03))
    # ax1.annotate('RL2', (fcc_udr2_rebuf+0.003, fcc_udr2_bitrate+0.01))
    # ax1.annotate('RL3', (fcc_udr3_rebuf+0.007, fcc_udr3_bitrate-0.01))
    # ax1.annotate('Genet', ( fcc_genet_rebuf+0.005, fcc_genet_bitrate+0.02))

    ax1.set_ylabel('Bitrate (Mbps)')
    ax1.set_yticks( [0, 10, 20, 30] )
    ax1.set_xlabel('90th percentile rebuffering ratio (%)')
    ax1.set_xticks([0.05, 0.1, 0.15, 0.2, 0.25])
    ax1.invert_xaxis()
    ax1.spines['top'].set_visible( False )
    ax1.spines['right'].set_visible( False )
    #ax.set_ylim(0.03, -0.01)

    fig1.legend(bbox_to_anchor=(0, 1.02, 1, 0.14), ncol=4, loc="upper center",
                borderaxespad=0, borderpad=0.2, columnspacing=0.01, handletextpad=0.001)

    # svg_file = os.path.join( SAVE_ROOT ,'mahi_fcc_arrow.svg' )
    pdf_file = os.path.join( SAVE_ROOT ,'mahi_4g_arrow.pdf' )
    fig1.savefig( pdf_file ,bbox_inches='tight' )



    # os.system( "inkscape {} --export-pdf={}".format( svg_file ,pdf_file ) )
    # os.system( "pdfcrop --margins 1 {} {}".format( pdf_file ,pdf_file ) )

    fig2, ax2 = plt.subplots(figsize=(9, 5))

    # ['sim_BBA: bitrate: 1.03% rebuf: 0.07658' ,'sim_RobustMPC: bitrate: 1.05% rebuf: 0.05053' ,
    #  'sim_udr_1: bitrate: 1.04% rebuf: 0.07323' ,'sim_udr_2: bitrate: 0.96% rebuf: 0.04276' ,
    #  'sim_udr_3: bitrate: 0.95% rebuf: 0.04796' ,'sim_adr: bitrate: 0.95% rebuf: 0.04498']

    # ['Default: bitrate: 23.5% rebuf: 0.24065', 'GPT35: bitrate: 23.44% rebuf: 0.24855']

    fiveg_default_bitrate ,fiveg_default_rebuf = 23.5 ,0.24065
    fiveg_gpt35_bitrate ,fiveg_gpt35_rebuf = 23.44 ,0.24855


    ax2.scatter( [fiveg_default_rebuf], [fiveg_default_bitrate] ,marker='d', color='C0', s=msize ,label='Default' )
    ax2.scatter( [fiveg_gpt35_rebuf] ,[fiveg_gpt35_bitrate] ,marker='>' ,color='C1',s=msize ,label='GPT35' )

    ax2.set_ylabel( 'Bitrate (Mbps)' )
    ax2.set_yticks( [0, 10, 20, 30] )
    ax2.set_xlabel( '90th percentile rebuffering ratio (%)' )
    ax2.set_xticks([0.05, 0.1, 0.15, 0.2, 0.25])
    ax2.invert_xaxis()
    ax2.spines['top'].set_visible( False )
    ax2.spines['right'].set_visible( False )

    fig2.legend(bbox_to_anchor=(0, 1.02, 1, 0.14), ncol=4, loc="upper center",
                borderaxespad=0, borderpad=0.2, columnspacing=0.01, handletextpad=0.001)

    pdf_file = os.path.join( SAVE_ROOT , 'mahi_5g_arrow.pdf')
    fig2.savefig( pdf_file ,bbox_inches='tight' )
    # os.system( "inkscape {} --export-pdf={}".format( svg_file ,pdf_file ) )
    # os.system("pdfcrop --margins 1 {} {}".format(pdf_file, pdf_file))



if __name__ == '__main__':
    main()