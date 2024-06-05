import subprocess
import re
import csv


#----------- Configuration variables -----------

servers = [
    "atl.speedtest.clouvider.net", 
    "nyc.speedtest.clouvider.net",
    "lon.speedtest.clouvider.net", 
    "la.speedtest.clouvider.net",
    "paris.testdebit.info",
    "lyon.testdebit.info",
    "aix-marseille.testdebit.info",
    "1.1.1.1"
]

packet_count = 4
payload_sizes = range(10, 1473, 10)
max_ttl = 64
rtt_csv_filename = 'RTT.csv'
hops_csv_filename = 'hops.csv'

#-----------------------------------------------


# Function to execute ping
def ping_server(server, packet_count=4, payload_size=56, ttl=64):
    command = f'ping -c {packet_count} -s {payload_size} -t {ttl} {server}'
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return result.stdout.decode('utf-8')

# Function to execute traceroute
def traceroute_server(server):
    command = f'traceroute {server}'
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return result.stdout.decode('utf-8')

# Function to extract RTT from ping output
def extract_rtt_from_ping_output(ping_output):
    last_line = ping_output.strip().split('\n')[-1]
    rtt_match = re.findall(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms', last_line)
    if rtt_match:
        min_rtt, avg_rtt, max_rtt, stddev_rtt = map(float, rtt_match[0])
        return min_rtt, avg_rtt, max_rtt, stddev_rtt
    return None, None, None, None

# Function to trace and calculate hops
def trace_and_calculate_hops(server, max_ttl, packet_count=4, payload_size=56):
    for ttl in range(max_ttl, 0, -1):
        ping_output = ping_server(server, packet_count, payload_size=payload_size, ttl=ttl)
        if "Time to live exceeded" in ping_output and "rtt" not in ping_output:
            traceroute_output = traceroute_server(server)
            hops = len(traceroute_output.strip().split('\n')) - 1
            return ttl+1, hops  # Increment TTL to reflect the successful ping response
    return None, None

# Write headers to CSV files
with open(rtt_csv_filename, mode='w', newline='') as rtt_file, open(hops_csv_filename, mode='w', newline='') as hops_file:
    rtt_writer = csv.writer(rtt_file)
    hops_writer = csv.writer(hops_file)
    
    rtt_writer.writerow(['server', 'payload_size', 'rtt_min', 'rtt_max', 'rtt_avg', 'rtt_std'])
    hops_writer.writerow(['server', 'ping_hops', 'traceroute_hops'])

    # Execute ping for each server and payload size combination
    for server in servers:
        ttl, hops = trace_and_calculate_hops(server, max_ttl=max_ttl)
        if ttl is not None:
            hops_writer.writerow([server, ttl, hops])
            for payload_size in payload_sizes:
                ping_output = ping_server(server, packet_count=packet_count, payload_size=payload_size, ttl=64)
                min_rtt, avg_rtt, max_rtt, stddev_rtt = extract_rtt_from_ping_output(ping_output)
                
                if min_rtt is not None:
                    rtt_writer.writerow([server, payload_size, min_rtt, max_rtt, avg_rtt, stddev_rtt])
    print("Saved RTT results and hops to respective CSV files.")
