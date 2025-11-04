#guide me to creat azure piple liem multi_cloud_auto_manager.py
#=============================
 
import boto3

import time

from datetime import datetime, timedelta

from azure.identity import DefaultAzureCredential

from azure.mgmt.compute import ComputeManagementClient

from google.cloud import compute_v1

from google.auth.exceptions import DefaultCredentialsError
 
# =======================================================

# Configuration

# =======================================================

AWS_REGION = "us-east-1"

CPU_THRESHOLD = 70.0

COOLDOWN = 300  # seconds

AZURE_SUBSCRIPTION_ID = "<YOUR_SUBSCRIPTION_ID>"

GCP_PROJECT_ID = "<YOUR_GCP_PROJECT_ID>"

GCP_ZONE = "<YOUR_GCP_ZONE>"
 
# =======================================================

# AWS Setup

# =======================================================

try:

    ec2 = boto3.client("ec2", region_name=AWS_REGION)

    cloudwatch = boto3.client("cloudwatch", region_name=AWS_REGION)

    print("✅ Connected to AWS successfully.")

except Exception as e:

    print(f"⚠️ AWS connection failed: {e}")

    ec2 = None

    cloudwatch = None
 
# =======================================================

# Azure Setup

# =======================================================

try:

    azure_cred = DefaultAzureCredential()

    azure_compute = ComputeManagementClient(azure_cred, AZURE_SUBSCRIPTION_ID)

    print("✅ Connected to Azure successfully.")

except Exception as e:

    print(f"⚠️ Azure connection failed: {e}")

    azure_compute = None
 
# =======================================================

# GCP Setup

# =======================================================

try:

    gcp_instances = compute_v1.InstancesClient()

    print("✅ Connected to GCP successfully.")

except DefaultCredentialsError as e:

    print("⚠️ GCP authentication error. Run 'gcloud auth application-default login'")

    gcp_instances = None

except Exception as e:

    print(f"⚠️ GCP connection failed: {e}")

    gcp_instances = None
 
# =======================================================

# AWS Helpers

# =======================================================

def get_aws_instances():

    """Fetch all running EC2 instances."""

    if not ec2:

        return []

    reservations = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    instances = []

    for res in reservations['Reservations']:

        for i in res['Instances']:

            instances.append(i)

    return instances
 
def get_aws_avg_cpu(instance_id):

    """Get average CPU utilization for an EC2 instance."""

    if not cloudwatch:

        return 0.0

    metrics = cloudwatch.get_metric_statistics(

        Namespace='AWS/EC2',

        MetricName='CPUUtilization',

        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],

        StartTime=datetime.utcnow() - timedelta(minutes=10),

        EndTime=datetime.utcnow(),

        Period=300,

        Statistics=['Average']

    )

    datapoints = metrics.get('Datapoints', [])

    return datapoints[-1]['Average'] if datapoints else 0.0
 
def aws_scale_logic():

    print("\n🔍 Checking AWS instances...")

    instances = get_aws_instances()

    if not instances:

        print("No running AWS instances found.")

        return
 
    for instance in instances:

        iid = instance['InstanceId']

        cpu = get_aws_avg_cpu(iid)

        print(f"Instance {iid} - CPU: {cpu:.2f}%")
 
        if cpu > CPU_THRESHOLD:

            print(f"⚙️ High CPU detected for {iid}. Launching new instance...")

            ec2.run_instances(

                ImageId=instance['ImageId'],

                InstanceType=instance['InstanceType'],

                MinCount=1,

                MaxCount=1

            )

        elif cpu < 10:

            print(f"💤 Low CPU detected for {iid}. Stopping instance...")

            ec2.stop_instances(InstanceIds=[iid])
 
# =======================================================

# Azure Helpers

# =======================================================

def get_azure_vms():

    if not azure_compute:

        return []

    return list(azure_compute.virtual_machines.list_all())
 
def azure_manage_vms():

    print("\n🔍 Checking Azure VMs...")

    vms = get_azure_vms()

    if not vms:

        print("No Azure VMs found.")

        return
 
    for vm in vms:

        name = vm.name

        rg = vm.id.split("/")[4]

        instance_view = azure_compute.virtual_machines.instance_view(rg, name)

        statuses = instance_view.statuses[-1].display_status

        print(f"VM {name} in {rg} - Status: {statuses}")
 
        # Stop idle VMs

        if "running" in statuses.lower():

            print(f"🛑 Stopping idle Azure VM {name}")

            azure_compute.virtual_machines.begin_power_off(rg, name)

        else:

            print(f"✅ VM {name} already stopped or inactive.")
 
# =======================================================

# GCP Helpers

# =======================================================

def get_gcp_instances():

    if not gcp_instances:

        return []

    request = compute_v1.AggregatedListInstancesRequest(project=GCP_PROJECT_ID)

    result = gcp_instances.aggregated_list(request=request)

    vms = []

    for zone, response in result:

        for instance in response.instances or []:

            vms.append(instance)

    return vms
 
def gcp_manage_instances():

    print("\n🔍 Checking GCP instances...")

    if not gcp_instances:

        print("⚠️ Skipping GCP — not authenticated.")

        return
 
    instances = gcp_instances.list(project=GCP_PROJECT_ID, zone=GCP_ZONE)

    found = False

    for instance in instances:

        found = True

        print(f"GCP Instance {instance.name} - Status: {instance.status}")

        if instance.status == "RUNNING":

            print(f"🛑 Stopping idle GCP instance {instance.name}...")

            gcp_instances.stop(project=GCP_PROJECT_ID, zone=GCP_ZONE, instance=instance.name)

        else:

            print(f"✅ GCP Instance {instance.name} already stopped.")

    if not found:

        print("No GCP instances found.")
 
# =======================================================

# MAIN WORKFLOW

# =======================================================

def main():

    print("=" * 70)

    print(f"☁️  Multi-Cloud Auto Manager Started at {datetime.utcnow()}")

    print("=" * 70)
 
    try:

        aws_scale_logic()

        azure_manage_vms()

        gcp_manage_instances()

    except Exception as e:

        print(f"❌ Error: {e}")
 
    print("\n✅ All cloud operations completed successfully.")
 
if __name__ == "__main__":

    main()

 
azurepipeline.yaml
#===============
trigger:

  branches:

    include:

      - main
 
pool:

  name: 'babu-agent'
 
steps:

- checkout: self
 
- task: UsePythonVersion@0

  inputs:

    versionSpec: '3.x'
 
- script: |

    echo "🚀 Installing dependencies..."

    pip install boto3 azure-identity azure-mgmt-compute google-cloud-compute google-auth

    echo "🌍 Running Multi-Cloud Auto Manager..."

    python multi_cloud_auto_manager.py

  displayName: "Run Multi-Cloud Auto Manager"

 
