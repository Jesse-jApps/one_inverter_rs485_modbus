#!/bin/bash

function start_app() {

    # tested with this , uncomment your command
    streamlit run app.py > app.log  2>&1 & 
    # write the pid to text to file to use it later
    app_pid=$!
    echo "Process started having PID $app_pid"
    # wait for process to check proper state, you can change this time accordingly 
    sleep 3
    if ps -p $app_pid > /dev/null
    then
        echo "Process successfully running having PID $app_pid"
        # write if success
        echo $app_pid > process_id.txt
    else
        echo "Process stopped before reached to steady state"
    fi
}

function stop_app() {
    # Get the PID from text file
    application_pid=$(cat process_id.txt)
    echo "stopping process, Details:"
    # print details
    ps -p $application_pid
    # check if running
    if ps -p $application_pid > /dev/null
    then
        # if running then kill else print message
        echo "Going to stop process having PId $application_pid"
        kill -9 $application_pid
        if [ $? -eq 0 ]; then
        echo "Process stopped successfully"
        else
        echo "Failed to stop process having PID $application_pid"
        fi
    else
        echo "Failed to stop process, Process is not running"
    fi
}


case "$1" in 
    start_app)   start_app ;;
    stop_app)    stop_app ;;
    restart_app) stop_app; start_app ;;
    *) echo "usage: $0 start_app|stop_app|restart_app" >&2
       exit 1
       ;;
esac