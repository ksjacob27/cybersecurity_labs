#!/bin/bash

logfile="/home/kevin/Documents/Lab-11/report.log"

pingtest() {
    target_ip=$1
    ping_output=$(ping -c3 $target_ip | tail -2)
    ping_summary=$(echo "$ping_output" | head -n1)
    ping_rtt=$(echo "$ping_output" | tail -n1)

    has_errors=$(echo "$ping_summary" | grep -o errors)

    if [ "$has_errors" != "" ]; then
        loss=$(echo "$ping_summary" | cut -d"," -f4 | cut -d" " -f2)
    else
        loss=$(echo "$ping_summary" | cut -d"," -f3 | cut -d" " -f2)
    fi

    delay=$(echo "$ping_rtt" | cut -d"=" -f2 | cut -d"/" -f1)

    timestamp=$(date)

    if [ "$loss" = "100%" ]; then
        echo "$timestamp - Server $target_ip is not responding at all."
        echo "$timestamp - Server $target_ip is not responding at all." >> $logfile
    elif [ "$loss" != "0%" ]; then
        echo "$timestamp - Server $target_ip is responding with packet loss."
        echo "$timestamp - Server $target_ip is responding with packet loss." >> $logfile
    else
        delay_sec_part=$(echo "$delay" | cut -d"." -f1)
        if [ "$delay_sec_part" -lt 1 ]; then
            echo "$timestamp - Server $target_ip is responding normally."
            echo "$timestamp - Server $target_ip is responding normally." >> $logfile
        else
            echo "$timestamp - Server $target_ip is responding slowly."
            echo "$timestamp - Server $target_ip is responding slowly." >> $logfile
        fi
    fi
}

arpcheck() {
    target_ip=$1
    expected_mac=$2

    ping -c1 $target_ip > /dev/null 2>&1

    actual_mac=$(arp $target_ip | tail -1 | cut -c34-50)

    timestamp=$(date)

    if [ "$actual_mac" != "$expected_mac" ]; then
        echo "$timestamp - WARNING: Server with IP $target_ip is responding with wrong MAC $actual_mac"
        echo "$timestamp - WARNING: Server with IP $target_ip is responding with wrong MAC $actual_mac" >> $logfile
    else
        echo "$timestamp - Server $target_ip has valid MAC address $actual_mac"
        echo "$timestamp - Server $target_ip has valid MAC address $actual_mac" >> $logfile
    fi
}

portcheckSimple() {
    nmaplog=$(nmap $1 | grep $2)
    if [ "$nmaplog" != "" ]; then
        echo "$(date) WARNING: Port $2 is open on $1"
        echo "$(date) WARNING: Port $2 is open on $1" >> $logfile
    fi
}

portcheck() {
    target_ip=$1
    expected_ports=$2
    IFS=';' read -r -a arrayports <<< "$expected_ports"

    nmaplog=$(nmap $target_ip)

    for port in "${arrayports[@]}"
    do
        match=$(echo "$nmaplog" | grep "$port/tcp" | grep open)
        if [ -z "$match" ]; then
            echo "$(date) - Port $port on server $target_ip is EXPECTED to be open, but it is CLOSED or FILTERED." >> "$logfile"
            echo "$(date) - Port $port on server $target_ip is EXPECTED to be open, but it is CLOSED or FILTERED."
        fi
    done

    allOpenPorts=$(echo "$nmaplog" | grep open | grep tcp | cut -d'/' -f1)

    for port in $allOpenPorts; do
        if [[ ! " ${arrayports[@]} " =~ " ${port} " ]]; then
            echo "$(date) - UNEXPECTED open port $port found on server $target_ip" >> "$logfile"
            echo "$(date) - UNEXPECTED open port $port found on server $target_ip"
        fi
    done

    IFS=$' \t\n'
}

comprehensivecheck() {
    input_file=$1

    while IFS= read -r line; do
        ip=$(echo "$line" | cut -d' ' -f1)
        mac=$(echo "$line" | cut -d' ' -f2)
        ports=$(echo "$line" | cut -d' ' -f3)

        echo "$(date) - Starting compliance check for $ip" | tee -a $logfile
        pingtest "$ip"
        arpcheck "$ip" "$mac"
        portcheck "$ip" "$ports"
        echo "$(date) - Compliance check complete for $ip" | tee -a $logfile
        echo "---"
    done < "$input_file"
}

comprehensivecheck /home/kevin/Documents/Lab-11/input.txt
