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
2. This step stores all the point forecasts to a file which is used by the points to bins converter in the next section.

## Points to Bins
1. Run the points to bins converter.
```
arguments with default values:
sample_submission = "/submissions/WEEK-CEID-2019.csv"
weeks_ahead = 1
location = "HHS Region 1"

```

Example:
```
python pointsAndBins.py --sample_submission = /path/to/file --weeks_ahead 1 --location "HHS Region 1"

```