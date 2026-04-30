# dws_3d_input_output_processing
workflow for processing input and output data for dws 3d model

# dws 3d model git repository
https://github.com/LTER-LIFE/GETM_ERSEM_SETUPS.git

# connect notebook kernel with laplace server

- set environmental variable DISPLAY 
$env:DISPLAY = "127.0.0.1:0.0"

- 1. create an SSH tunnel from your local machine
ssh -Y -L8889:localhost:8889 qzhan@laplace.nioz.nl

- 2. activate conda on Laplace Cluster
source $HOME/.bashrc.conda3 (or .bashrc.conda3)
conda env create -f 3Dmodel_input_output_env.yml 
conda env update -f 3Dmodel_input_output_env.yml 
conda activate my_env_name

- 3. check kernel
jupyter kernelspec list
python -m ipykernel install --user --name my_env_name --display-name "Python (my_env_name)"

- 4. To start JupyterLab type :
jupyter lab --no-browser --port=8889 --ip="0.0.0.0"

- 5. Then connect VS Code to the given server URL:
http://127.0.0.1:8889/?token=XXX

