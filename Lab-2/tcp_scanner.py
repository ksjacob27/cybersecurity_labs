import socket
import sys

def tcp_scanner(target, port):
   """
   # Add your comment here (e.g., Why do we use `socket.AF_INET` and `socket.SOCK_STREAM`?)
   socket.AF_INET is to specify IPv4 addressing
   SOCK_STREAM is to specify a TCP connection
   """
   try:
         tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         tcp_sock.settimeout(1)  # sets a 1 second time limit for a response 
         tcp_sock.connect((target, port))
         tcp_sock.close()
         return True
   except:
         """
         # Add your comment here (e.g., What types of exceptions might occur?)
         Exceptions may occur if the connection fails because the port is either closed or filtered 
         """
         return False

def main():
   """
   # Add your comment here (e.g., Why check for command-line arguments with `len(sys.argv)`?)
   We use this to ensure that the user has provided the correct number of arguments 
   """
   if len(sys.argv) != 2:
         print("Usage: python tcp_scanner.py <Metasploitable-2_IP>")
         sys.exit(1)

   target = sys.argv[1]
   print(f"Scanning TCP ports on {target}...")
   """
   # Add your comment here (e.g., Why loop through the port range 1-1024?)
   We loop through these ports because ports that fall within this range are standard ports used in common practice where most critical services operate. 
   """
   for port in range(1, 1024):
         if tcp_scanner(target, port):
            print(f"[*] Port {port}/tcp is open")

if __name__ == "__main__":
   main()