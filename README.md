## Environment setup
1. Create the environment from the environment.yml file:

```
conda env create -f environment.yml
```

The first line of the yml file sets the new environment's name. 

2. Activate the new environment: 
```
conda activate myenv
```
3. Verify that the new environment was installed correctly:
```
conda env list
```

## Generating point forecasts
1. Run the model file to generate point forecasts
```
arguments with default values:
n_lag = 4
n_seq = 4  # 99
n_test = 1
n_epochs = 1000
n_batch = 1
n_neurons = 2
data_path = /Data/FluViewPhase2Data/ILINet.csv
```
Example:
```
python LSTM.py --n_lag 4 --n_seq 4 --n_test 1 --n_epochs 1000 --n_batch 1 n_neurons 2 --data_path /path/to/data


```