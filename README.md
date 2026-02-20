# Quantum Phase Estimation Simulator

## Installation & Setup
### 1. Windows (Clickable)
* **Important:** Extract the files from the `.zip` folder first.
1. In the main folder, double-click **`launch.bat`**. It will handle setup on initial run, and can be used to run the simulator.

### 2. macOS (Clickable)
1. Open Terminal and `cd` to the downloaded folder.
2. Run this line to fix permissions:
   ```bash
   xattr -c *.command && chmod +x *.command
   ```
3. In the main folder, double-click **`launch.command`**. It will handle setup on initial run, and can be used to run the simulator.

### 3. Windows (Command Prompt)
1. Clone the repo and navigate to directory
2. To run the script, use `launch.bat`. It will handle setup on initial run, and can be used to run the simulator.

### 4. macOS (Terminal)
1. Clone the repo and navigate to directory
3. To run the script, use `./launch.command`. It will handle setup on initial run, and can be used to run the simulator.

## Main files
* `interface.py` provides a graphical window for controlling the laser and time-tagger,
while also plotting the single photon counts and optical power
* `experiment.py` defines a single high-level class for controlling the laser, time-tagger, 
and optical power meter
* `example.ipynb` provides an example of how to script measurements