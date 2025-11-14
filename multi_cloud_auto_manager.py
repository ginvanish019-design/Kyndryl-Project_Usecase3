# ==============================================================
# Azure Auto Manager (Updated for new Azure Monitor SDK)
# Description: Monitors CPU & Memory usage and spins up a new VM if utilization exceeds threshold
# Author: Anish Martin
# ==============================================================

from datetime import datetime, timedelta, timezone
import time
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient

# ✔ NEW Azure Monitor client
from azure.monitor.query import MetricsClient


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
    metrics_client = MetricsClient(azure_cred)
    print("✅ Connected to Azure successfully.")
except Exception as e:
    print(f"⚠️ Azure connection failed: {e}")
    azure_compute = None
    metrics_client = None


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
    """Fetch CPU & Memory usage using Azure Monitor (NEW API)."""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=10)

        response = metrics_client.query_resource(
            resource_id,
            metric_names=["Percentage CPU", "Available Memory Bytes"],
            timespan=f"{start_time}/{end_time}",
            aggregations=["Average"],      # ✔ Updated syntax
        )

        cpu_usage = 0
        memory_usage = 0

        for metric in response.metrics:
            name = metric.name.replace("\n", "").lower()

            # Extract all values
            values = [
                data.average
                for ts in metric.timeseries
                for data in ts.data
                if data.average is not None
            ]

            if not values:
                continue

            avg_value = sum(values) / len(values)

            if name == "percentage cpu":
                cpu_usage = avg_value

            elif name == "available memory bytes":
                total_memory = 8 * 1024 * 1024 * 1024  # 8GB assumption
                memory_usage = 100 - ((avg_value / total_memory) * 100)

        return round(cpu_usage, 2), round(memory_usage, 2)

    except Exception as e:
        print(f"⚠️ Failed to fetch metrics: {e}")
        return 0, 0


def spin_up_additional_vm(original_vm, resource_group):
    """Spin up a new VM based on the existing VM configuration."""
    try:
        new_vm_name = f"{original_vm.name}-extra-{int(time.time())}"
        print(f"🚀 High load detected! Creating new VM: {new_vm_name}")

        vm_params = {
            "location": original_vm.location,
            "hardware_profile": original_vm.hardware_profile,
            "storage_profile": original_vm.storage_profile,
            "os_profile": original_vm.os_profile,
            "network_profile": original_vm.network_profile,
        }

        async_create = azure_compute.virtual_machines.begin_create_or_update(
            resource_group_name=resource_group,
            vm_name=new_vm_name,
            parameters=vm_params,
        )
        async_create.wait()
        print(f"✅ VM Created Successfully: {new_vm_name}")

    except Exception as e:
        print(f"⚠️ Failed to create new VM: {e}")


def monitor_vm_performance(vm_name):
    print(f"\n🔍 Checking performance for VM: {vm_name}")
    vm, rg = find_vm_by_name(vm_name)

    if not vm:
        print(f"❌ VM '{vm_name}' not found.")
        return

    resource_id = vm.id
    cpu_usage, memory_usage = get_vm_metrics(resource_id)

    print(f"📊 VM Metrics → CPU: {cpu_usage}% | Memory: {memory_usage}%")

    if cpu_usage > CPU_THRESHOLD or memory_usage > MEMORY_THRESHOLD:
        print(f"⚠️ High Utilization Detected!")
        spin_up_additional_vm(vm, rg)
    else:
        print("✅ Utilization normal. No action required.")


# =======================================================
# MAIN WORKFLOW
# =======================================================
def main():
    print("=" * 70)
    print(f"☁️ Azure Auto Manager Started • {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    if azure_compute and metrics_client:
        monitor_vm_performance(TARGET_VM_NAME)
    else:
        print("❌ Azure connection not established.")

    print("\n✅ Azure VM monitoring completed.")


if __name__ == "__main__":
    main()
