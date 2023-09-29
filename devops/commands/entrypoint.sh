#!/bin/bash

check_vars () {
    var_names=("$@")
    for var_name in "${var_names[@]}"; do
        if [[ -z "${!var_name}" ]];
        then
            echo "Warning: ${var_name} is unset."
            var_unset=true
        fi
    done
    if [[ -n "$var_unset" ]];
    then
        return 1
    else
        return 0
    fi
}

wait_for () {
    for trial in `seq 1 100`; do
        echo "Trying to connect to $1:$2 ($trial)"
        (echo > /dev/tcp/$1/$2) >/dev/null 2>&1
        if [[ $? -eq 0 ]]; then
            echo "$1:$2 accepts connections!^_^"
            break
        fi
        sleep 1
    done
}

exec "$@"
