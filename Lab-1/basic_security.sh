#!/bin/bash
 # Variables
 SUBNET="192.168.10.0/24"    # Replace 'x' with the local subnet network address for your environment
 TARGET="192.168.10.13"       # Replace with the target IP or host IP (MS-2 Target VM)

 echo "Enhanced Security Script"
 echo "========================="

 # Part 1: Collect Information About the Local Machine
 echo "Part 1: Information About My Own Machine"
 echo "========================================="
 echo "[*] System Information:"
 uname -a   # Add comment: Explain what this command does
 echo

 echo "[*] Network Interfaces and IP Addresses:"
 ip addr show   # Add comment: Explain what this command does
 echo

 echo "[*] ARP Table:"
 arp -a   # Add comment: Explain what this command does
 echo

 echo "[*] Open Ports on Local Machine:"
 sudo netstat -tuln   # Add comment: Explain what this command does
 echo

 # Part 2: Collect Information About a Target
 echo "Part 2: Information About a Target"
 echo "=================================="
 echo "[*] Active Hosts in Subnet ($SUBNET):"
 sudo nmap -sP $SUBNET   # Add comment: Explain what this command does, including the purpose of the -sP option
 echo

 echo "[*] Service Scan on Target ($TARGET):"
 sudo nmap -sV $TARGET   # Add comment: Explain what this command does, including the purpose of the -sV option 
 echo

 echo "[*] Vulnerability Scan on Target ($TARGET):"
 sudo nmap --script vuln $TARGET   # Add comment: Explain what this command does, including the purpose of the '--script vuln' option
 echo
