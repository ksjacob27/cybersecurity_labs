import socket
import struct
import argparse
import time
import csv
import os
from datetime import datetime, timedelta

ipConnections = {}


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
        'Destination Port': destPort,
        'Flags': flagStatus
    }


def checkCsvHistory(targetIp):
    if os.path.exists("traffic_log.csv") == False:
        return False

    file = open("traffic_log.csv", "r")
    reader = csv.DictReader(file)
    thirtyMinsAgo = datetime.now() - timedelta(minutes=30)

    uniquePorts = []

    for row in reader:
        if row['src_ip'] == targetIp and row['protocol'] == "TCP" and "SYN" in row['tcp_flags'] and "ACK" not in row[
            'tcp_flags']:
            rowTime = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            if rowTime >= thirtyMinsAgo:
                p = row['dst_port']
                if p not in uniquePorts:
                    uniquePorts.append(p)

    file.close()

    if len(uniquePorts) > 50:
        return True

    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interface", required=True)
    args = parser.parse_args()

    print("Starting Port Scanner Detector on " + args.interface + "...")

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

                            dstPort = tcpInfo['Destination Port']
                            currentTime = int(time.time())

                            if srcIp not in ipConnections:
                                ipConnections[srcIp] = []

                            ipConnections[srcIp].append({"time": currentTime, "port": dstPort})

                            tempList = []
                            for connItem in ipConnections[srcIp]:
                                if currentTime - connItem["time"] <= 300:
                                    tempList.append(connItem)
                            ipConnections[srcIp] = tempList

                            ports1s = []
                            ports60s = []
                            ports300s = []

                            for connItem in ipConnections[srcIp]:
                                if currentTime - connItem["time"] <= 1:
                                    if connItem["port"] not in ports1s:
                                        ports1s.append(connItem["port"])
                                if currentTime - connItem["time"] <= 60:
                                    if connItem["port"] not in ports60s:
                                        ports60s.append(connItem["port"])
                                if currentTime - connItem["time"] <= 300:
                                    if connItem["port"] not in ports300s:
                                        ports300s.append(connItem["port"])

                            count1s = len(ports1s)
                            count60s = len(ports60s)
                            count300s = len(ports300s)

                            isScanner = False
                            reason = ""
                            fanOut = 0

                            if count1s > 5:
                                isScanner = True
                                reason = "Exceeded 5 ports/sec threshold"
                                fanOut = count1s
                            elif count60s > 100:
                                isScanner = True
                                reason = "Exceeded 100 ports/min threshold"
                                fanOut = count60s
                            elif count300s > 300:
                                isScanner = True
                                reason = "Exceeded 300 ports/5 mins threshold"
                                fanOut = count300s

                            if isScanner == True:
                                hasHistory = checkCsvHistory(srcIp)
                                if hasHistory == True:
                                    historyStr = "YES"
                                else:
                                    historyStr = "NO"

                                print("\nALERT: Port Scanner Detected! ")
                                print("Source: " + str(srcIp) + " | Fan-Out Rate: " + str(
                                    fanOut) + " | Reason: " + reason)
                                print("Previous port scan detected in last 30 minutes: " + historyStr + "\n")

                                ipConnections[srcIp] = []

    except KeyboardInterrupt:
        print("\nStopping detector.")


if __name__ == "__main__":
    main()