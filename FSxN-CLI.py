import argparse
import boto3
import time
import logging


# Set the log level in the basic configuration.  This means we will capture all our log entries and not just those at Warning or above.
logging.basicConfig(
    filename='FSxN-CLI.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# define function for CLIs
def parse_args():
    parser = argparse.ArgumentParser(
        description='FSx ONTAP and EC2 Resource Creation Script',
        prog='FSxN-CLI'
    )

    # Define throughput capacity based on deployment type
    valid_throughput_gen1 = [128, 256, 512, 1024, 2048, 4096]
    valid_throughput_gen2 = [384, 768, 1536, 3072, 6144]
    
    # Required arguments
    parser.add_argument(
        '-r', 
        '--region', 
        type=str, 
        default='ap-southeast-2',
        nargs='?',
        help='AWS region (default: ap-southeast-2)'
    )

    parser.add_argument(
        '-k', 
        '--key-pair', 
        type=str,
        required=True, 
        nargs='?',
        help='Key pair name (defaults to region value)'
    ) 

    parser.add_argument(
        '-sg', 
        '--security-group', 
        type=str,
        required=True, 
        nargs='?',
        help='Security group name (default: default)'
    )   

    parser.add_argument(
        '-sc', 
        '--storage-capacity', 
        type=int, 
        default=2048,
        nargs='?',
        help='FSx ONTAP storage capacity in GiB (default: 2048)'
    )
    
    parser.add_argument(
        '-sn', 
        '--svm-name', 
        type=str, 
        default='svm',
        nargs='?',
        help='Storage Virtual Machine name (default: svm)'
    )
    
    parser.add_argument(
        '-vs', 
        '--volume-size', 
        type=int, 
        default=1024,
        nargs='?',
        help='Volume size in GiB (default: 1024)'
    )
    
    parser.add_argument(
        '-vn', 
        '--volume-name', 
        type=str, 
        default='data',
        nargs='?',
        help='Volume name (default: data)'
    )
    
    parser.add_argument(
        '-ap', 
        '--admin-password', 
        type=str, 
        default='asdf4321',
        nargs='?',
        help='Admin password for FSx (default: asdf4321)'
    )
    
    parser.add_argument(
        '-it', 
        '--instance-type', 
        type=str, 
        default='t3.medium',
        nargs='?',
        help='EC2 instance type (default: t3.medium)'
    )
    
    parser.add_argument(
        '-dt', 
        '--deployment-type', 
        type=str, 
        choices=['MULTI_AZ_1', 'SINGLE_AZ_1', 'SINGLE_AZ_2', 'MULTI_AZ_2'],
        help='FSx deployment type (default: MULTI_AZ_1)', 
        default='MULTI_AZ_1',
        nargs='?'
    )
    
    parser.add_argument(
        '-s', 
        '--snapmirror', 
        type=str, 
        choices=['yes', 'no'],
        help='Enable or disable snapmirror (default: Disabled)', 
        default='no',
        nargs='?'
    )
    
    parser.add_argument(
        '-st', 
        '--snapmirror-type', 
        type=str, 
        choices=['src', 'dest'],
        help='Snapmirror type (required if snapmirror is yes)'
    )
    
    parser.add_argument(
        '-tc', 
        '--throughput-capacity', 
        type=int,
        nargs='?',
        help=f'''Throughput capacity in MB/s. 
        For MULTI_AZ_1/SINGLE_AZ_1: {valid_throughput_gen1} (default: 128)
        For MULTI_AZ_2/SINGLE_AZ_2: {valid_throughput_gen2} (default: 384)'''
    )
    
    args = parser.parse_args()

    # Validate snapmirror-type requirement
    if args.snapmirror.lower() == 'yes' and not args.snapmirror_type:
        parser.error("--snapmirror-type is required when --snapmirror is set to 'yes'")

    # Set key-pair default value to region if not specified
    if args.key_pair is None:
        args.key_pair = args.region

    # Set security group default value to default if not specified
    if args.security_group is None:
        args.security_group = 'default'

    # Validate throughput capacity based on deployment type
    if args.deployment_type in ['MULTI_AZ_1', 'SINGLE_AZ_1']:
        if args.throughput_capacity is None:
            args.throughput_capacity = 128 # Default value for 1st gen.
        elif args.throughput_capacity not in valid_throughput_gen1:
            parser.error(f" For {args.deployment_type}, throughput capacity must be one of: {valid_throughput_gen1}")

    else: # For second generation
        if args.throughput_capacity is None:
            args.throughput_capacity = 384 # Default value for 2nd gen.
        elif args.throughput_capacity not in valid_throughput_gen2:
            parser.error(f" For {args.deployment_type}, throughput capacity must be one of: {valid_throughput_gen2}")        
    
    return args

def get_fsx_inputs(args):
    """Process FSx inputs from command line arguments"""
    deployment_type = args.deployment_type.upper()
    snapmirror = args.snapmirror.lower()
    snapmirror_type = args.snapmirror_type.lower() if args.snapmirror_type else None
    
    return deployment_type, snapmirror, snapmirror_type

# Get Security group
def get_security_group(sg_name):
    response = ec2_client.describe_security_groups(
        Filters = [{'Name': 'group-name', 'Values': [sg_name]}]
    )
    
    if not response['SecurityGroups']:
        logging.error(f"No security group found with name: {sg_name}")
        raise Exception(f"No security group found with name: {sg_name}") 
    
    security_group = response['SecurityGroups'][0]['GroupId']
    return security_group

# Get default VPC
def get_default_vpc():
    response = ec2_client.describe_vpcs(
        Filters=[{
            'Name': 'is-default',
            'Values':['true']
        }]
    )

    if not response['Vpcs']:
        logging.error(f"No default VPC found in this region")
        return None
    
    default_vpc = response['Vpcs'][0]['VpcId']
    return default_vpc

# Get subnets in default VPC
def get_subnets(vpc_id):
    response = ec2_client.describe_subnets(
        Filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}]
    )

    if not response['Subnets']:
        logging.error(f"No subnets found in the VPC: {vpc_id}")
        raise Exception(f"No subnets found in the VPC: {vpc_id}")
    
    subnets = []
    for subnet in response['Subnets']:
        subnets.append(subnet['SubnetId'])
    return subnets

# Get AMI Id through SSM parameter
def get_ami(parameter_name):
    response = ssm_client.get_parameter(Name = parameter_name)
    ami_id = response['Parameter']['Value']
    return ami_id

# Create file system
def create_file_system():
    logging.info(f"Creating FSx file system: {snapmirror_type}..." if snapmirror == 'yes' else f"Creating FSx file system: {deployment_type}_{region}...")
    if deployment_type in ['SINGLE_AZ_1', 'SINGLE_AZ_2']:
        response = fsx_client.create_file_system(
            FileSystemType = 'ONTAP',
            StorageCapacity = storage_capacity,
            SubnetIds = subnet_ids[:1],
            SecurityGroupIds = [get_security_group(security_group)], # SG needs to be changed as per your use case.
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
            SecurityGroupIds = [get_security_group(security_group)], # SG needs to be changed as per your use case.
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
    logging.info(f"File system creation initiated: {file_system_id}")
    return file_system_id

# Wait for file system to become available
def wait_for_file_system(file_system_id):
    logging.info(f"Waiting for file system {file_system_id} to become available...")
    while True:
        response = fsx_client.describe_file_systems(FileSystemIds=[file_system_id])
        status = response['FileSystems'][0]['Lifecycle']
        if status == 'AVAILABLE':
            logging.info(f"File system {file_system_id} is now available.")
            break
        elif status in ['FAILED', 'DELETING']:
            logging.error(f"File system creation failed with status: {status}")
            raise Exception(f"File system creation failed with status: {status}")
        time.sleep(30)

# Create storage virtual machine
def create_svm(file_system_id):
    logging.info(f"Creating SVM: {svm_name}_{snapmirror_type}..." if snapmirror == 'yes' else f"Creating SVM: {svm_name}...")
    response = fsx_client.create_storage_virtual_machine(
        FileSystemId = file_system_id,
        Name = f"{svm_name}_{snapmirror_type}" if snapmirror == 'yes' else f"{svm_name}",
        RootVolumeSecurityStyle = 'UNIX',
    )
    svm_id = response['StorageVirtualMachine']['StorageVirtualMachineId']
    logging.info(f"SVM creation initiated: {svm_id}")
    return svm_id

# Wait for SVM to become available
def wait_for_svm(svm_id):
    logging.info(f"Waiting for {svm_id} to become available...")
    while True:
        response = fsx_client.describe_storage_virtual_machines(StorageVirtualMachineIds=[svm_id])
        status = response['StorageVirtualMachines'][0]['Lifecycle']
        if status == 'CREATED':
            logging.info(f"SVM {svm_id} is now active")
            break
        elif status in ['FAILED', 'DELETING']:
            logging.error(f"SVM creation failed with status: {status}")
            raise Exception(f"SVM creation failed with status: {status}")
        time.sleep(15)

# Create volume
def create_volume(svm_id):
    logging.info(f"Creating data volume {volume_name}_{snapmirror_type}..." if snapmirror == 'yes' else f"Creating data volume {volume_name}...")
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
    logging.info(f"Volume creation initiated: {volume_id}")
    return volume_id

# Wait for volume to become available
def wait_for_volume(volume_id):
    logging.info(f"Waiting for volume {volume_id} to become available...")
    while True:
        response = fsx_client.describe_volumes(VolumeIds=[volume_id])
        status = response['Volumes'][0]['Lifecycle']
        if status == 'CREATED':
            logging.info(f"Volume {volume_id} is now available")
            break
        elif status in ['FAILED', 'DELETING']:
            logging.error(f"Volume creation failed with status: {status}")
            raise Exception(f"Volume creation failed with status: {status}")
        time.sleep(15)

# Create EC2 instance
def create_ec2():
    logging.info(f"Creating EC2 instance...")
    response = ec2_client.run_instances(
        ImageId = image_id,
        InstanceType = instance_type,
        KeyName = key_pair,
        SubnetId = subnet_ids[0],
        MaxCount = 1,
        MinCount = 1,
        SecurityGroupIds = [get_security_group(security_group)], # SG needs to be changed as per your use case.
        TagSpecifications = [{
            'ResourceType': 'instance',
            'Tags':[{'Key': 'Name', 'Value': f"{snapmirror_type}" if snapmirror == 'yes' else f"{deployment_type}_client_{region}"}]
        }]
    )

    instance_id = response['Instances'][0]['InstanceId']
    logging.info(f"EC2 Instance launched: {instance_id}")
    return instance_id

def main():
    # Parse command line arguments
    args = parse_args()
    
    # Initialize clients with region from args
    global region
    region = args.region

    global fsx_client, ec2_client, ssm_client
    fsx_client = boto3.client('fsx', region_name=region)
    ec2_client = boto3.client('ec2', region_name=region)
    ssm_client = boto3.client('ssm', region_name=region)
    
    # Use the parsed arguments in your existing variables
    global storage_capacity, svm_name, volume_size, volume_name, admin_password, instance_type, throughput_capacity, key_pair, security_group
    storage_capacity = args.storage_capacity
    svm_name = args.svm_name
    volume_size = args.volume_size
    volume_name = args.volume_name
    admin_password = args.admin_password
    instance_type = args.instance_type
    throughput_capacity = args.throughput_capacity
    key_pair = args.key_pair
    security_group = args.security_group
    
    # Get other required variables
    global subnet_ids, image_id, deployment_type, snapmirror, snapmirror_type
    subnet_ids = get_subnets(get_default_vpc())
    image_id = get_ami(f"/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.12-x86_64")
    deployment_type, snapmirror, snapmirror_type = get_fsx_inputs(args)

    try:
        file_system_id = create_file_system()
        wait_for_file_system(file_system_id)

        svm_id = create_svm(file_system_id)
        wait_for_svm(svm_id)

        volume_id = create_volume(svm_id)
        wait_for_volume(volume_id)

        instance_id = create_ec2()
    
        print(f"All resource created successfully!")
        logging.debug(f"File System ID: {file_system_id}")
        logging.debug(f"SVM ID: {svm_id}")
        logging.debug(f"Volume ID: {volume_id}")
        logging.debug(f"EC2 instance ID: {instance_id}")
        
    except Exception as e:
        logging.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()