import glob
import os


def rename_files(dir):
    for file in glob.glob(dir + '/*'):
        if 'GPT35' in dir:
            new_file = file.replace('RL', 'GPT35')
            os.rename(file, new_file)
        elif 'GPT4' in dir:
            new_file = file.replace('RL', 'GPT4')
            os.rename(file, new_file)
        elif 'Default' in dir:
            new_file = file.replace('RL', 'Default')
            os.rename(file, new_file)

# rename_files('./GPT35_60_40_4G')
# rename_files('./GPT4_60_40_4G')
# rename_files('./Default_60_40_4G')