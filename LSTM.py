import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import backend
from pandas import DataFrame
from pandas import Series
from pandas import concat
from pandas import read_csv
from pandas import datetime
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
# from tensorflow.keras.callbacks import Callbacks
from math import sqrt
from matplotlib import pyplot
from numpy import array
import time
import argparse

parser.add_argument('--n_lag', type=int, default=4,
                    help='tells the model how many weeks in the past to look at')
parser.add_argument('--n_seq', type=int, default=4,
                    help='tells the model how many weeks in the future to forecast')
parser.add_argument('--n_test', type=int, default=1,
                    help='number of weeks to take while testing')
parser.add_argument('--n_epochs', type=int, default=1000,
                    help='number of epochs to train the model for')
parser.add_argument('--n_batch', type=int, default=1,
                    help='size of each training batch')
parser.add_argument('--n_neurons', type=int, default=2,
                    help='number of neurons in one hidden layer of the model')
parser.add_argument('--data_path', type=str, default="/data/FluViewPhase2Data/ILINet.csv",
                    help='path to ILINet.csv')


args = parser.parse_args()
n_lag = n_lag
n_seq = n_seq  # 99
n_test = n_test
n_epochs = n_epochs
n_batch = n_batch
n_neurons = n_neurons
data_path = data_path

ind_og = pd.read_csv(data_path)
# ind = data.set_index(["WEEK"])
region = "Region"
ind = ind_og.loc[ind_og["REGION"] == "Region " + str(r)]
ind_next = ind_og[0:300]

from epiweeks import Week, Year

date = []
for item, row in ind.iterrows():
    week = Week(row["YEAR"], row["WEEK"])
    # print(row["YEAR"], row["WEEK"], week.startdate())
    date.append(week.startdate())
ind["DATE"] = date

new_ind = ind[['DATE', '% WEIGHTED ILI']]  # ,'WEEK']]
new_ind.index = new_ind['DATE']
series = new_ind.drop(['DATE'], axis=1)

all_32_forecasts = []

for r in range(1, 11):

    # date-time parsing function for loading the dataset
    def parser(x):
        return datetime.strptime('190' + x, '%Y-%m')


    # convert time series into supervised learning problem
    def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
        n_vars = 1 if type(data) is list else data.shape[1]
        df = DataFrame(data)
        cols, names = list(), list()
        # input sequence (t-n, ... t-1)
        for i in range(n_in, 0, -1):
            cols.append(df.shift(i))
            names += [('var%d(t-%d)' % (j + 1, i)) for j in range(n_vars)]
        # forecast sequence (t, t+1, ... t+n)
        for i in range(0, n_out):
            cols.append(df.shift(-i))
            if i == 0:
                names += [('var%d(t)' % (j + 1)) for j in range(n_vars)]
            else:
                names += [('var%d(t+%d)' % (j + 1, i)) for j in range(n_vars)]
        # put it all together
        agg = concat(cols, axis=1)
        agg.columns = names
        # drop rows with NaN values
        if dropnan:
            agg.dropna(inplace=True)
        return agg


    # create a differenced series
    def difference(dataset, interval=1):
        diff = list()
        for i in range(interval, len(dataset)):
            value = dataset[i] - dataset[i - interval]
            diff.append(value)
        return Series(diff)


    # transform series into train and test sets for supervised learning
    def prepare_data(series, n_test, n_lag, n_seq):
        # extract raw values
        raw_values = series.values
        # transform data to be stationary
        diff_series = difference(raw_values, 1)
        diff_values = diff_series.values
        diff_values = diff_values.reshape(len(diff_values), 1)
        # rescale values to -1, 1
        scaler = MinMaxScaler(feature_range=(-1, 1))
        scaled_values = scaler.fit_transform(diff_values)
        scaled_values = scaled_values.reshape(len(scaled_values), 1)
        # transform into supervised learning problem X, y
        supervised = series_to_supervised(scaled_values, n_lag, n_seq)
        supervised_values = supervised.values
        # split into train and test sets
        train, test = supervised_values[0:-n_test], supervised_values[-n_test:]
        return scaler, train, test


    # fit an LSTM network to training data
    def fit_lstm(train, n_lag, n_seq, n_batch, nb_epoch, n_neurons):
        # reshape training into [samples, timesteps, features]
        X, y = train[:, 0:n_lag], train[:, n_lag:]
        X = X.reshape(X.shape[0], 1, X.shape[1])
        # design network
        model = Sequential()
        model.add(
            LSTM(n_neurons, batch_input_shape=(n_batch, X.shape[1], X.shape[2]), stateful=True, return_sequences=True))
        model.add(LSTM(n_neurons, return_sequences=True))
        model.add(LSTM(n_neurons, return_sequences=True))
        model.add(LSTM(n_neurons))
        model.add(Dense(y.shape[1]))
        model.compile(loss='mean_squared_error', optimizer='adam')
        # fit network

        for i in range(nb_epoch):
            start = time.time()
            history = (model.fit(X, y, epochs=1, batch_size=n_batch, verbose=0, shuffle=False))
            end = time.time()
            # print(end-start)
            model.reset_states()
        return model, history


    # make one forecast with an LSTM,
    def forecast_lstm(model, X, n_batch):
        # reshape input pattern to [samples, timesteps, features]
        X = X.reshape(1, 1, len(X))
        # make forecast
        forecast = model.predict(X, batch_size=n_batch)
        # convert to array
        return [x for x in forecast[0, :]]


    # evaluate the persistence model
    def make_forecasts(model, n_batch, train, test, n_lag, n_seq):
        forecasts = list()
        for i in range(len(test)):
            X, y = test[i, 0:n_lag], test[i, n_lag:]
            # make forecast
            forecast = forecast_lstm(model, X, n_batch)
            # store the forecast
            forecasts.append(forecast)
        return forecasts


    # invert differenced forecast
    def inverse_difference(last_ob, forecast):
        # invert first forecast
        inverted = list()
        inverted.append(forecast[0] + last_ob)
        # propagate difference forecast using inverted first value
        for i in range(1, len(forecast)):
            inverted.append(forecast[i] + inverted[i - 1])
        return inverted


    # inverse data transform on forecasts
    def inverse_transform(series, forecasts, scaler, n_test):
        inverted = list()
        for i in range(len(forecasts)):
            # create array from forecast
            forecast = array(forecasts[i])
            forecast = forecast.reshape(1, len(forecast))
            # invert scaling
            inv_scale = scaler.inverse_transform(forecast)
            inv_scale = inv_scale[0, :]
            # invert differencing
            index = len(series) - n_test + i - 1
            last_ob = series.values[index]
            inv_diff = inverse_difference(last_ob, inv_scale)
            # store
            inverted.append(inv_diff)
        return inverted


    # evaluate the RMSE for each forecast time step
    def evaluate_forecasts(test, forecasts, n_lag, n_seq):
        for i in range(n_seq):
            actual = [row[i] for row in test]
            predicted = [forecast[i] for forecast in forecasts]
            rmse = sqrt(mean_squared_error(actual, predicted))
            print('t+%d RMSE: %f' % ((i + 1), rmse))


    # plot the forecasts in the context of the original dataset
    def plot_forecasts(ind_og, series, forecasts, n_test):
        # plot the entire dataset in blue
        pyplot.plot(series.values)
        # plot the forecasts in red
        for i in range(len(forecasts)):
            off_s = len(series) - n_test + i - 1
            off_e = off_s + len(forecasts[i]) + 1
            xaxis = [x for x in range(off_s, off_e)]
            yaxis = [series.values[off_s]] + forecasts[i]
            pyplot.plot(xaxis, yaxis, color='red')
            pyplot.plot(ind_og["% WEIGHTED ILI"], color='blue')
        # show the plot
        pyplot.show()


    # load dataset
    # series = read_csv('shampoo-sales.csv', header=0, parse_dates=[0], index_col=0, squeeze=True, date_parser=parser)
    # configure
    n_lag = 4
    n_seq = 4  # 99
    n_test = 1
    n_epochs = 1000
    n_batch = 1
    n_neurons = 2
    # prepare data
    scaler, train, test = prepare_data(series, n_test, n_lag, n_seq)
    # fit model
    model, history = fit_lstm(train, n_lag, n_seq, n_batch, n_epochs, n_neurons)
    # make forecasts
    forecasts = make_forecasts(model, n_batch, train, test, n_lag, n_seq)
    # inverse transform forecasts and test
    forecasts = inverse_transform(series, forecasts, scaler, n_test)  # +2)
    actual = [row[n_lag:] for row in test]
    actual = inverse_transform(series, actual, scaler, n_test)  # +2)
    # evaluate forecasts
    evaluate_forecasts(actual, forecasts, n_lag, n_seq)
    # plot forecasts
    plot_forecasts(ind_og, series, forecasts, n_test)  # +2)
    # prepare data
    # train, test = prepare_data(series, n_test, n_lag, n_seq)
    # # make forecasts
    # forecasts = make_forecasts(train, test, n_lag, n_seq)
    # # evaluate forecasts
    # evaluate_forecasts(test, forecasts, n_lag, n_seq)
    # # plot forecasts
    # plot_forecasts(series, forecasts, n_test+2)
    plt.plot(history.history["loss"])
    all_32_forecasts.append(forecasts)
