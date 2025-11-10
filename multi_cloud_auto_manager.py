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
            instance_view = azur_
