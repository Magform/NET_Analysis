import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#----------- Configuration variables -----------
rtt_csv_filename = 'RTT.csv'
results_directory = 'results'
#-----------------------------------------------

# Create results directory if it does not exist
os.makedirs(results_directory, exist_ok=True)

# Load ping results from CSV
ping_results = pd.read_csv(rtt_csv_filename)
R_results = {}

# Summary statistics
summary_stats = ping_results.groupby(['server', 'payload_size']).agg(
    rtt_min=('rtt_min', 'min'),
    rtt_avg=('rtt_avg', 'mean'),
    rtt_max=('rtt_max', 'max'),
    rtt_std=('rtt_std', 'mean')
).reset_index()

# Generate separate plots for each server
for server in summary_stats['server'].unique():
    server_data = summary_stats[summary_stats['server'] == server]
    
    # Plot for rtt_min, rtt_avg, rtt_max
    plt.figure(figsize=(10, 6))
    for stat in ['rtt_min', 'rtt_avg', 'rtt_max']:
        plt.plot((server_data['payload_size'] + 28) * 8, server_data[stat], label=f"{stat}", marker='o')
    plt.xlabel('Payload Size (bytes)')
    plt.ylabel('RTT (ms)')
    plt.title(f'RTT vs Payload Size for {server}')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(results_directory, f'rtt_vs_payload_size_{server}.png'))
    plt.close()
    
    # Plot for rtt_std
    plt.figure(figsize=(10, 6))
    plt.plot((server_data['payload_size'] + 28) * 8, server_data['rtt_std'], label='rtt_std', marker='o')
    plt.xlabel('Payload Size (bytes)')
    plt.ylabel('RTT std (ms)')
    plt.title(f'RTT std vs Payload Size for {server}')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(results_directory, f'rtt_std_vs_payload_size_{server}.png'))
    plt.close()

    # Estimate throughput
    try:
        coeff = np.polyfit(server_data['payload_size'], server_data['rtt_min'], 1)
        a = coeff[0]
        n = len(server_data['payload_size'])
        throughput = n / a
        throughput_bottleneck = 2 / a
        
        R_results[server] = {
            'coefficient': a,
            'throughput': throughput,
            'throughput_bottleneck': throughput_bottleneck
        }
    except np.RankWarning as e:
        print(f"Could not fit a polynomial for server {server}: {e}")

# Print summary statistics
print("Summary Statistics:")
print(summary_stats.describe())

# Print the estimated throughput results
print("Estimated Throughput Results:")
for server, results in R_results.items():
    print(f"Server: {server}")
    print(f"  Coefficient (a): {results['coefficient']}")
    print(f"  Throughput: {results['throughput']:.2f} bps")
    print(f"  Bottleneck Throughput: {results['throughput_bottleneck']:.2f} bps")
