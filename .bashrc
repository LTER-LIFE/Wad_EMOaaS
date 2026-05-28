juplab() {
  # Clean up local port and remote jupyter on exit
  cleanup() {
    echo ""
    echo "Shutting down JupyterLab and closing tunnel..."
    # Kill remote jupyter on port 8889
    ssh qzhan@laplace.nioz.nl \
      "pkill -u qzhan -f 'jupyter-lab.*8889'" 2>/dev/null
    # Kill any local process still holding port 8889
    fuser -k 8889/tcp 2>/dev/null
    echo "Done."
  }

  trap cleanup EXIT

  ssh -L 8889:localhost:8889 qzhan@laplace.nioz.nl \
    "source ~/.bashrc.conda3 && \
     conda activate 3Dmodel_input_output_process && \ 
     jupyter lab --no-browser --ip=0.0.0.0 --port=8889 --port-retries=0"
}

juplab_slurm() {

  USER="qzhan"
  HOST="laplace.nioz.nl"
  PORT=8889

  echo "Submitting SLURM job..."

  JOBID=$(ssh ${USER}@${HOST} \
    "sbatch --parsable << 'EOF'
#!/bin/bash
#SBATCH --job-name=jupyter
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=80G

source ~/.bashrc.conda3
conda activate 3Dmodel_input_output_process

PORT=${PORT}
echo \"Running on host: \$(hostname)\"
echo \"PORT=\${PORT}\"

jupyter lab --no-browser --ip=0.0.0.0 --port=\${PORT} --port-retries=0
EOF
")

  echo "Job submitted: $JOBID"
  echo "Waiting for job to start..."

  # Wait for job to start and get node
  while true; do
    NODE=$(ssh ${USER}@${HOST} "squeue -j $JOBID -h -o %N")
    if [[ -n "$NODE" && "$NODE" != "(null)" ]]; then
      break
    fi
    sleep 2
  done

  echo "Job is running on node: $NODE"

  # Get full node hostname if needed
  NODE_FULL="$NODE"

  echo "Setting up SSH tunnel..."

  # Cleanup function
  cleanup() {
    echo ""
    echo "Cleaning up..."
    ssh ${USER}@${HOST} "scancel $JOBID" 2>/dev/null
    fuser -k ${PORT}/tcp 2>/dev/null
    echo "Done."
  }

  trap cleanup EXIT

  # Open tunnel (login node ? compute node)
  ssh -L ${PORT}:${NODE_FULL}:${PORT} ${USER}@${HOST}

}

# conda envs:
# input_data_prep
# 3Dmodel_input_output_process

# kill by name:
# lsof -i :8889
# kill -9 <PID>
