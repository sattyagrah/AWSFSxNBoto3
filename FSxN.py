import boto3
import time


# region
region = 'ap-southeast-2'

# Initialize the FSx client
fsx_client = boto3.client('fsx', region_name=region) 

# Initialize the EC2 Client
ec2_client = boto3.client('ec2', region_name=region)

# Initialize the SSM Client
ssm_client = boto3.client('ssm', region_name=region)

# Get user choice (helper function)
def get_user_choice(prompt, valid_options):
    """Helper function to get and validate user input from a list of options"""
    while True:
        print(f"\n{prompt}")
        print(f"Options: {', '.join(valid_options)}")
        choice = input(f"Enter your choice:\t".strip().lower()) # Case-insensitive input
        if choice in [opt for opt in valid_options]: #[opt.lower()
            return choice.upper() if choice in ['yes', 'no'] else choice #choice.upper()
        print(f"Invalid choice. Please select one of: {', '.join(valid_options)}")

# Get user choice (main function)
def get_fsx_inputs():
    """Collect FSx inputs from user and set them to variables"""
    # Define valid options
    deployment_types = ["MULTI_AZ_1", "SINGLE_AZ_1", "SINGLE_AZ_2", "MULTI_AZ_2"]
    snapmirror_choice = ["yes", "no"]
    snapmirror_types = ["src", "dest"]

    # set variables directly from user input
    deployment_type = get_user_choice("Deployment type:", deployment_types)
    snapmirror = get_user_choice("Snapmirror:", snapmirror_choice)

    # conditionally set snapmirror type
    snapmirror_type = None
    if snapmirror == "YES":
        snapmirror_type = get_user_choice("Snapmirror type:", snapmirror_types)

    return deployment_type.upper(), snapmirror.lower(), f"{snapmirror_type}" if (snapmirror_type == None) else f"{snapmirror_type}".lower()


# Get Security group
def get_security_group(sg_name):
    # print(f"Fetching Security group {sg_name}...")
    response = ec2_client.describe_security_groups(
        Filters = [{'Name': 'group-name', 'Values': [sg_name]}]
    )
    
    if not response['SecurityGroups']:
        raise Exception(f"No security group found with name: {sg_name}") 
    
    security_group = response['SecurityGroups'][0]['GroupId']
    # print(f"Found security group: {security_group}")
    return security_group

# Get default VPC
def get_default_vpc():
    # print(f"Fetching default VPC...")
    response = ec2_client.describe_vpcs(
        Filters=[{
            'Name': 'is-default',
            'Values':['true']
        }]
    )

    if not response['Vpcs']:
        print(f"No default VPC found in this region")
        return None
    
    default_vpc = response['Vpcs'][0]['VpcId']
    # print(f"Default VPC found: {default_vpc}")
    return default_vpc

# Get subnets in default VPC
def get_subnets(vpc_id):
    # print(f"Fetching subnets in {vpc_id}...")
    response = ec2_client.describe_subnets(
        Filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}]
    )

    if not response['Subnets']:
        raise Exception(f"No subnets found in the VPC: {vpc_id}")
    
    subnets = []
    for subnet in response['Subnets']:
        subnets.append(subnet['SubnetId'])

        # if len(subnets) == 2:
        #     break
    # print(f"Subnets are: {subnets}")
    return subnets

# Get AMI Id through SSM parameter
def get_ami(parameter_name):
    # print(f"Fetching AMI ID from SSM parameter: {parameter_name}...")
    response = ssm_client.get_parameter(Name = parameter_name)
    ami_id = response['Parameter']['Value']

    # print(f"AMI ID: {ami_id}")
    return ami_id

# Variables
storage_capacity = 2048 # FSx ONTAP storage capacity in GiB.
subnet_ids = get_subnets(get_default_vpc())
svm_name = 'svm'
volume_size = 1024 # Volume size in GiB
volume_name = 'data'
admin_password = 'asdf4321'
instance_type = 't3.medium'
image_id = get_ami(f"/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.12-x86_64")
deployment_type, snapmirror, snapmirror_type = get_fsx_inputs()

# Create file system
def create_file_system():
    print(f"Creating FSx file system: {snapmirror_type}" if snapmirror == 'yes' else f"Creating FSx file system: {deployment_type}_{region}")
    if (deployment_type == 'MULTI_AZ_1' or deployment_type == 'SINGLE_AZ_1'):
        throughput_capacity = 128 # [128, 256, 512, 1024, 2048, 4096]
    else:
        throughput_capacity = 384 # [384, 768, 1536, 3072, 6144]

    if (deployment_type == 'SINGLE_AZ_1' or deployment_type == 'SINGLE_AZ_2'):
        response = fsx_client.create_file_system(
            FileSystemType = 'ONTAP',
            StorageCapacity = storage_capacity,
            SubnetIds = subnet_ids[:1],
            SecurityGroupIds = [get_security_group(f"FSx")],
            OntapConfiguration={
                'AutomaticBackupRetentionDays' : 0,
                'DeploymentType' : deployment_type,
                'FsxAdminPassword' : admin_password,
                'ThroughputCapacity' : throughput_capacity
            },
            Tags = [{'Key': 'Name', 'Value': f"{snapmirror_type}" if snapmirror == 'yes' else f"{deployment_type}_{region}"}]
        )

    else:
        response = fsx_client.create_file_system(
            FileSystemType = 'ONTAP',
            StorageCapacity = storage_capacity,
            SubnetIds = subnet_ids[:2],
            SecurityGroupIds = [get_security_group(f"FSx")],
            OntapConfiguration={
                'AutomaticBackupRetentionDays' : 0,
                'DeploymentType' : deployment_type,
                'FsxAdminPassword' : admin_password,
                'ThroughputCapacity' : throughput_capacity,
                'PreferredSubnetId' : f"{subnet_ids[0]}"
            },
            Tags = [{'Key': 'Name', 'Value': f"{snapmirror_type}" if snapmirror == 'yes' else f"{deployment_type}_{region}"}]            
        )
        
    file_system_id = response['FileSystem']['FileSystemId']
    print(f"File system creation initiated: {file_system_id}")
    return file_system_id

# Wait for file system to become available
def wait_for_file_system(file_system_id):
    print(f"Waiting for file system {file_system_id} to become available...")
    while True:
        response = fsx_client.describe_file_systems(FileSystemIds=[file_system_id])
        status = response['FileSystems'][0]['Lifecycle']
        if status == 'AVAILABLE':
            print(f"File system {file_system_id} is now available.")
            break
        elif status in ['FAILED', 'DELETING']:
            raise Exception(f"File system creation failed with status: {status}")
        time.sleep(30)

# Create storage virtual machine
def create_svm(file_system_id):
    print(f"Creating SVM: {svm_name}_{snapmirror_type}" if snapmirror == 'yes' else f"Creating SVM: {svm_name}")
    response = fsx_client.create_storage_virtual_machine(
        FileSystemId = file_system_id,
        Name = f"{svm_name}_{snapmirror_type}" if snapmirror == 'yes' else f"{svm_name}",
        RootVolumeSecurityStyle = 'UNIX',
    )
    svm_id = response['StorageVirtualMachine']['StorageVirtualMachineId']
    print(f"SVM creation initiated: {svm_id}")
    return svm_id

# Wait for SVM to become available
def wait_for_svm(svm_id):
    print(f"Waiting for {svm_id} to become available...")
    while True:
        response = fsx_client.describe_storage_virtual_machines(StorageVirtualMachineIds=[svm_id])
        status = response['StorageVirtualMachines'][0]['Lifecycle']
        if status == 'CREATED':
            print(f"SVM {svm_id} is now active")
            break
        elif status in ['FAILED', 'DELETING']:
            raise Exception(f"SVM creation failed with status: {status}")
        time.sleep(15)

# Create volume
def create_volume(svm_id):
    print(f"Creating data volume {volume_name}_{snapmirror_type}..." if snapmirror == 'yes' else f"Creating data volume {volume_name}...")
    
    if (snapmirror == 'yes' and snapmirror_type == 'dest'):
        response = fsx_client.create_volume(
            Name = f"{volume_name}_{snapmirror_type}" if snapmirror == 'yes' else f"{volume_name}",
            VolumeType = 'ONTAP',
            OntapConfiguration = {        
                'SizeInMegabytes': volume_size*1024,
                'StorageVirtualMachineId': svm_id,
                'TieringPolicy' : {
                    'Name': 'ALL'
                },
                'OntapVolumeType': 'DP',
            }
        )
    else:
        response = fsx_client.create_volume(
            Name = f"{volume_name}_{snapmirror_type}" if snapmirror == 'yes' else f"{volume_name}",
            VolumeType = 'ONTAP',
            OntapConfiguration = {        
                'SizeInMegabytes': volume_size*1024,
                'StorageVirtualMachineId': svm_id,
                'JunctionPath': f"/{volume_name}_{snapmirror_type}" if snapmirror == 'yes' else f"/{volume_name}",
                'SecurityStyle': 'UNIX',
                'StorageEfficiencyEnabled': True,
                'TieringPolicy' : {
                    'Name': 'ALL'
                },
                'OntapVolumeType': 'RW',
                'SnapshotPolicy': 'none'
            }
        )
    volume_id = response['Volume']['VolumeId']
    print(f"Volume creation initiated: {volume_id}")
    return volume_id

# Wait for volume to become available
def wait_for_volume(volume_id):
    print(f"Waiting for volume {volume_id} to become available...")
    while True:
        response = fsx_client.describe_volumes(VolumeIds=[volume_id])
        status = response['Volumes'][0]['Lifecycle']
        if status == 'CREATED':
            print(f"Volume {volume_id} is now available")
            break
        elif status in ['FAILED', 'DELETING']:
            raise Exception(f"Volume creation failed with sttaus: {status}")
        time.sleep(15)


# Create EC2 instance
def create_ec2():
    print(f"Creating EC2 instance...")
    response = ec2_client.run_instances(
        ImageId = image_id,
        InstanceType = instance_type,
        KeyName = region,
        SubnetId = subnet_ids[0],
        MaxCount = 1,
        MinCount = 1,
        SecurityGroupIds = [get_security_group(f"SGFor-{region}")],
        TagSpecifications = [{
            'ResourceType': 'instance',
            'Tags':[{'Key': 'Name', 'Value': f"{snapmirror_type}" if snapmirror == 'yes' else f"{deployment_type}_client_{region}"}]
        }]
    )

    instance_id = response['Instances'][0]['InstanceId']
    print(f"EC2 Instance launched: {instance_id}")
    return instance_id


def main():
    try:
        file_system_id = create_file_system()
        wait_for_file_system(file_system_id)

        svm_id = create_svm(file_system_id)
        wait_for_svm(svm_id)

        volume_id = create_volume(svm_id)
        wait_for_volume(volume_id)

        instance_id = create_ec2()
        

        print(f"All resource created successfully!")
        print(f"File System ID: {file_system_id}")
        print(f"SVM ID: {svm_id}")
        print(f"Volume ID: {volume_id}")
        print(f"EC2 instance ID: {instance_id}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()