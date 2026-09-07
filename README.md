# Encrypted Neural Controller for a Differential-Drive Robot

This repository contains the code used to reproduce the differential-drive robot experiment presented in the paper. The complete workflow is:

1. collect the Webots training dataset with the Kanayama controller;
2. train the neural network and export its weights and normalization values;
3. run the Webots client against the inference server in three modes: Kanayama, plaintext neural network, and CKKS encrypted neural network;
4. move the generated result files to the repository root; and
5. run one result script to print the paper metrics and display the figures.

The instructions below assume that commands are executed from the repository root unless another location is stated explicitly.

---

## Repository structure

```text
FHE_NN_Controller_DifferentialDrive/
|
|-- data_collector.py
|-- train.py
|-- client.py
|-- server.py
|-- requirements.txt
|-- README.md
|
|-- Webots/
|   |-- model_export.json                 # copy here after training
|   |-- webots_dataset.npz                # generated during data collection
|   |-- run_data_webots_*.npz             # generated during evaluation
|   |
|   |-- controllers/
|   |   `-- robot_controller/
|   |       `-- robot_controller.py       # file actually executed by Webots
|   |
|   `-- world/
|       `-- world.wbt
|
`-- scripts/
    `-- results.py
```

The files `webots_dataset.npz`, `model_export.json`, `run_data_webots_*.npz`, and `server_processing_times_*.npz` are generated during the experiment.

---

# 1. Software requirements

You need:

- Webots;
- Python;
- the Python packages listed in `requirements.txt`.

Install the Python dependencies from the repository root:

```bash
pip install -r requirements.txt
```

The Webots controller must use a Python interpreter in which the required packages are installed. If Webots reports an error such as `ModuleNotFoundError`, check which Python executable Webots is using and install the packages into that same Python environment.

You can quickly test the main Python dependencies from a terminal with:

```bash
python -c "import numpy, scipy, torch; print('NumPy/SciPy/PyTorch OK')"
```

For CKKS execution, also check TenSEAL:

```bash
python -c "import tenseal; print('TenSEAL OK')"
```

The data collector and Webots client must be executed by Webots, not directly with `python data_collector.py` or `python client.py`, because they use the Webots `controller` API.

---

# 2. Experiment configuration used in the paper

## Robot and control settings

- Webots simulation step: `10 ms`
- Controller update period: `100 ms`
- Wheel radius: `0.04445 m`
- Wheelbase: `0.393 m`
- Wheel-speed limit: `+/-10 rad/s`
- Kanayama gains:
  - `Kx = 2.0`
  - `Ky = 9.0`
  - `Ktheta = 6.0`

The robot state used by the controller contains position, heading, and measured translational speed. The neural-network input contains six features:

```text
[e_x, e_y, e_theta, v_ref, v_robot, omega_ref]
```

The target output contains the right and left wheel speeds:

```text
[wr, wl]
```

## Training dataset

The training dataset uses these eight reference trajectories:

1. lemniscate
2. circle
3. rounded square
4. spiral
5. rose
6. clover
7. hypotrochoid
8. random spline

The Lissajous trajectory is not used for training. It is reserved for the final evaluation.

Dataset settings:

- 40 rollouts per training trajectory
- random seed: `42`
- position perturbation: `+/-0.3 m`
- heading perturbation: `+/-0.7 rad`
- velocity perturbation: `+/-0.10 m/s`
- expected number of feature-target pairs: `192,680`

## Neural network

- inputs: `6`
- hidden neurons: `64`
- outputs: `2`
- hidden activation:

```text
p(z) = z + 0.125 z^2
```

Training settings:

- optimizer: AdamW
- epochs: `16`
- batch size: `1024`
- learning rate: `3e-3`
- weight decay: `1e-5`

## CKKS parameters

- polynomial modulus degree: `8192`
- coefficient modulus bits: `[40, 30, 30, 30, 30, 40]`
- global scale: `2^30`
- Galois keys: enabled
- relinearization keys: enabled

## Evaluation trajectory

The final comparison uses one unseen 50 s Lissajous trajectory.

The three evaluated controllers are:

```text
kanayama
plaintext
ckks
```

The client sends 501 measured control requests at:

```text
0.0, 0.1, 0.2, ..., 50.0 s
```

Two additional warm-up requests are executed before the measured run. They are not included in the client-side measured request arrays. The server timing file therefore normally contains 503 entries: 2 warm-ups + 501 measured requests. The result script removes the two server warm-up entries before computing the reported timing values.

For the timing experiment reported in the paper, the Webots client and inference server were executed on the same workstation and communicated through the local loopback interface (`127.0.0.1`). Network latency from a physical LAN/WAN is therefore not part of the reported paper timing.

---

# 3. Important: how Webots chooses the controller

The Webots world is configured with the controller name:

```text
robot_controller
```

Therefore Webots executes exactly this file:

```text
Webots/controllers/robot_controller/robot_controller.py
```

You do not need to edit the `controller` field in the Webots world when switching between data collection and evaluation.

Instead, copy the required repository script over `robot_controller.py`.

## Activate the data collector

Copy:

```text
data_collector.py
```

to:

```text
Webots/controllers/robot_controller/robot_controller.py
```

### Windows

```bat
copy /Y data_collector.py Webots\controllers\robot_controller\robot_controller.py
```

### Linux/macOS

```bash
cp data_collector.py Webots/controllers/robot_controller/robot_controller.py
```

## Activate the evaluation client

Copy:

```text
client.py
```

to:

```text
Webots/controllers/robot_controller/robot_controller.py
```

### Windows

```bat
copy /Y client.py Webots\controllers\robot_controller\robot_controller.py
```

### Linux/macOS

```bash
cp client.py Webots/controllers/robot_controller/robot_controller.py
```

After changing the active controller file, reset or restart the Webots simulation before running it again.

A simple way to verify which controller is active is to look at the Webots console when the simulation starts. The data collector prints messages beginning with `[Collector]`, while the evaluation client prints its connection/evaluation progress.

---

# 4. Full reproduction procedure

## Step 1 - Prepare the repository

Open a terminal in the repository root.

The current directory should contain at least:

```text
data_collector.py
train.py
client.py
server.py
requirements.txt
Webots/
scripts/
```

Install dependencies if you have not already done so:

```bash
pip install -r requirements.txt
```

---

## Step 2 - Activate the Webots data collector

From the repository root, overwrite the active Webots controller with `data_collector.py`.

### Windows

```bat
copy /Y data_collector.py Webots\controllers\robot_controller\robot_controller.py
```

### Linux/macOS

```bash
cp data_collector.py Webots/controllers/robot_controller/robot_controller.py
```

Now open this world in Webots:

```text
Webots/world/world.wbt
```

Reset the simulation before starting the collection.

For data collection, Webots fast mode (`>>`) is strongly recommended. The collector generates 192,680 samples, so real-time simulation would take much longer.

Start the simulation.

You should see progress messages similar to:

```text
[Collector] Starting data collection: 8 trajectories, 40 rollouts each, 192680 expected samples.
[Collector] Trajectory 1/8: lemniscate
...
```

The exact progress formatting may vary slightly, but the controller should continue printing occasional messages so that the collection does not appear frozen.

### Expected output

When collection finishes, this file should exist:

```text
Webots/webots_dataset.npz
```

The expected sample count is:

```text
192680
```

If the sample count is different, first verify that the active collector uses:

```python
N_ROLLOUTS_PER_TRAJECTORY = 40
```

Do not continue to the paper-reproduction training step with a different dataset size unless you intentionally changed the experiment.

---

## Step 3 - Copy the dataset next to `train.py`

`train.py` is intended to be run from the repository root and expects the Webots dataset there by default.

Copy the generated dataset from:

```text
Webots/webots_dataset.npz
```

to:

```text
webots_dataset.npz
```

so the repository root contains:

```text
train.py
webots_dataset.npz
```

### Windows

```bat
copy /Y Webots\webots_dataset.npz webots_dataset.npz
```

### Linux/macOS

```bash
cp Webots/webots_dataset.npz webots_dataset.npz
```

For reproduction of the paper, make sure this Webots dataset exists before running `train.py`. Do not rely on any alternate/synthetic dataset path if you have modified the training script.

---

## Step 4 - Train the neural network

From the repository root, run:

```bash
python train.py
```

The script:

1. loads `webots_dataset.npz`;
2. calculates input and output normalization values;
3. trains the 6-64-2 neural network for 16 epochs;
4. prints training progress;
5. exports the trained weights and normalization values.

### Expected output file

```text
model_export.json
```

After training, the repository root should contain:

```text
train.py
webots_dataset.npz
model_export.json
```

The exact training time depends on the computer. With the paper configuration, the normalized training MSE should be close to the value reported in the paper (`0.004388`), although small numerical differences are possible.

---

## Step 5 - Put the model in both required locations

The same `model_export.json` is used by both the server and the Webots client, but they look for it in different default locations.

### Server copy

Keep the model in the repository root:

```text
server.py
model_export.json
```

### Webots client copy

Also copy the same file to:

```text
Webots/model_export.json
```

### Windows

```bat
copy /Y model_export.json Webots\model_export.json
```

### Linux/macOS

```bash
cp model_export.json Webots/model_export.json
```

After this step there should be two identical copies:

```text
model_export.json
Webots/model_export.json
```

The server uses the model weights for plaintext and CKKS inference. The client uses the normalization values stored in the same file.

---

## Step 6 - Restore the Webots evaluation client

The data collector is no longer needed for the final experiment.

Replace the active Webots controller with `client.py`.

### Windows

```bat
copy /Y client.py Webots\controllers\robot_controller\robot_controller.py
```

### Linux/macOS

```bash
cp client.py Webots/controllers/robot_controller/robot_controller.py
```

Reset or restart Webots after copying the file.

When the evaluation client starts, it automatically creates/draws the Lissajous reference trajectory in the Webots world. You do not need to add the reference trajectory manually to `world.wbt`.

---

## Step 7 - Start the inference server

Open a separate terminal in the repository root and run:

```bash
python server.py
```

Keep this terminal open while running the Webots experiment.

The server defaults to:

```text
mode: auto
bind address: 0.0.0.0
port: 50007
```

In `auto` mode, the server accepts the mode requested by the Webots client, so the same server program can be used for all three runs.

For the same-machine configuration used in the paper, the client connects to:

```text
127.0.0.1:50007
```

If the client reports that it cannot connect, check that:

1. `server.py` is already running;
2. no other process is using port `50007`;
3. the client is using the correct server address;
4. the firewall is not blocking the connection if you run the client and server on different machines.

For CKKS mode, TenSEAL must be installed in both the server Python environment and the Python environment used by Webots.

---

## Step 8 - Select an evaluation mode

The evaluation client supports:

```text
kanayama
plaintext
ckks
```

The default client mode is `kanayama`.

The simplest reproducible method is to set `AMR_MODE` before launching Webots from that same environment, or edit the default `MODE` value in the active Webots controller.

### Windows Command Prompt example

Kanayama:

```bat
set AMR_MODE=kanayama
```

Plaintext NN:

```bat
set AMR_MODE=plaintext
```

CKKS NN:

```bat
set AMR_MODE=ckks
```

### Linux/macOS example

Kanayama:

```bash
export AMR_MODE=kanayama
```

Plaintext NN:

```bash
export AMR_MODE=plaintext
```

CKKS NN:

```bash
export AMR_MODE=ckks
```

If Webots was opened from the desktop rather than from the terminal where the environment variable was set, that variable may not be inherited. In that case, either launch Webots from the configured terminal or change the default mode in:

```text
Webots/controllers/robot_controller/robot_controller.py
```

before the run.

---

## Step 9 - Run the Kanayama experiment

1. Make sure `server.py` is running.
2. Set the client mode to `kanayama`.
3. Reset the Webots simulation.
4. Start the simulation.
5. Allow it to run until the 50 s evaluation finishes.
6. Wait until the client reports that the run data were saved.
7. Allow the server to detect the client disconnection and save its timing file.

Expected files:

Client result:

```text
Webots/run_data_webots_kanayama.npz
```

Server timing:

```text
server_processing_times_kanayama.npz
```

---

## Step 10 - Run the plaintext neural-network experiment

1. Set the client mode to `plaintext`.
2. Reset Webots before the new run.
3. Keep or restart `server.py` in `auto` mode.
4. Start the simulation.
5. Wait for the complete 50 s run and file saving.

Expected files:

```text
Webots/run_data_webots_plaintext.npz
server_processing_times_plaintext.npz
```

---

## Step 11 - Run the CKKS encrypted experiment

1. Set the client mode to `ckks`.
2. Confirm that `Webots/model_export.json` exists.
3. Confirm that `model_export.json` exists next to `server.py`.
4. Confirm that TenSEAL can be imported by both Python environments.
5. Reset Webots.
6. Make sure `server.py` is running.
7. Start the simulation.

At the beginning of the CKKS session, the client creates the CKKS context and sends a public context to the server. The secret key remains on the client side.

The client performs two uncounted warm-up round trips before the measured run begins. After that, the robot executes the 501 measured control requests over the 50 s Lissajous experiment.

Expected files:

```text
Webots/run_data_webots_ckks.npz
server_processing_times_ckks.npz
```

---

## Step 12 - Collect the six result files in the repository root

After all three runs, copy the three Webots result files to the repository root.

### Windows

```bat
copy /Y Webots\run_data_webots_kanayama.npz run_data_webots_kanayama.npz
copy /Y Webots\run_data_webots_plaintext.npz run_data_webots_plaintext.npz
copy /Y Webots\run_data_webots_ckks.npz run_data_webots_ckks.npz
```

### Linux/macOS

```bash
cp Webots/run_data_webots_kanayama.npz run_data_webots_kanayama.npz
cp Webots/run_data_webots_plaintext.npz run_data_webots_plaintext.npz
cp Webots/run_data_webots_ckks.npz run_data_webots_ckks.npz
```

The server timing files should already be in the repository root if `server.py` was started from there.

Before running the result script, verify that these six files exist:

```text
run_data_webots_kanayama.npz
run_data_webots_plaintext.npz
run_data_webots_ckks.npz
server_processing_times_kanayama.npz
server_processing_times_plaintext.npz
server_processing_times_ckks.npz
```

---

## Step 13 - Print the metrics and show the figures

From the repository root, run:

```bash
python scripts/results.py
```

The script:

- prints RMSE, mean position error, and maximum position error for all three controllers;
- prints server processing times;
- prints client-observed round-trip processing times;
- prints the CKKS timing breakdown;
- shows the trajectory comparison;
- shows the tracking-error comparison;
- shows the right- and left-wheel speed comparison.

The script displays the figures only. It does not save PNG, PDF, or EPS files.

Close a displayed Matplotlib window to continue to the next figure if your Matplotlib backend shows the figures sequentially.

---

# 5. Expected paper results

These values can be used as a check that the complete workflow was reproduced correctly.

## Tracking performance

| Controller | RMSE (cm) | Mean error (cm) | Max error (cm) |
|---|---:|---:|---:|
| Kanayama | 0.6940 | 0.5717 | 1.5209 |
| Plaintext NN | 1.1416 | 1.0075 | 2.2684 |
| CKKS NN | 1.3460 | 1.2267 | 2.4917 |

Small numerical differences can occur because of software, hardware, and simulation differences, but the reproduced values should be close if the same dataset, trained model, controller settings, and world are used.

All wheel commands should remain within the configured limit:

```text
+/-10 rad/s
```

## Processing-time results from the paper test machine

| Mode | Server mean (ms) | RTT mean (ms) | RTT min (ms) | RTT max (ms) |
|---|---:|---:|---:|---:|
| Kanayama | 0.08 | 0.41 | 0.08 | 1.11 |
| Plaintext NN | 0.13 | 0.49 | 0.17 | 1.71 |
| CKKS NN | 52.52 | 61.98 | 57.36 | 71.69 |

For CKKS, the mean client-side timing breakdown was approximately:

```text
request preparation (encode/encrypt/serialize): 8.22 ms
server processing:                            52.52 ms
response processing (reconstruct/decrypt):     0.70 ms
remaining loopback/scheduling overhead:         0.54 ms
```

All 501 measured CKKS round trips in the reported experiment were below the 100 ms controller update period.

Timing values are hardware- and operating-system-dependent. They should not be expected to match exactly on another computer. The tracking results are the more useful check for implementation correctness; timing should be interpreted relative to the 100 ms control period.

---

# 6. File flow summary

This is the complete movement of generated files during reproduction.

```text
DATA COLLECTION
---------------
data_collector.py
    -> Webots/controllers/robot_controller/robot_controller.py

Webots runs the collector
    -> Webots/webots_dataset.npz

TRAINING
--------
Webots/webots_dataset.npz
    -> webots_dataset.npz

python train.py
    -> model_export.json

MODEL DEPLOYMENT
----------------
model_export.json
    -> keep next to server.py

model_export.json
    -> Webots/model_export.json

EVALUATION
----------
client.py
    -> Webots/controllers/robot_controller/robot_controller.py

Webots/client runs in kanayama mode
    -> Webots/run_data_webots_kanayama.npz
server.py
    -> server_processing_times_kanayama.npz

Webots/client runs in plaintext mode
    -> Webots/run_data_webots_plaintext.npz
server.py
    -> server_processing_times_plaintext.npz

Webots/client runs in ckks mode
    -> Webots/run_data_webots_ckks.npz
server.py
    -> server_processing_times_ckks.npz

RESULT ANALYSIS
---------------
copy the three Webots run_data files to the repository root

python scripts/results.py
    -> prints metrics
    -> displays figures
```

---

# 7. Environment variables supported by the current scripts

The following environment variables are used by the repository scripts.

| Variable | Used by | Purpose |
|---|---|---|
| `AMR_MODE` | client, server | Client mode (`kanayama`, `plaintext`, `ckks`) or server mode (`auto`, `kanayama`, `plaintext`, `ckks`) |
| `AMR_SERVER` | client | Server IP/hostname; default `127.0.0.1` |
| `AMR_MODEL` | client, server, train | Override the default `model_export.json` path |
| `AMR_SAVE` | client | Override the directory where `run_data_webots_<mode>.npz` is saved |
| `AMR_DATASET` | data collector, train | Override the default `webots_dataset.npz` path |

The current client/server port is fixed in the scripts at:

```text
50007
```

The server bind address is fixed at:

```text
0.0.0.0
```

If you change the port in the source code, change it consistently in both `client.py` and `server.py`.

---

# 8. Troubleshooting

## Webots immediately exits with a Python exception

Read the first Python traceback in the Webots console. Common causes are:

- a required Python package is missing from the Python environment used by Webots;
- the wrong script was copied to `robot_controller.py`;
- the model file is missing during plaintext/CKKS evaluation.

After replacing the controller script, reset or restart Webots.

## The collector seems stuck

The full dataset contains 192,680 samples. Use Webots fast mode for collection. The collector prints occasional progress messages, so a changing rollout/sample count indicates that it is working normally.

## Dataset size is not 192,680

Verify:

```python
N_ROLLOUTS_PER_TRAJECTORY = 40
```

and make sure all eight training trajectories completed without the Webots controller aborting.

## `train.py` cannot find the dataset

Make sure this file exists in the repository root before starting training:

```text
webots_dataset.npz
```

Run `python train.py` from the repository root.

## Server says `model_export.json` is missing

Make sure these files are next to each other:

```text
server.py
model_export.json
```

and start the server from the repository root.

## Webots client says `model_export.json` is missing

Make sure the second model copy exists here:

```text
Webots/model_export.json
```

## Client cannot connect to the server

For the paper setup, use:

```text
server: 127.0.0.1
port:   50007
```

Start `server.py` before running Webots.

## CKKS mode reports that TenSEAL is missing

TenSEAL must be installed for both:

- the Python interpreter running `server.py`;
- the Python interpreter used by the Webots controller.

## Server timing file contains 503 entries instead of 501

This is expected. The CKKS/client startup performs two warm-up requests before the measured 501-request experiment. `scripts/results.py` removes the two server warm-up entries before calculating the paper timing statistics.

## Result script says a file is missing

Before running `scripts/results.py`, confirm that all six required `.npz` files are in the repository root:

```text
run_data_webots_kanayama.npz
run_data_webots_plaintext.npz
run_data_webots_ckks.npz
server_processing_times_kanayama.npz
server_processing_times_plaintext.npz
server_processing_times_ckks.npz
```

## Timing does not match the paper exactly

This is normal. CKKS execution time and process/network scheduling depend on CPU, operating system, background load, Python/TenSEAL versions, and hardware. Compare the timing to the 100 ms control period rather than expecting identical millisecond values on different machines.

---

# 9. Minimal quick-start checklist

For users who already understand the details above, the complete sequence is:

```text
1. pip install -r requirements.txt

2. Copy data_collector.py to:
   Webots/controllers/robot_controller/robot_controller.py

3. Open Webots/world/world.wbt and collect the dataset in fast mode.
   Output: Webots/webots_dataset.npz

4. Copy Webots/webots_dataset.npz to the repository root.

5. Run:
   python train.py
   Output: model_export.json

6. Keep model_export.json next to server.py and also copy it to:
   Webots/model_export.json

7. Copy client.py to:
   Webots/controllers/robot_controller/robot_controller.py

8. Start the server from the repository root:
   python server.py

9. Run Webots three times, resetting between runs:
   kanayama
   plaintext
   ckks

10. Copy the three Webots/run_data_webots_*.npz files to the repository root.

11. Confirm the three server_processing_times_*.npz files are also in the root.

12. Run:
    python scripts/results.py
```

This produces the tracking metrics, timing metrics, and displayed plots used to compare the three controllers in the paper.
