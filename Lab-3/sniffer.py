import socket
import struct


def ethernet_dissect(ethernet_data):
    dest_mac, src_mac, l2_protocol = struct.unpack('!6s6sH', ethernet_data[:14])
    return {
        "Destination MAC": ":".join(f"{b:02x}" for b in dest_mac).upper(),
        "Source MAC": ":".join(f"{b:02x}" for b in src_mac).upper(),
        "L2_Protocol": l2_protocol,
        "Data": ethernet_data[14:],
    }


def ipv4_dissect(ip_data):
    version_ihl, tos, total_length, identification, flags_offset, ttl, l3_protocol, checksum, src, dest = \
        struct.unpack('!BBHHHBBH4s4s', ip_data[:20])

    version = version_ihl >> 4
    ihl = version_ihl & 0x0F
    header_len = ihl * 4

    return {
        'Version': version,
        'IHL': ihl,
        'Source IP': socket.inet_ntoa(src),
        'Destination IP': socket.inet_ntoa(dest),
        'L3_Protocol': l3_protocol,
        'Data': ip_data[header_len:]
    }


def tcp_dissect(transport_data):
    # TCP header is at least 20 bytes
    if len(transport_data) < 20:
        return None

    src_port, dest_port, sequence, acknowledgement, offset_reserved_flags, window, checksum, urg_ptr = \
        struct.unpack('!HHLLHHHH', transport_data[:20])

    # Data Offset is top 4 bits (header length in 32-bit words)
    tcp_header_length = (offset_reserved_flags >> 12) * 4

    if len(transport_data) < tcp_header_length:
        return None

    # For this lab, focus on the common 4 flags (SYN/ACK/FIN/RST)
    flags = offset_reserved_flags & 0x01FF  # includes NS/CWR/ECE if present; we only display a subset
    flag_status = {
        'SYN': bool(flags & 0x02),
        'ACK': bool(flags & 0x10),
        'FIN': bool(flags & 0x01),
        'RST': bool(flags & 0x04),
    }

    return {
        'Source Port': src_port,
        'Destination Port': dest_port,
        'Sequence Number': sequence,
        'Acknowledgment Number': acknowledgement,
        'Header Length (bytes)': tcp_header_length,
        'Flags': flag_status,
        'Payload': transport_data[tcp_header_length:]
    }


def udp_dissect(data):
    # UDP header is 8 bytes
    if len(data) < 8:
        return None

    src_port, dest_port, length, checksum = struct.unpack('!HHHH', data[:8])
    return {
        'Source Port': src_port,
        'Destination Port': dest_port,
        'Length': length,
        'Checksum': checksum,
        'Payload': data[8:]
    }


def icmp_dissect(icmp_data):
    # ICMP header is at least 4 bytes (Type, Code, Checksum)
    if len(icmp_data) < 4:
        return None

    icmp_type, icmp_code, checksum = struct.unpack('!BBH', icmp_data[:4])
    return {
        'Type': icmp_type,
        'Code': icmp_code,
        'Checksum': checksum,
        'Payload': icmp_data[4:]
    }

def parse_http(data):
    try:
        return {
            'HTTP Data': data.decode('utf-8')
        }
    except UnicodeDecodeError:
        return None

def parse_dns(data):
    # DNS header is 12 bytes
    if len(data) < 12:
        return None

    transaction_id, flags, questions, answer_rrs, authority_rrs, additional_rrs = struct.unpack('!HHHHHH', data[:12])
    return {
        'Transaction ID': transaction_id,
        'Flags': flags,
        'Questions': questions,
        'Answer RRs': answer_rrs,
        'Authority RRs': authority_rrs,
        'Additional RRs': additional_rrs
    }
def main():
    ETH_P_ALL = 0x0003
    packets = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))

    while True:
        raw_data, address = packets.recvfrom(65536)
        # print(raw_data)
        eth_info = ethernet_dissect(raw_data)

        ip_info = ipv4_dissect(eth_info['Data'])

        udp_info = udp_dissect(ip_info['Data'])
        # print(
        #     f"Destination MAC: {eth_info['Destination MAC']}, Source MAC: {eth_info['Source MAC']}, L2_Protocol: {eth_info['L2_Protocol']}")
        if udp_info and (udp_info['Source Port'] == 53 or udp_info['Destination Port'] == 53):
            dns_info = parse_dns(udp_info['Payload'])
            if dns_info:
                print("=== DNS Header ===")
                for key, value in dns_info.items():
                    print(f"{key}: {value}")
        # if eth_info['L2_Protocol'] == 0x0800:  # IPv4 (EtherType)
        #     ip_info = ipv4_dissect(eth_info['Data'])
        #     # print(
        #     #     f"Source IP: {ip_info['Source IP']}, "
        #     #     f"Destination IP: {ip_info['Destination IP']}, "
        #     #     f"L3 Protocol: {ip_info['L3_Protocol']}"
        #     # )
        #
        #     if ip_info['L3_Protocol'] == 6:  # TCP
        #         tcp_info = tcp_dissect(ip_info['Data'])
        #         udp_info = udp_dissect(ip_info['Data'])


                # if tcp_info:
                #     print(f"TCP {tcp_info['Source Port']} -> {tcp_info['Destination Port']}")
                #     print(f"TCP Header Length: {tcp_info['Header Length (bytes)']} bytes")
                #     print("TCP Flags:")
                #     for flag, status in tcp_info['Flags'].items():
                #         print(f"  {flag}: {'Set' if status else 'Not Set'}")
                # if tcp_info['Source Port'] == 80 or tcp_info['Destination Port'] == 80:
                #     http_info = parse_http(tcp_info['Payload'])
                #     if http_info:
                #         print(http_info['HTTP Data'][:100])
            # if ip_info['L3_Protocol'] == 17:  # UDP
            #     udp_info = udp_dissect(ip_info['Data'])
            #     if udp_info:
            #         print(f"Source Port: {udp_info['Source Port']}, Destination Port: {udp_info['Destination Port']}")
            #
            # if ip_info['L3_Protocol'] == 1:  # ICMP
            #     icmp_info = icmp_dissect(ip_info['Data'])
            #     if icmp_info:
            #         print(
            #             f"ICMP Type: {icmp_info['Type']}, Code: {icmp_info['Code']}, Checksum: {icmp_info['Checksum']}")



if __name__ == "__main__":
    main()