# hibou
Projet Hibou

## Deps
 python3-gstreamer1

| ANT | working? | Comments         |
|-----|----------|------------------|
| 0   | ✅️       | Background noise |
| 1   | ✅️       | Background noise |

| HCAN | working? | IP             | Subnet mask   | PORT | Comments             |
|------|----------|----------------|---------------|------|----------------------|
| 0    | ✅️       | 192.168.250.12 | 255.255.255.0 | 5001 | USB connector broken |
| 1    | ✅        | 192.168.250.11 | 255.255.255.0 | 5004 |                      |


## How to add an ip

sudo ip addr add 192.168.250.79/24 dev enp3s0