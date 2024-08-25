# VPC

## de1vpc -> DEPRECATED ! =====> de1vpc1 (10.1.0.0/16)

### Subnetting

- 10.1.1.0/24 - de1ec2subnet- c

- 10.1.2.0/24 - de1rdssubnet - a (?)

- 10.1.3.0/24 - de1kafkasubnet - a

- 10.1.4.0/24 - de1grafanasubnet - c(...)

- 10.1.5.0/24 - de1emrsubnet- c

### RouteTable

- de1routetable1 : 10.1.0.0/16

    - 0.0.0.0/0 : de1internetgateway1

    - 10.1.0.0/16 : local

