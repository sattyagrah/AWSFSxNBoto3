## Create FSxN ONTAP file system along with SVM and data volume in AWS cloud. 

> [!NOTE]
> 
> - Only to be used in AWS CLOUD. Make sure to [download](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [configure AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) before using this script.
> 
> - Please install **python** and **pip** in your local machine before using this python file. 

### How to use (python):

> [!IMPORTANT] 
>
> 1. By default, this script will create resources in the AWS region `ap-southeast-2`.
> 
> 2. Please set the **region** variable in the script as per your use case after downloading this script.
>
> 3. This script is using custom security group for FSx and EC2 resources, please modify if as per your use case in the line [132](https://github.com/sattyagrah/AWSFSxNBoto3/blob/main/FSxN.py#L132C54-L132C57), [147](https://github.com/sattyagrah/AWSFSxNBoto3/blob/main/FSxN.py#L147C54-L147C57) and [262](https://github.com/sattyagrah/AWSFSxNBoto3/blob/main/FSxN.py#L262C50-L262C64).
>
> 4. Change the key-pair name, as per your use case in the line [258](https://github.com/sattyagrah/AWSFSxNBoto3/blob/main/FSxN.py#L258).
> 
> 5. This script is using 2 subnets of the default VPC of the selected region.

- Download the script:

    > ```sh
    > curl https://raw.githubusercontent.com/sattyagrah/AWSFSxNBoto3/refs/heads/main/FSxN.py -o FSxN.py
    > ```

- Make modifications, if required as mentioned above. 

- Create FSxN ONTAP resources using the below command: 

    > ```sh
    > python3 FSxN.py
    > ```

### Sample output:

- The script will ask for few input such as `Deployment type`, `Snapmirror` and `Snapmirror type`. Please answer it as per your choice...
    > ```md
    > # python3 FSxN.py
    > 
    > Deployment type:
    > Options: MULTI_AZ_1, SINGLE_AZ_1, SINGLE_AZ_2, MULTI_AZ_2
    > enter your choice:MULTI_AZ_1
    > 
    > Snapmirror:
    > Options: yes, no
    > enter your choice:yes
    > 
    > Snapmirror type:
    > Options: src, dest
    > enter your choice:dest
    > Creating FSx file system: dest
    > File system creation initiated: fs-00e8cc2ad8f5e2c53
    > Waiting for file system fs-00e8cc2ad8f5e2c53 to become available...
    > File system fs-00e8cc2ad8f5e2c53 is now available.
    > Creating SVM: svm_dest
    > SVM creation initiated: svm-06e9029f71894372c
    > Waiting for svm-06e9029f71894372c to become available...
    > SVM svm-06e9029f71894372c is now active
    > Creating data volume data_dest...
    > Volume creation initiated: fsvol-03d2780328d243f94
    > Waiting for volume fsvol-03d2780328d243f94 to become available...
    > Volume fsvol-03d2780328d243f94 is now available
    > Creating EC2 instance...
    > EC2 Instance launched: i-06e23c81318dd6964
    > All resource created successfully!
    > File System ID: fs-00e8cc2ad8f5e2c53
    > SVM ID: svm-06e9029f71894372c
    > Volume ID: fsvol-03d2780328d243f94
    > EC2 instance ID: i-06e23c81318dd6964
    > ```

### How to use (yaml):

1. Download the template to your local machine from GitHub repository.

    > ```bash
    > curl https://raw.githubusercontent.com/sattyagrah/AWSFSxNBoto3/refs/heads/main/FSx.yaml -o FSx.yaml
    > ```

2. Use the template to [create the stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-create-stack.html) through AWS console. 

### How to use (FSxN-CLI):

> [!IMPORTANT] 
>
> 1. By default, this script will create resources in the AWS region `ap-southeast-2`.
> 
> 2. Use the `-h` or `--help` flag to get all the options. 
>
> 3. This script will create a log file `FSxN-CLI.log` in the same directory, while this script will be downloaded.
>
> 4. **Security group** and **Key pair** is required. Pass the security group name as per your use (default: default). 
>
> 5. This script considers that a key-pair with name, same a region (E.g: us-east-1) is already present in your account.

- Download the script:

    > ```sh
    > curl https://raw.githubusercontent.com/sattyagrah/AWSFSxNBoto3/refs/heads/main/FSxN-CLI.py -o FSxN-CLI.py
    > ```

- Create FSxN ONTAP resources using the below command: 

    > ```python
    > python3 FSxN-CLI.py -k <key_pair> -sg <security_group_name>
    > ```

    - Example: 
        > ```python
        > python3 FSxN-CLI.py -k demo-key -sg demo-sg
        > ```

- Example: 

    > ```python
    > ❯ python3 FSxN-CLI.py -h
    > usage: FSxN-CLI [-h] [-r [REGION]] -k [KEY_PAIR] -sg [SECURITY_GROUP] [-sc [STORAGE_CAPACITY]] [-sn [SVM_NAME]] [-vs [VOLUME_SIZE]]
    >                 [-vn [VOLUME_NAME]] [-ap [ADMIN_PASSWORD]] [-it [INSTANCE_TYPE]]
    >                 [-dt [{MULTI_AZ_1,SINGLE_AZ_1,SINGLE_AZ_2,MULTI_AZ_2}]] [-s [{yes,no}]] [-st {src,dest}] [-tc [THROUGHPUT_CAPACITY]]
    > 
    > FSx ONTAP and EC2 Resource Creation Script
    > 
    > optional arguments:
    >   -h, --help            show this help message and exit
    >   -r [REGION], --region [REGION]
    >                         AWS region (default: ap-southeast-2)
    >   -k [KEY_PAIR], --key-pair [KEY_PAIR]
    >                         Key pair name (defaults to region value)
    >   -sg [SECURITY_GROUP], --security-group [SECURITY_GROUP]
    >                         Security group name (default: default)
    >   -sc [STORAGE_CAPACITY], --storage-capacity [STORAGE_CAPACITY]
    >                         FSx ONTAP storage capacity in GiB (default: 2048)
    >   -sn [SVM_NAME], --svm-name [SVM_NAME]
    >                         Storage Virtual Machine name (default: svm)
    >   -vs [VOLUME_SIZE], --volume-size [VOLUME_SIZE]
    >                         Volume size in GiB (default: 1024)
    >   -vn [VOLUME_NAME], --volume-name [VOLUME_NAME]
    >                         Volume name (default: data)
    >   -ap [ADMIN_PASSWORD], --admin-password [ADMIN_PASSWORD]
    >                         Admin password for FSx (default: asdf4321)
    >   -it [INSTANCE_TYPE], --instance-type [INSTANCE_TYPE]
    >                         EC2 instance type (default: t3.medium)
    >   -dt [{MULTI_AZ_1,SINGLE_AZ_1,SINGLE_AZ_2,MULTI_AZ_2}], --deployment-type [{MULTI_AZ_1,SINGLE_AZ_1,SINGLE_AZ_2,MULTI_AZ_2}]
    >                         FSx deployment type (default: MULTI_AZ_1)
    >   -s [{yes,no}], --snapmirror [{yes,no}]
    >                         Enable or disable snapmirror (default: Disabled)
    >   -st {src,dest}, --snapmirror-type {src,dest}
    >                         Snapmirror type (required if snapmirror is yes)
    >   -tc [THROUGHPUT_CAPACITY], --throughput-capacity [THROUGHPUT_CAPACITY]
    >                         Throughput capacity in MB/s. For MULTI_AZ_1/SINGLE_AZ_1: [128, 256, 512, 1024, 2048, 4096] (default: 128) For
    >                         MULTI_AZ_2/SINGLE_AZ_2: [384, 768, 1536, 3072, 6144] (default: 384)
    > ```
    ---
    > ```python
    > ❯ python3 FSxN-CLI.py -k -sg
    > ```
