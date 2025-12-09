#!/bin/bash

# Dòng này để báo lỗi ngay nếu có lệnh nào bị fail (giúp debug dễ hơn)
set -e

echo "--- Starting Submission Pipeline ---"



echo "Running prediction..."
python3 predict.py

echo "--- Pipeline Finished Successfully ---"