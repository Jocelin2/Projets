#! /usr/bin/python3.12

### IMPORTS ###

from struct import *
from socket import *
from time import *
from random import *


### FUNCTIONS ###

def init_checksum(packet, protocol):                                                # Function that sets the checksum value to 0
    
    """
    This function sets the checksum value to 0, with two parameters:
    packet (the packet) and protocol (the protocol).
    
    params:
    packet (bytes): the packet
    protocol (str): the protocol
    
    return:
    bytes: the packet with the checksum value set to 0
    """

    index =  {
        "IP" : 10,                                                                  # Dictionary that maps the protocol to the index of the checksum value in the packet
        "ICMP" : 2,
    }                       
    return packet[:index[protocol]] + b"\x00\x00" + packet[index[protocol]+2:]      # return the packet with the checksum value set to 0

def checksum(packet):                                                               # Function that calculates the checksum value                                       
    
    """
    This function calculates the checksum value of a packet, with a parameter of type bytes.
    
    params:
    packet (bytes): the packet
    
    return:
    bytes: the checksum value in network byte order
    """

    sum = 0x0000                                                                    #Set the value of the checksum to 0
    for i in range(0, len(packet), 2):                                              #For each byte in the packet
        sum += (packet[i] << 8) + packet[i+1]                                       # Add the two bytes at index i and i+1 to the sum
    sum = ~((sum & 0xffff) + (sum >> 16)) & 0xffff                                  # If the sum is greater than 16 bits, add the carry to the sum                                             
    return pack(">H", sum)                                                          # Return the checksum value in network byte order

def build_echo_datagram(data, identifier, number):                                  # Function that builds the ICMP datagram for the echo request
    
    """
    This function builds the ICMP datagram for the echo request, with three parameters: 
    data (the data to send), identifier (the identifier of the ICMP datagram) and number (the number of the ICMP datagram).
    
    params:
    data (bytes): the data to send
    identifier (int): the identifier of the ICMP datagram
    number (int): the number of the ICMP datagram
    
    return:
    bytes: the ICMP datagram
    """
    
    identifier_number_bytes = pack(">Hh", identifier, number)                                   # Concatenation of the identifier and the number of the ICMP datagram    
    Type = pack("b", 8)                                                                         #value for echo 
    Code = pack("b", 0)                                                                         #default value                       
    data_bytes = b""                                                                            #set the value of the data to an empty byte string                             
    for i in data:                                                                              #for each character in the data               
        data_bytes += pack("b", i)                                                              #convert the character to a byte string and add it to the data byte string                                
    icmp_checksum = checksum(Type + Code + b"\x00\x00" + identifier_number_bytes + data_bytes)  #checksum value of the ICMP datagram
    text = Type + Code + icmp_checksum + identifier_number_bytes + data_bytes                   #concatenation of the ICMP datagram
    return text                                                                                 #return the ICMP datagram                            

def build_packet(datagram, identifier, ttl=64, protocole=1, header_checksum=0, ip_source="127.0.0.1", ip_dest="127.0.0.1", options=0, padding=0):                          # Function that builds the packet with the ICMP datagram and the IP header

    """
    This function builds the packet with the ICMP datagram and the IP header, with eight parameters: 
    datagram (the ICMP datagram), identifier (the identifier of the ICMP datagram), ttl (the time to live), protocole (the protocole),
    header_checksum (the checksum value of the IP header), ip_source (the source IP address), ip_dest (the destination IP address),
    options (the options of the IP header) and padding (the padding of the IP header). Refer to the RFC 791 for more information.
    
    params:
    datagram (bytes): the ICMP datagram
    identifier (int): the identifier of the ICMP datagram
    ttl (int): the time to live
    protocole (int): the protocole
    header_checksum (int): the checksum value of the IP header
    ip_source (str): the source IP address
    ip_dest (str): the destination IP address
    options (int): the options of the IP header
    padding (int): the padding of the IP header
    
    return:
    bytes: the packet
    """

    version = 0x4                                                                                                                                                           # in hexadecimal value for the first byte of the IP header
    ihl = 0x5                                                                                                                                                               # in hexadecimal value for the first byte of the IP header          
    version_ihl = pack("b", (version << 4 & 0xf0) + (ihl & 0x0f))                                                                                                           # concatenation of version and ihl in one byte                               
    type_of_service = pack("b", 0)                                                                                                                                          # default value
    total_length = pack(">H", 28 + len(datagram))                                                                                                                           # length of the IP header + length of the ICMP datagram
    flags_fragment_offset = pack(">h", (1416*(len(datagram)//1416)//8))                                                                                                     # calculate the number of fragments                                         
    ttl = pack("B", ttl)                                                                                                                                                    # value defined by the user                                                          
    protocole = pack("b", protocole)                                                                                                                                        # value defined by the user
    identifier = pack(">H", identifier)                                                                                                                                     # value defined by the user
    ip_source = inet_aton(ip_source)                                                                                                                                        # value defined by the user                             
    ip_dest = inet_aton(ip_dest)                                                                                                                                            # value defined by the user             
    header_checksum = checksum(version_ihl + type_of_service + total_length + identifier + flags_fragment_offset + ttl + protocole + b"\x00\x00" + ip_source + ip_dest)     # checksum value of the IP header
    
    ip_header =  version_ihl + type_of_service + total_length + identifier + flags_fragment_offset + ttl + protocole + header_checksum + ip_source + ip_dest                                                                                                                                                      # if there is no options                              
    packet = ip_header + datagram                                                                                                                                           # concatenation of the IP header and the ICMP datagram
    if options != 0:                                                                                                                                                        # if there is options                                                      
        options = pack("B", options)                                                                                                                                        # options converted to bytes                             
        padding = b"\x00" * (32-len(ip_header))                                                                                                                             # padding to fill the IP header                          
        packet = ip_header + options + padding + datagram                                                                                                                   # concatenation of the IP header and the ICMP datagram
    return  packet                                                                                                                                                          # return the packet                                                                   

def send_packet(packet, ip_dest=gethostbyname("saebut.chalons.univ-reims.fr")):     # Function that sends the packet to the destination
    
    """
    This function sends the packet to the destination, with two parameters:
    packet (the packet to send) and ip_dest (the destination IP address or domain name, by default the IP address of "saebut.chalons.univ-reims.fr").
    
    params:
    packet (bytes): the packet to send
    ip_dest (str): the destination IP address or domain name, default value is the IP address of "saebut.chalons.univ-reims.fr"
    
    return:
    None
    """

    ip_dest = gethostbyname(ip_dest)                                                #get the IP address of the destination if it is a domain name, else return the IP address
    rawSocket = socket(AF_INET, SOCK_RAW, IPPROTO_RAW)                              #create a raw socket
    rawSocket.sendto(packet, (ip_dest,0))                                           #send the packet to the destination
    rawSocket.close()                                                               #close the socket

def send_ping(datagram, ip_dest=gethostbyname("saebut.chalons.univ-reims.fr")):     # Function that sends the packet to the destination and receive the response
  
    """
    This function sends the packet to the destination and receive the response, with two parameters:
    datagram (the ICMP datagram) and ip_dest (the destination IP address, by default the IP address of "saebut.chalons.univ-reims.fr").
    
    params:
    datagram (bytes): the ICMP datagram
    ip_dest (str): the destination IP address, default value is the IP address of "saebut.chalons.univ-reims.fr"
    
    return:
    tuple: the received packet, the address of the destination, the response and the time in milliseconds
    """

    time_ms = time()                                                                #get the time in milliseconds
    ip_dest = gethostbyname(ip_dest)                                                #get the IP address of the destination if it is a domain name, else return the IP address
    rawSocket = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)                             #create a raw socket
    rawSocket.sendto(datagram, (ip_dest,0))                                         #send the packet to the destination
    recv_packet, addr = rawSocket.recvfrom(1024)                                    #receive the packet from the destination
    response = unpack_response(recv_packet)                                         #unpack the response
    rawSocket.close()                                                               #close the socket 
    return recv_packet, addr,  response, time_ms                                    #return the received packet, the address of the destination, the response and the time in milliseconds

def unpack_response(datagram):                                                      # Function that unpacks the response from the destination
    
    """
    This function unpacks the response from the destination, with one parameter:
    datagram (the ICMP datagram).
    
    params:
    datagram (bytes): the ICMP datagram
    
    return:
    tuple: the IP header and the ICMP datagram
    """

    ip_name = ['IHL', 'Type of service', 'Total Length', 'ID', 'Flags', 'TTL', 'Protocol', 'Checksum', 'Source IP', 'Destination IP']       # list of the names of the fields of the IP header
    icmp_name = ['Type', 'Code', 'Checksum', 'Identifier', 'Number']                                                                        # list of the names of the fields of the IP header and the ICMP datagram               

    ip_header = {
        'Version': datagram[0] >> 4,                                                #shift the first byte of the datagram to the right by 4 bits to get the version
    }
    ip_header.update(dict(zip(ip_name, unpack(">BBHHHBBH4s4s", datagram[:20]))))    #unpack the IP header and add the values to the dictionary
    icmp_header = dict(zip(icmp_name, unpack(">BBHHh", datagram[20:28])))           #unpack the ICMP datagram and add the values to the dictionary
    ip_header['IHL'] = unpack(">B", datagram[:1])[0] & 0xF                          #get the IHL value from the first byte of the datagram
    ip_header['Checksum'] = hex(ip_header['Checksum'])                              #convert the checksum value to hexadecimal
    ip_header['Source IP'] = inet_ntoa(datagram[12:16])                             #convert the source IP address to a string
    ip_header['Destination IP'] = inet_ntoa(datagram[16:20])                        #convert the destination IP address to a string 
    icmp_header['Checksum'] = hex(icmp_header['Checksum'])                          #convert the checksum value to hexadecimal    

    return ip_header, icmp_header                                                   #return the IP header and the ICMP datagram as a tuple                     

### MAIN ###

if __name__ == "__main__":                                                          #if the script is executed directly 

    data = b"abcdefghijklmnopqrstuvwabcdefghi"                                      #default data for the ICMP datagram  
    identifier = randint(0, 65535)                                                  #a random number between 0 and 65535 for the ICMP datagram                                                                          
    number = 1                                                                      #default number for the ICMP datagram                         
    datagram = build_echo_datagram(data, identifier, number)                        #build the ICMP datagram
    packet = build_packet(datagram, identifier)                                     #build the packet with the ICMP datagram and the IP header  
    packet_send = send_packet(packet, '127.0.0.1')                                  #send the packet to the destination
    ping_send = send_ping(datagram, '127.0.0.1')                                    #send the packet to the destination and receive the response
    response = unpack_response(packet)                                              #unpack the response from the destination
    print(datagram)                                                                 #print the ICMP datagram
    print(packet)                                                                   #print the packet
    print(packet_send)                                                              #print the packet send
    print(response)                                                                 #print the response from the destination
