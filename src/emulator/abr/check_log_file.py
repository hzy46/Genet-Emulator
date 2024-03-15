import fire
import pandas as pd
import os

def main(path):
    if os.path.exists(path) is True:
        try:
            trace_df = pd.read_csv(path, delimiter="\t")
            assert len(trace_df) == 49
        except Exception as e:
            print("will delete {}".format(path))
            os.remove(path)

if __name__ == '__main__':
    fire.Fire(main)