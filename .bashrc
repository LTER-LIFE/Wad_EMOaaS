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

# kill by name:
# lsof -i :8889
# kill -9 <PID>
