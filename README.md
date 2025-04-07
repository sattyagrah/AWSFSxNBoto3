## Create FSxN ONTAP file system along with SVM and data volume in AWS cloud. 

> [!NOTE]
> 
> - Only to be used in AWS CLOUD.
> 
> - Please install **python** and **pip** in your local machine before using this python file. 

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

### How to use (python):

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

