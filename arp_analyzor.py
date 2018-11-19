import pyshark
import socket
from subprocess import check_output,CalledProcessError,TimeoutExpired
from nested_dict import nested_dict
from contextlib import contextmanager
import signal
import re
from decimal import Decimal




global timeout_time
timeout_time = 2


def raise_error(signum, frame):
    """This handler will raise an error inside gethostbyname"""
    raise OSError

@contextmanager
def set_signal(signum, handler):
    """Temporarily set signal"""
    old_handler = signal.getsignal(signum)
    signal.signal(signum, handler)
    try:
        yield
    finally:
        signal.signal(signum, old_handler)

@contextmanager
def set_alarm(time):
    """Temporarily set alarm"""
    signal.setitimer(signal.ITIMER_REAL, time)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0) # Disable alarm

@contextmanager
def raise_on_timeout(time):
    """This context manager will raise an OSError unless
    The with scope is exited in time."""
    with set_signal(signal.SIGALRM, raise_error):
        with set_alarm(time):
            yield

global resolved_dict
resolved_dict = {}

# this function resolve an IP address using nslookup and nmblookup tool of bash.
def resolve(ipa):
    hostname = ""
    hostname1 = ""
    hostname2 = ""
    if ipa in resolved_dict:
        return resolved_dict[ipa]
    try:
        with raise_on_timeout(timeout_time):
            a = socket.gethostbyaddr(ipa)
            hostname1 = a[0]
            resolved_dict[ipa] = hostname1
            matchObj = re.match(r"(dhcp|vpn)\d*.iit.cnr.it", hostname1)
            if not matchObj:
                hostname = hostname1
    except OSError:
        pass
    if hostname == "":
        try:
            out = check_output(["nmblookup", "-A", ipa],timeout=timeout_time)
            hostname2=str(out).split("\\n")[1].split()[0].replace("\\t", "")
            hostname = hostname2
        except (CalledProcessError,TimeoutExpired) as e:
            if hostname1 != "":
                hostname = hostname1
            else:
                hostname = ipa

    return hostname

#for the ARP Packets we read the pcap from the CNR and filter the traffic for arp packets but the ARPs which is not emmited from
#the DHCP Server 146.48.99.254

cap = pyshark.FileCapture('/root/captures/sofar.pcap',display_filter="arp and not arp.src.proto_ipv4 == 146.48.99.254 and not arp.dst.proto_ipv4 == 146.48.96.1 and not arp.dst.proto_ipv4 == 146.48.96.2")


global relations
relations = {}



nd = nested_dict(2, int)

# This is the main function which reads every packet and fills the relations Dictionary.
# This Dict has a key for source IP address and the value is a set of IP addresses that the key is trying to resolve
# through ARP protocol


def print_conversation_header(pkt):
    # x=Decimal(int(pkt.number)/96100)*100
    # output = round(x, 4)
    # print(str(output) + "%")
    my_data = pkt['ARP']
    src_ip = my_data.src_proto_ipv4
    dst_ip = my_data.dst_proto_ipv4
    if src_ip == dst_ip :
        return
    if dst_ip in nd:
        if src_ip in nd[src_ip]:
            nd[dst_ip][src_ip] += 1
            return
    nd[src_ip][dst_ip] +=1


def print_highest_layer(pkt):
    print (pkt.highest_layer)





cap.apply_on_packets(print_conversation_header)

#outfile = open('arp_graph_new.txt','w')

days = 2
threshold = 5

for key in nd:
    for host in nd[key]:
        #key_resolved = resolve(key)
        #host_resolved =resolve(host)
        # temp_sentence = key_resolved + " " + host_resolved + "  " + str(nd[key][host])
        if nd[key][host]/days > threshold:
            temp_sentence = key + " " + host + "  " + str(nd[key][host])
            print(temp_sentence)
        #outfile.write(temp_sentence + "\n")


#outfile.close()
