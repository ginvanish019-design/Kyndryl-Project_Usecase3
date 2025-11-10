# ==============================================================
# Azure Auto Manager
# Description: Automatically manages Azure Virtual Machines
# Author: Anish Martin
# ==============================================================

from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient

# =======================================================
# Configuration
# =======================================================
AZURE_SUBSCRIPTION_ID = "c070b0a7-e56f-4350-a4bd-3c01811a284c"

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
def get_azure_vms():
    """Fetch all Azure VMs."""
    if not azure_compute:
        return []
    return list(azure_compute.virtual_machines.list_all())

def azure_manage_vms():
    """Check and manage Azure VMs."""
    print("\n🔍 Checking Azure VMs...")
    vms = get_azure_vms()
    if not vms:
        print("No Azure VMs found.")
        return

    for vm in vms:
        try:
            name = vm.name
            rg = vm.id.split("/")[4]
            # ✅ Correct syntax: fetch instance view
            instance_view = azure_compute.virtual_machines.instance_view(rg, name)
            statuses = instance_view.statuses[-1].display_status
            print(f"🖥️ VM: {name} | Resource Group: {rg} | Status: {statuses}")

            # Stop idle/running VMs
            if "running" in statuses.lower():
                print(f"🛑 Stopping Azure VM: {name}")
                azure_compute.virtual_machines.begin_power_off(rg, name)
            else:
                print(f"✅ VM {name} already stopped or inactive.")

        except Exception as e:
            print(f"⚠️ Failed to manage VM {vm.name}: {e}")

# =======================================================
# MAIN WORKFLOW
# =======================================================
def main():
    print("=" * 70)
    print(f"☁️ Azure Auto Manager Started at {datetime.utcnow()}")
    print("=" * 70)

    try:
        azure_manage_vms()
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n✅ Azure VM management completed successfully.")

# =======================================================
# Entry Point
# =======================================================
if __name__ == "__main__":
    main()
