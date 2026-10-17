# General Propeller Analysis using OpenFOAM

This repository contains files and scripts for a CFD simulation of a general propeller using OpenFOAM. 
The simulation was modified to allow the use of any propeller geometry by changing the propellerTip.obj file in ./constant/triSurface
Note: The propeller diameter is resctricted to 0.2 m so as to reduce the domanin size and decrease the simulation time and disk space requirement.


## Simulation Setup

1. **Geometry**: The propellerTip.obj propeller geometry is used. This file can be produce by any CAD file.

2. **Boundary Conditions**: Defined in the ./0 folder.

3. **Solver**: The `pimpleFoam` solver is used.


## Running the Simulation

1. **Prepare the case**:

  Run Allrun.pre

2. **Run the Simulation**:

  Run Allrun

3. **Post-Processing**: Use the forces function in the `controlDict` to calculate thrust and torque on the propeller. The results are stored in the `postProcessing/forces` directory. The same applies to the moments.




