#!/bin/bash

subnet="192.168.10.0/24"
output_dir="/home/kevin/Documents/assignment3/scans"
log_file="/home/kevin/Documents/assignment3/log.txt"
timestamp=$(/bin/date +"%Y-%m-%d_%H-%M")
scan_file="$output_dir/scan_$timestamp.txt"
current_state="$output_dir/current_state.txt"
previous_state="$output_dir/previous_state.txt"

first_run=false
changes_output=""

scan_network() {
    /bin/mkdir -p "$output_dir"
    /usr/bin/nmap -sS -p- "$subnet" --open -oG "$scan_file"
}

parse_scan_results() {
    /usr/bin/grep "Ports:" "$scan_file" | /usr/bin/awk '{
        ip = $2
        split($0, a, "Ports: ")
        ports_raw = a[2]
        gsub(/\/[^,]*/, "", ports_raw)
        gsub(/\t.*/, "", ports_raw)
        print ip " \342\206\222 " ports_raw
    }' > "$current_state"
}

detect_changes() {
    if [ ! -f "$previous_state" ]; then
        first_run=true
        /bin/cp "$current_state" "$previous_state"
        return
    fi

    local output=""

    # New hosts (in current but not in previous)
    while IFS= read -r line; do
        ip=$(echo "$line" | /usr/bin/awk '{print $1}')
        if ! /usr/bin/grep -q "^$ip " "$previous_state"; then
            ports=$(echo "$line" | /usr/bin/sed 's/^[^ ]* → //')
            output="$output\n+ New host: $ip\n    Open ports: $ports"
        fi
    done < "$current_state"

    # Missing hosts (in previous but not in current)
    while IFS= read -r line; do
        ip=$(echo "$line" | /usr/bin/awk '{print $1}')
        if ! /usr/bin/grep -q "^$ip " "$current_state"; then
            output="$output\n- Host offline: $ip"
        fi
    done < "$previous_state"

    # Port changes for hosts that exist in both scans
    while IFS= read -r curr_line; do
        ip=$(echo "$curr_line" | /usr/bin/awk '{print $1}')
        if /usr/bin/grep -q "^$ip " "$previous_state"; then
            curr_ports=$(echo "$curr_line" | /usr/bin/sed 's/^[^ ]* → //')
            prev_ports=$(/usr/bin/grep "^$ip " "$previous_state" | /usr/bin/sed 's/^[^ ]* → //')

            # Newly opened ports
            for port in $(echo "$curr_ports" | /usr/bin/tr ',' ' '); do
                port=$(echo "$port" | /usr/bin/tr -d ' ')
                if ! echo "$prev_ports" | /usr/bin/grep -qw "$port"; then
                    output="$output\n+ $ip: Port $port opened"
                fi
            done

            # Closed ports
            for port in $(echo "$prev_ports" | /usr/bin/tr ',' ' '); do
                port=$(echo "$port" | /usr/bin/tr -d ' ')
                if ! echo "$curr_ports" | /usr/bin/grep -qw "$port"; then
                    output="$output\n- $ip: Port $port closed"
                fi
            done
        fi
    done < "$current_state"

    changes_output="$output"
    /bin/cp "$current_state" "$previous_state"
}

log_changes() {
    if [ "$first_run" = true ]; then
        echo "[$(date '+%Y-%m-%d %H:%M')] Initial scan:" >> "$log_file"
        /bin/cat "$current_state" >> "$log_file"
    elif [ -n "$changes_output" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M')] Change detected:" >> "$log_file"
        echo -e "$changes_output" >> "$log_file"
    else
        echo "[$(date '+%Y-%m-%d %H:%M')] No changes detected." >> "$log_file"
    fi
}

main() {
    scan_network
    parse_scan_results
    detect_changes
    log_changes
}

main