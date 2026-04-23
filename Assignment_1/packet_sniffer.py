import socket
import struct
import argparse
import csv
import threading
import time
from collections import deque
from datetime import datetime, timedelta

packetMemory = deque()
csvBuffer = []
bufferLock = threading.Lock()


def ethernetDissect(ethernetData):
    destMac, srcMac, l2Protocol = struct.unpack('!6s6sH', ethernetData[:14])
    return {
        "Destination MAC": ":".join(f"{b:02x}" for b in destMac).upper(),
        "Source MAC": ":".join(f"{b:02x}" for b in srcMac).upper(),
        "L2_Protocol": l2Protocol,
        "Data": ethernetData[14:],
    }


def ipv4Dissect(ipData):
    versionIhl, tos, totalLength, identification, flagsOffset, ttl, l3Protocol, checksum, src, dest = struct.unpack(
        '!BBHHHBBH4s4s', ipData[:20])
    version = versionIhl >> 4
    ihl = versionIhl & 0x0F
    headerLen = ihl * 4
    return {
        'Version': version,
        'IHL': ihl,
        'Source IP': socket.inet_ntoa(src),
        'Destination IP': socket.inet_ntoa(dest),
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
        'Source Port': srcPort,
        'Destination Port': destPort,
        'Flags': flagStatus,
        'Payload': transportData[tcpHeaderLength:]
    }


def udpDissect(data):
    if len(data) < 8:
        return None
    srcPort, destPort, length, checksum = struct.unpack('!HHHH', data[:8])
    return {
        'Source Port': srcPort,
        'Destination Port': destPort,
    }


def icmpDissect(icmpData):
    if len(icmpData) < 4:
        return None
    icmpType, icmpCode, checksum = struct.unpack('!BBH', icmpData[:4])
    return {'Type': icmpType, 'Code': icmpCode}


def memoryAndCsvManager(outputFile):
    while True:
        time.sleep(10)

        bufferLock.acquire()

        if outputFile != None:
            if len(csvBuffer) > 0:
                try:
                    file = open(outputFile, mode='a', newline='')
                    writer = csv.DictWriter(file, fieldnames=['timestamp', 'src_ip', 'dst_ip', 'dst_port', 'protocol',
                                                              'tcp_flags'])
                    if file.tell() == 0:
                        writer.writeheader()
                    for row in csvBuffer:
                        writer.writerow(row)
                    file.close()
                    csvBuffer.clear()
                except:
                    pass

        tenMinsAgo = datetime.now() - timedelta(minutes=10)
        itemsToRemove = []

        for packet in packetMemory:
            packetTime = datetime.strptime(packet['timestamp'], '%Y-%m-%d %H:%M:%S')
            if packetTime < tenMinsAgo:
                itemsToRemove.append(packet)

        for item in itemsToRemove:
            packetMemory.remove(item)

        bufferLock.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interface", required=True)
    parser.add_argument("-o", "--output", default=None)
    args = parser.parse_args()

    managerThread = threading.Thread(target=memoryAndCsvManager, args=(args.output,), daemon=True)
    managerThread.start()

    print("Starting raw socket packet sniffing on " + args.interface + "...")
    if args.output != None:
        print("Logging to " + args.output + " in batches every 10 seconds.")

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
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                srcIp = ipInfo['Source IP']
                dstIp = ipInfo['Destination IP']

                protocol = "UNKNOWN"
                dstPort = "-"
                tcpFlags = "-"

                if ipInfo['L3_Protocol'] == 6:
                    protocol = "TCP"
                    tcpInfo = tcpDissect(ipInfo['Data'])
                    if tcpInfo != None:
                        dstPort = tcpInfo['Destination Port']

                        flagsList = []
                        if tcpInfo['Flags']['SYN'] == True:
                            flagsList.append("SYN")
                        if tcpInfo['Flags']['ACK'] == True:
                            flagsList.append("ACK")
                        if tcpInfo['Flags']['FIN'] == True:
                            flagsList.append("FIN")
                        if tcpInfo['Flags']['RST'] == True:
                            flagsList.append("RST")

                        if len(flagsList) > 0:
                            tcpFlags = ""
                            for f in flagsList:
                                tcpFlags += f + "|"
                            tcpFlags = tcpFlags[:-1]
                        else:
                            tcpFlags = "-"

                elif ipInfo['L3_Protocol'] == 17:
                    protocol = "UDP"
                    udpInfo = udpDissect(ipInfo['Data'])
                    if udpInfo != None:
                        dstPort = udpInfo['Destination Port']

                elif ipInfo['L3_Protocol'] == 1:
                    protocol = "ICMP"
                    icmpInfo = icmpDissect(ipInfo['Data'])
                    if icmpInfo != None:
                        if icmpInfo['Type'] == 8:
                            tcpFlags = "ECHO_REQUEST"
                        elif icmpInfo['Type'] == 0:
                            tcpFlags = "ECHO_REPLY"

                logEntry = {
                    'timestamp': timestamp,
                    'src_ip': srcIp,
                    'dst_ip': dstIp,
                    'dst_port': dstPort,
                    'protocol': protocol,
                    'tcp_flags': tcpFlags
                }

                print("[" + timestamp + "] " + str(srcIp) + " -> " + str(dstIp) + " | Proto: " + str(
                    protocol) + " | Port: " + str(dstPort) + " | Flags: " + str(tcpFlags))

                bufferLock.acquire()
                packetMemory.append(logEntry)
                csvBuffer.append(logEntry)
                bufferLock.release()

    except KeyboardInterrupt:
        print("\nStopping sniffer.")


if __name__ == "__main__":
    main()