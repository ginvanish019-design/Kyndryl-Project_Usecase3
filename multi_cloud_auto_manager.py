# ==============================================================
# Azure Auto Manager
# Description: Checks VM performance and spins up a new VM if needed
# Author: Anish Martin
# ==============================================================

from datetime import datetime, timedelta, timezone
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.monitor.query import MetricsQueryClient
from azure.mgmt.compute.models import VirtualMachine
import time

# =======================================================
# Configuration
# =======================================================
AZURE_SUBSCRIPTION_ID = "c070b0a7-e56f-4350-a4bd-3c01811a284c"
TARGET_VM_NAME = "anish_test-vm"
CPU_THRESHOLD = 70
MEMORY_THRESHOLD = 70

# =======================================================
# Azure Setup
# =======================================================
try:
    print("🔑 Authenticating to Azure...")
    azure_cred = DefaultAzureCredential()
    azure_compute = ComputeManagementClient(azure_cred, AZURE_SUBSCRIPTION_ID)
    metrics_client = MetricsQueryClient(azure_cred)
    print("✅ Connected to Azure successfully.")
except Exception as e:
    print(f"⚠️ Azure connection failed: {e}")
    azure_compute = None

# =======================================================
# Helper Functions
# =======================================================
def find_vm_by_name(vm_name):
    """Find the VM and return its object and resource group."""
    vms = azure_compute.virtual_machines.list_all()
    for vm in vms:
        if vm.name.lower() == vm_name.lower():
            rg = vm.id.split("/")[4]
            return vm, rg
    return None, None

def get_vm_metrics(resource_id):
    """Fetch CPU and memory metrics from Azure Monitor."""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=10)

        response = metrics_client.query_resource(
            resource_id,
            metric_names=["Percentage CPU", "Available Memory Bytes"],
            timespan=f"{start_time}/{end_time}"
        )

        cpu_usage = None
        memory_usage = None

        for metric in response.metrics:
            if metric.name == "Percentage CPU":
                cpu_usage = metric.timeseries[0].data[-1].average
            elif metric.name == "Available Memory Bytes":
                # Convert available memory to percentage used (assuming 8GB total for demo)
                total_memory = 8 * 1024 * 1024 * 1024
                memory_available = metric.timeseries[0].data[-1].average
                memory_usage = 100 - ((memory_available / total_memory) * 100)

        return cpu_usage or 0, memory_usage or 0

    except Exception as e:
        print(f"⚠️ Failed to fetch metrics: {e}")
        return 0, 0

def spin_up_additional_vm(original_vm, resource_group):
    """Create a new VM clone if load is high."""
    try:
        new_vm_name = f"{original_vm.name}-extra-{int(time.time())}"
        print(f"🚀 High load detected! Creating new VM: {new_vm_name}")

        vm_params = {
            "location": original_vm.location,
            "hardware_profile": original_vm.hardware_profile,
            "storage_profile": original_vm.storage_profile,
            "os_profile": original_vm.os_profile,
            "network_profile": original_vm.network_profile
        }

        async_vm_creation = azure_compute.virtual_machines.begin_create_or_update(
            resource_group, new_vm_name, vm_params
        )
        async_vm_creation.wait()
        print(f"✅ Successfully created additional VM: {new_vm_name}")

    except Exception as e:
        print(f"⚠️ Failed to create new VM: {e}")

def check_vm_status_and_scale(vm_name):
    """Check the VM's performance and manage scaling."""
    print(f"\n🔍 Checking VM performance for: {vm_name}")
    vm, rg = find_vm_by_name(vm_name)
    if not vm:
        print(f"❌ VM '{vm_name}' not found.")
        return

    resource_id = vm.id
    cpu, mem = get_vm_metrics(resource_id)

    print(f"📊 VM Metrics - CPU: {cpu:.2f}% | Memory Used: {mem:.2f}%")

    if cpu > CPU_THRESHOLD or mem > MEMORY_THRESHOLD:
        print(f"⚠️ High resource usage detected! (CPU: {cpu:.1f}%, Memory: {mem:.1f}%)")
        spin_up_additional_vm(vm, rg)
    else:
        print(f"✅ VM is healthy. No scaling needed.")

# =======================================================
# MAIN WORKFLOW
# =======================================================
def main():
    print("=" * 70)
    print(f"☁️ Azure Auto Manager Started at {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    if azure_compute:
        check_vm_status_and_scale(TARGET_VM_NAME)
    else:
        print("❌ Azure connection not established.")

    print("\n✅ Azure VM monitoring completed successfully.")

# =======================================================
# Entry Point
# =======================================================
if __name__ == "__main__":
    main()
