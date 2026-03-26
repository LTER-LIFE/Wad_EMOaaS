# dws_3d_input_output_processing
workflow for processing input and output data for dws 3d model

# dws 3d model git repository
https://github.com/LTER-LIFE/GETM_ERSEM_SETUPS.git

# connect notebook kernel with laplace server
## 1. To start the jupyter application first activate the conda environment with the command
source $HOME/.bashrc.conda2 (or .bashrc.conda3)

## 2. To start JupyterLab type :
jupyter lab --no-browser --port=8888 --ip="0.0.0.0"

## 3. create an SSH tunnel from your local machine
ssh -L8888:localhost:8888 qzhan@laplace.nioz.nl

## 4. Then connect VS Code to this server URL:
http://127.0.0.1:8888/?token=XXX