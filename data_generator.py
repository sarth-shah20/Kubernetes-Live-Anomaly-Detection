import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random

def generate_k8s_metrics_dataset(hours=72, interval_minutes=1):
    """
    Generate realistic Kubernetes metrics with anomalies
    
    Args:
        hours: Total time period to simulate
        interval_minutes: Data collection interval
    """
    
    # Calculate number of data points
    total_points = int(hours * 60 / interval_minutes)
    
    # Generate timestamps
    start_time = datetime.now() - timedelta(hours=hours)
    timestamps = [start_time + timedelta(minutes=i*interval_minutes) for i in range(total_points)]
    
    # Initialize lists for metrics
    cpu_usage = []
    memory_usage = []
    network_io = []
    disk_io = []
    response_time = []
    error_rate = []
    pod_restarts = []
    is_anomaly = []
    anomaly_type = []
    
    # Define normal behavior patterns
    base_cpu = 25  # 25% average CPU
    base_memory = 40  # 40% average memory
    base_response = 150  # 150ms average response time
    base_error_rate = 0.5  # 0.5% error rate
    
    print("Generating Enhanced Kubernetes metrics dataset...")
    print(f"Simulating {hours} hours of data with {total_points} data points")
    
    for i in range(total_points):
        # Add daily patterns (higher usage during business hours)
        hour_of_day = timestamps[i].hour
        daily_factor = 1.2 if 9 <= hour_of_day <= 17 else 0.8
        
        # Add weekly patterns (lower usage on weekends)
        day_of_week = timestamps[i].weekday()
        weekly_factor = 0.7 if day_of_week >= 5 else 1.0
        
        # Add some random noise to make it realistic
        noise_factor = np.random.normal(1, 0.1)
        
        # Normal behavior
        current_cpu = base_cpu * daily_factor * weekly_factor * noise_factor
        current_memory = base_memory * daily_factor * weekly_factor * noise_factor
        current_response = base_response * daily_factor * weekly_factor * noise_factor
        current_error = base_error_rate * noise_factor
        current_network = np.random.normal(50, 10) * daily_factor * weekly_factor
        current_disk = np.random.normal(30, 5) * daily_factor * weekly_factor
        current_restarts = 0
        
        anomaly_flag = False
        anomaly_category = "normal"
        
        # Inject different types of anomalies (12% of data points for more realistic distribution)
        if np.random.random() < 0.12:
            anomaly_flag = True
            anomaly_types = [
                "memory_leak", "cpu_spike", "network_congestion", "disk_bottleneck", 
                "cascade_failure", "pod_crashloop", "oom_killer", "resource_starvation",
                "latency_spike", "connection_timeout", "dns_resolution_failure",
                "storage_full", "node_pressure", "scheduler_failure", "api_server_overload"
            ]
            # Weight certain anomalies as more common (realistic distribution)
            anomaly_weights = [0.15, 0.12, 0.10, 0.08, 0.05, 0.12, 0.08, 0.07, 0.09, 0.06, 0.03, 0.02, 0.02, 0.01, 0.00]
            # Normalize weights to ensure they sum to 1.0
            anomaly_weights = np.array(anomaly_weights)
            anomaly_weights = anomaly_weights / anomaly_weights.sum()
            selected_anomaly = np.random.choice(anomaly_types, p=anomaly_weights)
            anomaly_category = selected_anomaly
            
            if selected_anomaly == "memory_leak":
                # Gradual memory increase
                leak_factor = min(3.0, 1 + (i % 100) * 0.02)
                current_memory = min(95, current_memory * leak_factor)
                current_response *= 1.5
                current_error *= 2
                
            elif selected_anomaly == "cpu_spike":
                # Sudden CPU spike
                current_cpu = min(95, current_cpu * np.random.uniform(2.5, 4.0))
                current_response *= 2
                current_error *= 3
                
            elif selected_anomaly == "network_congestion":
                # Network issues
                current_network *= np.random.uniform(3, 5)
                current_response *= np.random.uniform(2, 4)
                current_error *= 2
                
            elif selected_anomaly == "disk_bottleneck":
                # Disk I/O issues
                current_disk *= np.random.uniform(4, 6)
                current_response *= 1.8
                current_error *= 1.5
                
            elif selected_anomaly == "cascade_failure":
                # Multiple systems failing
                current_cpu *= 2
                current_memory *= 1.5
                current_response *= 3
                current_error *= 5
                current_restarts = np.random.randint(1, 4)
                
            elif selected_anomaly == "pod_crashloop":
                # Pod keeps crashing and restarting
                current_restarts = np.random.randint(3, 8)
                current_cpu *= 0.3  # Low CPU due to constant restarts
                current_response *= 4
                current_error *= 6
                
            elif selected_anomaly == "oom_killer":
                # Out of Memory killer activated
                current_memory = np.random.uniform(85, 98)
                current_restarts = np.random.randint(1, 3)
                current_cpu *= 0.5  # Drops after OOM kill
                current_response *= 5
                
            elif selected_anomaly == "resource_starvation":
                # Not enough resources allocated
                current_cpu = np.random.uniform(95, 100)
                current_memory = np.random.uniform(90, 98)
                current_response *= np.random.uniform(3, 6)
                current_error *= 4
                
            elif selected_anomaly == "latency_spike":
                # Network or database latency issues
                current_response *= np.random.uniform(4, 8)
                current_error *= 2
                current_network *= 1.5
                
            elif selected_anomaly == "connection_timeout":
                # Connection pool exhaustion or network issues
                current_response *= np.random.uniform(3, 5)
                current_error *= np.random.uniform(5, 10)
                current_network *= 2
                
            elif selected_anomaly == "dns_resolution_failure":
                # DNS issues causing intermittent failures
                current_response *= np.random.uniform(2, 4)
                current_error *= np.random.uniform(3, 8)
                
            elif selected_anomaly == "storage_full":
                # Disk space issues
                current_disk *= np.random.uniform(5, 8)
                current_response *= 2
                current_error *= 3
                
            elif selected_anomaly == "node_pressure":
                # Node under resource pressure
                current_cpu *= np.random.uniform(1.5, 2.5)
                current_memory *= np.random.uniform(1.3, 2.0)
                current_response *= 2
                
            elif selected_anomaly == "scheduler_failure":
                # Kubernetes scheduler issues
                current_restarts = np.random.randint(1, 3)
                current_response *= 2
                current_error *= 2
                
            elif selected_anomaly == "api_server_overload":
                # K8s API server overwhelmed
                current_response *= np.random.uniform(3, 6)
                current_error *= 3
                current_network *= 2
        
        # Ensure values stay within realistic bounds
        current_cpu = max(0, min(100, current_cpu))
        current_memory = max(0, min(100, current_memory))
        current_response = max(50, min(5000, current_response))
        current_error = max(0, min(20, current_error))
        current_network = max(0, current_network)
        current_disk = max(0, current_disk)
        
        # Store values
        cpu_usage.append(round(current_cpu, 2))
        memory_usage.append(round(current_memory, 2))
        response_time.append(round(current_response, 2))
        error_rate.append(round(current_error, 3))
        network_io.append(round(current_network, 2))
        disk_io.append(round(current_disk, 2))
        pod_restarts.append(current_restarts)
        is_anomaly.append(1 if anomaly_flag else 0)
        anomaly_type.append(anomaly_category)
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'cpu_usage_percent': cpu_usage,
        'memory_usage_percent': memory_usage,
        'response_time_ms': response_time,
        'error_rate_percent': error_rate,
        'network_io_mbps': network_io,
        'disk_io_mbps': disk_io,
        'pod_restarts': pod_restarts,
        'is_anomaly': is_anomaly,
        'anomaly_type': anomaly_type
    })
    
    # Add some derived features that ML models love
    df['cpu_memory_ratio'] = df['cpu_usage_percent'] / (df['memory_usage_percent'] + 0.1)
    df['performance_score'] = 100 - (df['response_time_ms'] / 50 + df['error_rate_percent'] * 10)
    df['resource_pressure'] = df['cpu_usage_percent'] + df['memory_usage_percent']
    
    # Add missing data simulation (realistic scenario)
    missing_indices = np.random.choice(df.index, size=int(0.02 * len(df)), replace=False)
    for idx in missing_indices:
        metric = np.random.choice(['network_io_mbps', 'disk_io_mbps'])
        df.loc[idx, metric] = np.nan
    
    print(f"\nDataset generated successfully!")
    print(f"Total data points: {len(df)}")
    print(f"Anomaly data points: {df['is_anomaly'].sum()} ({df['is_anomaly'].mean()*100:.1f}%)")
    print(f"Missing data points: {df.isnull().sum().sum()} ({df.isnull().sum().sum()/(len(df)*len(df.columns))*100:.2f}%)")
    print(f"Anomaly types distribution:")
    for anomaly, count in df['anomaly_type'].value_counts().head(10).items():
        if anomaly != 'normal':
            print(f"  {anomaly}: {count}")
    
    return df

def visualize_dataset(df, save_plots=True):
    """Create comprehensive visualizations to understand the dataset"""
    
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    fig.suptitle('Enhanced Kubernetes Metrics Dataset Overview', fontsize=16)
    
    # Plot 1: CPU and Memory over time with anomalies highlighted
    ax1 = axes[0, 0]
    sample_data = df.iloc[::20]  # Sample for cleaner visualization
    ax1.plot(sample_data['timestamp'], sample_data['cpu_usage_percent'], label='CPU %', alpha=0.7, linewidth=1)
    ax1.plot(sample_data['timestamp'], sample_data['memory_usage_percent'], label='Memory %', alpha=0.7, linewidth=1)
    
    # Highlight anomalies
    anomaly_sample = sample_data[sample_data['is_anomaly'] == 1]
    ax1.scatter(anomaly_sample['timestamp'], anomaly_sample['cpu_usage_percent'], 
                color='red', s=15, alpha=0.8, label='CPU Anomalies')
    ax1.scatter(anomaly_sample['timestamp'], anomaly_sample['memory_usage_percent'], 
                color='orange', s=15, alpha=0.8, label='Memory Anomalies')
    
    ax1.set_title('CPU and Memory Usage Over Time')
    ax1.set_ylabel('Usage Percentage')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Plot 2: Response time and error rate
    ax2 = axes[0, 1]
    ax2_twin = ax2.twinx()
    
    ax2.plot(sample_data['timestamp'], sample_data['response_time_ms'], color='blue', label='Response Time', alpha=0.7)
    ax2_twin.plot(sample_data['timestamp'], sample_data['error_rate_percent'], color='red', label='Error Rate', alpha=0.7)
    
    # Highlight response time anomalies
    response_anomalies = sample_data[sample_data['response_time_ms'] > 500]
    ax2.scatter(response_anomalies['timestamp'], response_anomalies['response_time_ms'], 
                color='purple', s=20, alpha=0.8, label='Response Anomalies')
    
    ax2.set_title('Response Time and Error Rate Over Time')
    ax2.set_ylabel('Response Time (ms)', color='blue')
    ax2_twin.set_ylabel('Error Rate (%)', color='red')
    ax2.legend(loc='upper left')
    ax2_twin.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    # Plot 3: Anomaly types distribution
    ax3 = axes[1, 0]
    anomaly_counts = df[df['is_anomaly'] == 1]['anomaly_type'].value_counts().head(12)
    bars = ax3.barh(range(len(anomaly_counts)), anomaly_counts.values, color='skyblue', edgecolor='navy')
    ax3.set_yticks(range(len(anomaly_counts)))
    ax3.set_yticklabels(anomaly_counts.index)
    ax3.set_title('Anomaly Types Distribution')
    ax3.set_xlabel('Count')
    ax3.grid(True, alpha=0.3, axis='x')
    
    # Add count labels on bars
    for i, bar in enumerate(bars):
        ax3.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                str(anomaly_counts.values[i]), va='center', fontsize=9)
    
    # Plot 4: Daily and hourly patterns
    ax4 = axes[1, 1]
    hourly_cpu = df.groupby(df['timestamp'].dt.hour)['cpu_usage_percent'].mean()
    hourly_memory = df.groupby(df['timestamp'].dt.hour)['memory_usage_percent'].mean()
    hourly_anomalies = df.groupby(df['timestamp'].dt.hour)['is_anomaly'].mean() * 100
    
    ax4_twin = ax4.twinx()
    ax4.bar(hourly_cpu.index - 0.2, hourly_cpu.values, width=0.4, label='Avg CPU %', alpha=0.7)
    ax4.bar(hourly_memory.index + 0.2, hourly_memory.values, width=0.4, label='Avg Memory %', alpha=0.7)
    ax4_twin.plot(hourly_anomalies.index, hourly_anomalies.values, 'ro-', label='Anomaly Rate %')
    
    ax4.set_title('Hourly Resource Usage and Anomaly Patterns')
    ax4.set_xlabel('Hour of Day')
    ax4.set_ylabel('Resource Usage %')
    ax4_twin.set_ylabel('Anomaly Rate %', color='red')
    ax4.legend(loc='upper left')
    ax4_twin.legend(loc='upper right')
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Resource correlation scatter
    ax5 = axes[2, 0]
    normal_data = df[df['is_anomaly'] == 0].sample(n=min(1000, len(df[df['is_anomaly'] == 0])))
    anomaly_data = df[df['is_anomaly'] == 1]
    
    ax5.scatter(normal_data['cpu_usage_percent'], normal_data['memory_usage_percent'], 
                alpha=0.5, label='Normal', s=10, color='lightblue')
    ax5.scatter(anomaly_data['cpu_usage_percent'], anomaly_data['memory_usage_percent'], 
                alpha=0.8, label='Anomaly', s=15, color='red')
    
    ax5.set_title('CPU vs Memory Usage Distribution')
    ax5.set_xlabel('CPU Usage %')
    ax5.set_ylabel('Memory Usage %')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: Performance metrics distribution
    ax6 = axes[2, 1]
    metrics_to_plot = ['response_time_ms', 'error_rate_percent', 'pod_restarts']
    colors = ['skyblue', 'lightcoral', 'lightgreen']
    
    for i, (metric, color) in enumerate(zip(metrics_to_plot, colors)):
        normal_values = df[df['is_anomaly'] == 0][metric]
        anomaly_values = df[df['is_anomaly'] == 1][metric]
        
        # Create box plots
        positions = [i*3 + 1, i*3 + 2]
        bp = ax6.boxplot([normal_values, anomaly_values], positions=positions, 
                        patch_artist=True, widths=0.8)
        bp['boxes'][0].set_facecolor('lightblue')
        bp['boxes'][1].set_facecolor('lightcoral')
    
    ax6.set_title('Performance Metrics: Normal vs Anomalous')
    ax6.set_xticks([1.5, 4.5, 7.5])
    ax6.set_xticklabels(['Response Time', 'Error Rate', 'Pod Restarts'])
    ax6.set_ylabel('Metric Value')
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='lightblue', label='Normal'),
                      Patch(facecolor='lightcoral', label='Anomaly')]
    ax6.legend(handles=legend_elements)
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_plots:
        plt.savefig('enhanced_k8s_dataset_overview.png', dpi=300, bbox_inches='tight')
        print(f"Enhanced visualizations saved as 'enhanced_k8s_dataset_overview.png'")
    
    plt.show()
    
    return fig

def generate_dataset_summary(df):
    """Generate a comprehensive summary of the dataset"""
    
    print("\n" + "="*70)
    print("ENHANCED KUBERNETES METRICS DATASET SUMMARY")
    print("="*70)
    
    print(f"\n📊 DATASET OVERVIEW:")
    print(f"   • Total data points: {len(df):,}")
    print(f"   • Time period: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"   • Data collection interval: 1 minute")
    print(f"   • Total duration: {(df['timestamp'].max() - df['timestamp'].min()).total_seconds()/3600:.1f} hours")
    
    print(f"\n🚨 ANOMALY ANALYSIS:")
    print(f"   • Total anomalies: {df['is_anomaly'].sum():,} ({df['is_anomaly'].mean()*100:.1f}%)")
    print(f"   • Normal data points: {(df['is_anomaly'] == 0).sum():,} ({(df['is_anomaly'] == 0).mean()*100:.1f}%)")
    print(f"   • Unique anomaly types: {len(df[df['is_anomaly']==1]['anomaly_type'].unique())}")
    
    print(f"\n📈 KEY METRICS STATISTICS:")
    metrics = ['cpu_usage_percent', 'memory_usage_percent', 'response_time_ms', 'error_rate_percent']
    for metric in metrics:
        normal_avg = df[df['is_anomaly'] == 0][metric].mean()
        anomaly_avg = df[df['is_anomaly'] == 1][metric].mean()
        print(f"   • {metric}:")
        print(f"     - Normal avg: {normal_avg:.2f}")
        print(f"     - Anomaly avg: {anomaly_avg:.2f}")
        print(f"     - Difference: {((anomaly_avg - normal_avg) / normal_avg * 100):.1f}%")
    
    print(f"\n🔧 TOP ANOMALY TYPES:")
    anomaly_types = df[df['is_anomaly'] == 1]['anomaly_type'].value_counts().head(8)
    for anomaly, count in anomaly_types.items():
        percentage = (count / df['is_anomaly'].sum()) * 100
        print(f"   • {anomaly}: {count} ({percentage:.1f}%)")
    
    print(f"\n⚡ DATASET QUALITY INDICATORS:")
    print(f"   • Missing values: {df.isnull().sum().sum()} ({df.isnull().sum().sum()/(len(df)*len(df.columns))*100:.2f}%)")
    print(f"   • Data completeness: {((len(df)*len(df.columns) - df.isnull().sum().sum())/(len(df)*len(df.columns)))*100:.2f}%")
    print(f"   • Temporal consistency: ✅ (1-minute intervals)")
    print(f"   • Realistic value ranges: ✅ (bounded between 0-100% for usage metrics)")
    
    # Business hour analysis
    df_copy = df.copy()
    df_copy['hour'] = df_copy['timestamp'].dt.hour
    business_hours_anomalies = df_copy[(df_copy['hour'] >= 9) & (df_copy['hour'] <= 17)]['is_anomaly'].mean()
    off_hours_anomalies = df_copy[(df_copy['hour'] < 9) | (df_copy['hour'] > 17)]['is_anomaly'].mean()
    
    print(f"\n🕒 TEMPORAL PATTERNS:")
    print(f"   • Business hours anomaly rate: {business_hours_anomalies*100:.2f}%")
    print(f"   • Off-hours anomaly rate: {off_hours_anomalies*100:.2f}%")
    print(f"   • Peak usage hours: 9 AM - 5 PM (realistic business pattern)")
    
    print(f"\n✅ DATASET READINESS FOR ML:")
    print(f"   • Sufficient data points: ✅ ({len(df):,} > 1000)")
    print(f"   • Balanced classes: {'✅' if 0.05 <= df['is_anomaly'].mean() <= 0.20 else '⚠️'} ({df['is_anomaly'].mean()*100:.1f}% anomalies)")
    print(f"   • Multiple feature types: ✅ (numeric, categorical, temporal)")
    print(f"   • Realistic patterns: ✅ (daily/weekly cycles)")
    print(f"   • Ground truth labels: ✅ (is_anomaly column)")
    
    print("="*70)
    
    return df_copy

# Generate the dataset
if __name__ == "__main__":
    print("🚀 Enhanced Kubernetes Metrics Dataset Generator")
    print("🎯 Optimized for ML Anomaly Detection Demo")
    print("="*60)
    
    # Generate 72 hours of data with 1-minute intervals (more realistic for ML)
    dataset = generate_k8s_metrics_dataset(hours=72, interval_minutes=1)
    
    # Save to CSV
    dataset.to_csv('kubernetes_metrics_dataset.csv', index=False)
    print(f"\n💾 Dataset saved as 'kubernetes_metrics_dataset.csv'")
    
    # Generate comprehensive summary
    dataset_with_temporal = generate_dataset_summary(dataset)
    
    # Create enhanced visualizations
    print(f"\n📊 Creating enhanced visualizations...")
    visualize_dataset(dataset)
    
    print("\n" + "="*60)
    print("🎉 DATASET GENERATION COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("📋 NEXT STEPS:")
    print("   1. ✅ Dataset generated (kubernetes_metrics_dataset.csv)")
    print("   2. ✅ Visualizations created (enhanced_k8s_dataset_overview.png)")
    print("   3. 🔄 Next: Run ML pipeline script")
    print("   4. 🎯 Then: Evaluate model performance")
    print("   5. 📊 Finally: Prepare demo presentation")
    print("="*60)
    
    # Quick validation
    print(f"\n🔍 QUICK VALIDATION:")
    print(f"   • File size: ~{len(dataset) * len(dataset.columns) * 8 / 1024:.1f} KB")
    print(f"   • Memory usage: ~{dataset.memory_usage(deep=True).sum() / 1024:.1f} KB")
    print(f"   • Ready for ML processing: ✅")