# ==============================================================
# Azure Auto Manager
# Description: Checks and manages a specific Azure Virtual Machine
# Author: Anish Martin
# ==============================================================

from datetime import datetime, timezone
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient

# =======================================================
# Configuration
# =======================================================
AZURE_SUBSCRIPTION_ID = "c070b0a7-e56f-4350-a4bd-3c01811a284c"
TARGET_VM_NAME = "anish_test-vm"  # 👈 Specify the VM name here

# =======================================================
# Azure Setup
# =======================================================
try:
    print("🔑 Authenticating to Azure...")
    azure_cred = DefaultAzureCredential()
    azure_compute = ComputeManagementClient(azure_cred, AZURE_SUBSCRIPTION_ID)
    print("✅ Connected to Azure successfully.")
except Exception as e:
    print(f"⚠️ Azure connection failed: {e}")
    azure_compute = None

# =======================================================
# Azure Helpers
# =======================================================
def find_vm_by_name(vm_name):
    """Find the VM and return its object and resource group."""
    vms = azure_compute.virtual_machines.list_all()
    for vm in vms:
        if vm.name.lower() == vm_name.lower():
            rg = vm.id.split("/")[4]
            return vm, rg
    return None, None

def check_vm_status(vm_name):
    """Check and optionally manage the specified Azure VM."""
    print(f"\n🔍 Searching for VM: {vm_name} ...")
    vm, rg = find_vm_by_name(vm_name)

    if not vm:
        print(f"❌ VM '{vm_name}' not found in the subscription.")
        return

    try:
        # ✅ Fetch the instance view
        instance_view = azure_compute.virtual_machines.instance_view(
            resource_group_name=rg, vm_name=vm_name
        )
        statuses = [s.display_status for s in instance_view.statuses if s.code.startswith("PowerState/")]
        power_state = statuses[0] if statuses else "Unknown"

        print(f"🖥️ VM: {vm_name} | Resource Group: {rg} | Status: {power_state}")

        # Optionally stop if running
        if "running" in power_state.lower():
            print(f"🛑 Stopping Azure VM: {vm_name} ...")
            azure_compute.virtual_machines.begin_power_off(rg, vm_name)
            print("✅ Stop command sent successfully.")
        else:
            print(f"⚙️ VM '{vm_name}' is not running. No action needed.")

    except Exception as e:
        print(f"⚠️ Failed to check or manage VM '{vm_name}': {e}")

# =======================================================
# MAIN WORKFLOW
# =======================================================
def main():
    print("=" * 70)
    print(f"☁️ Azure Auto Manager Started at {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    if azure_compute:
        check_vm_status(TARGET_VM_NAME)
    else:
        print("❌ Azure connection not established.")

    print("\n✅ Azure VM management completed successfully.")

# =======================================================
# Entry Point
# =======================================================
if __name__ == "__main__":
    main()
