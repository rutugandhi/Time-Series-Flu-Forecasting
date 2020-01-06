import math
from scipy.stats import norm
import numpy as np

# def four_week_ahead_bins(point, std_dev):
num_std_dev = 2


def point_and_bins(pred, num_std_dev, std_dev=0.3):
    # pred = 2.06532243
    x = np.linspace(pred - num_std_dev, pred + num_std_dev, 100)
    rv = norm(pred, 0.3)

    all_bins = np.arange(0, 13.1, 0.1)

    # def four_week_bins():
    bin_prob = [pred, rv.cdf(all_bins[0])]
    for i in range(130):
        bin_prob.append(rv.cdf(all_bins[i + 1]) - rv.cdf(all_bins[i]))

    return bin_prob


bin_prob = point_and_bins(1.07543445, 2)

import pandas as pd
full = pd.read_csv("/home/rutu/flu-challenge-master/forecasts-formatted/EW44-CEID-2018-11-12.csv")

full[((full["Location"]=="HHS Region 1") & (full["Target"]=="4 wk ahead")) ]["Value"]=bin_prob