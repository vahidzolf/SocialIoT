import pyshark
import socket
from subprocess import check_output,CalledProcessError

cap = pyshark.FileCapture('/root/captures/CNR_Big_capture.pcap',display_filter="not arp.src.proto_ipv4 == 146.48.99.254 and arp")


global relations
relations = {}

def resolve(ipa):
    try:
        a = socket.gethostbyaddr(ipa)
        return a[0]
    except socket.herror:
        try:
            out = check_output(["nmblookup", "-A", ipa])
            hostname=str(out).split("\\n")[1].split()[0].replace("\\t", "")
            return hostname
        except CalledProcessError:
            pass

def print_conversation_header(pkt):

    my_data = pkt['ARP']
    src_ip = my_data.src_proto_ipv4
    dst_ip = my_data.dst_proto_ipv4
    try:
        relations[src_ip].append(dst_ip)
    except KeyError:
        relations[src_ip]=[dst_ip]


def print_highest_layer(pkt):
    print (pkt.highest_layer)

cap.apply_on_packets(print_conversation_header)

outfile = open('arp_graph.txt','w')


counter = 0
for key in relations:
    temp_set = set(relations[key])
    for element in temp_set:
        count = relations[key].count(element)
        try:
            print (key + " ====> "  + resolve(key))
        except TypeError:


            print(key)
        try:
            print(element + " ====> "  + resolve(element))
        except TypeError:
            print(element)
        #outfile.write(resolve(key) + "\t" + resolve(element) + "\t" + str(count) + '\n')

#now I need to convert IP numbers to host

outfile.close()
exit(1)