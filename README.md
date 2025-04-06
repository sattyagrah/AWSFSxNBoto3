## Python code to create FSxN ONTAP file system along with SVM and data volume in AWS cloud. 

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
> 4. This script is using 2 subnets of the default VPC of the selected region. 

### How to use:

- Download the script:

    > ```sh
    > curl https://raw.githubusercontent.com/sattyagrah/AWSFSxNBoto3/refs/heads/main/FSxN.py -o FSxN.py
    > ```

- Make modifications, if required as mentioned above. 


- Create FSxN ONTAP resources using the below command: 

    > ```sh
    > python3 FSxN.py
    > ```