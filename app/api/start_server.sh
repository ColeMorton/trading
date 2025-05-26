#!/bin/bash
# Start the API server from the correct directory

cd /Users/colemorton/Projects/trading
python -m app.api.run "$@"