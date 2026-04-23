import socket
import struct
import argparse
import time
import csv
import os
from datetime import datetime, timedelta

ipStats = {}


def ethernetDissect(ethernetData):
    destMac, srcMac, l2Protocol = struct.unpack('!6s6sH', ethernetData[:14])
    return {
        "L2_Protocol": l2Protocol,
        "Data": ethernetData[14:],
    }


def ipv4Dissect(ipData):
    versionIhl, tos, totalLength, identification, flagsOffset, ttl, l3Protocol, checksum, src, dest = struct.unpack(
        '!BBHHHBBH4s4s', ipData[:20])
    ihl = versionIhl & 0x0F
    headerLen = ihl * 4
    return {
        'Source IP': socket.inet_ntoa(src),
        'L3_Protocol': l3Protocol,
        'Data': ipData[headerLen:]
    }


def tcpDissect(transportData):
    if len(transportData) < 20:
        return None
    srcPort, destPort, sequence, acknowledgement, offsetReservedFlags, window, checksum, urgPtr = struct.unpack(
        '!HHLLHHHH', transportData[:20])
    tcpHeaderLength = (offsetReservedFlags >> 12) * 4
    if len(transportData) < tcpHeaderLength:
        return None

    flags = offsetReservedFlags & 0x01FF
    flagStatus = {
        'SYN': bool(flags & 0x02),
        'ACK': bool(flags & 0x10),
        'FIN': bool(flags & 0x01),
        'RST': bool(flags & 0x04),
    }
    return {
        'Flags': flagStatus
    }


def checkCsvHistory(targetIp):
    if os.path.exists("traffic_log.csv") == False:
        return False

    file = open("traffic_log.csv", "r")
    reader = csv.DictReader(file)
    thirtyMinsAgo = datetime.now() - timedelta(minutes=30)

    historyStats = {}

    for row in reader:
        if row['src_ip'] == targetIp and row['protocol'] == "TCP" and "SYN" in row['tcp_flags'] and "ACK" not in row[
            'tcp_flags']:
            rowTime = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            if rowTime >= thirtyMinsAgo:
                timeStr = row['timestamp']
                if timeStr in historyStats:
                    historyStats[timeStr] += 1
                else:
                    historyStats[timeStr] = 1

    file.close()

    for t in historyStats:
        if historyStats[t] > 100:
            return True

    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interface", required=True)
    args = parser.parse_args()

    print("Starting SYN Flood Detector on " + args.interface + "...")

    try:
        conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
        conn.bind((args.interface, 0))
    except:
        print("Error: run with sudo")
        return

    try:
        while True:
            rawData, addr = conn.recvfrom(65536)
            ethInfo = ethernetDissect(rawData)

            if ethInfo['L2_Protocol'] == 0x0800:
                ipInfo = ipv4Dissect(ethInfo['Data'])
                srcIp = ipInfo['Source IP']

                if ipInfo['L3_Protocol'] == 6:
                    tcpInfo = tcpDissect(ipInfo['Data'])
                    if tcpInfo != None:
                        if tcpInfo['Flags']['SYN'] == True and tcpInfo['Flags']['ACK'] == False:

                            currentSec = int(time.time())

                            if srcIp not in ipStats:
                                ipStats[srcIp] = {"lastSec": currentSec, "count": 1, "consecSecs": 0}
                            else:
                                if ipStats[srcIp]["lastSec"] == currentSec:
                                    ipStats[srcIp]["count"] += 1
                                else:
                                    if ipStats[srcIp]["count"] > 100:
                                        ipStats[srcIp]["consecSecs"] += 1
                                    else:
                                        ipStats[srcIp]["consecSecs"] = 0

                                    ipStats[srcIp]["count"] = 1
                                    ipStats[srcIp]["lastSec"] = currentSec

                                if ipStats[srcIp]["consecSecs"] >= 3:
                                    hasHistory = checkCsvHistory(srcIp)
                                    if hasHistory == True:
                                        historyStr = "YES"
                                    else:
                                        historyStr = "NO"

                                    print("\nALERT: SYN Flood Detected! ")
                                    print("Source: " + str(srcIp) + " | Rate: >100 SYN packets/sec | Duration: 3 sec")
                                    print("Previous SYN flood detected in last 30 minutes: " + historyStr + "\n")

                                    ipStats[srcIp]["consecSecs"] = 0

    except KeyboardInterrupt:
        print("\nStopping detector.")


if __name__ == "__main__":
    main()