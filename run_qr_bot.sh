#!/bin/bash

# Navigate to home directory
cd /home/ubuntu

# Log file
LOG_FILE="/home/ubuntu/qr_bot.log"

# Function to start the bot
start_bot() {
    echo "$(date): Starting QR Bot..." >> $LOG_FILE
    python3 /home/ubuntu/qr_bot.py >> $LOG_FILE 2>&1
}

# Infinite loop to keep the bot running
while true; do
    start_bot
    echo "$(date): Bot crashed or stopped. Restarting in 5 seconds..." >> $LOG_FILE
    sleep 5
done
