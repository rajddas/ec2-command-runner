# ec2-command-runner
Use AWS lambda to run any command in EC2 with SSM agent installed

# `CommandRunner Release Notes`

> ## v1.0.0 (06/10/2021)
> 
> #### First Release features :
> 
> - Runs any command for a given set of instances having SSM installed.

>  ## v1.0.1 (06/14/2021)

> - Runs any command to all the instances having SSM agent installed.
> - Can be invoked from multiple cloudwatch rules.

>  ## v2.0.1 (06/22/2021)

> - sends a notification email whenever the service is inactive or failed using sns.

> 
> #### Bug Fixes:
> Not found

> ## Usage

> These are the input JSON can be sent from cloudwatch in certain intervals/onetime.

> for running different commands to different instances at once

```json
{
  "inputs": [
    {
      "InstanceIds": [
        "i-0b03ded3f5e064fbb",
        "i-0513c5e33ac0abf90"
      ],
      "Commands": [
        "#!/bin/bash",
        "echo $PATH",
        "exit 1"
      ]
    },
    {
      "InstanceIds": [
        "i-0b03ded3f5e064fbb",
        "i-0513c5e33ac0abf90"
      ],
      "Commands": [
        "echo \"Rajdeep\""
      ]
    }
  ]
}
```
> for running multiple commands to instances at once

```json
{
  "inputs": [
    {
      "InstanceIds": [
        "i-0adebd38dd364aba8"
      ],
      "Commands": [
        "#!/bin/bash",
        "sudo systemctl is-active persistwebapp.service; if [[ $? -eq 0 ]]; then echo \"Service is running\"; else sudo systemctl start persistwebapp.service; echo \"Service Started\"; fi"
      ]
    }
  ]
}
```
> for running multiple commands to all SSM enabled instances at once

```json
{
  "inputs": [
    {
      "InstanceIds": [ ],
      "Commands": [
        "#!/bin/bash",
        "status=$(pgrep exim 2>&1); if [[ -n \"$status\" ]]; then echo \"exim exists :: Trying to remove\"; sudo rpm -e --nodeps \"exim\"; else echo \"exim does not exists\"; fi"
      ]
    }
  ]
}
```

## Contributors


Rajdeep Das
