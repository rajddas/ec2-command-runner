import boto3
import datetime
import logging
import json
import time
from dateutil import tz
from datetime import datetime

################################## Loading logger ###################################

def load_log_config():
    """
    # Basic config. Replace with your own logging config if required
    :return: object for basic logging
    """
    global logger

    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(format=LOG_FORMAT, datefmt=DATETIME_FORMAT)
    logger = logging.getLogger("LAMBDA_LOG")
    
    logger.setLevel(logging.DEBUG)

############################# Initializing clients ##################################

ssm = boto3.client('ssm')
ec2 = boto3.client('ec2')
sns = boto3.client('sns')
######################### Check if Instance is running ##############################

def check_running_status(instance_ids):
    '''
    Function to check which instance is running given a instance list
    which gives a list of running instances as list
    '''
    try:
        running_instance_ids = []
        logger.info('Checking is instances are running')
        if len(instance_ids):
            response = ec2.describe_instances(
                Filters=[
                    {
                        'Name': 'instance-state-name',
                        'Values': [
                            'running',
                        ]
                    },
                ],
                InstanceIds=instance_ids,
            )
        
            for r in response['Reservations']:
              for i in r['Instances']:
                running_instance_ids.append(i['InstanceId'])
        
            logger.info('Running Instance Count : ' +str(len(running_instance_ids)))
            return running_instance_ids
            
        else:
            response = ec2.describe_instances(
                Filters=[
                    {
                        'Name': 'instance-state-name',
                        'Values': [
                            'running',
                        ]
                    },
                ],
            )
            for r in response['Reservations']:
              for i in r['Instances']:
                running_instance_ids.append(i['InstanceId'])
            while "NextToken" in response:
                response = ec2.describe_instances(
                    Filters=[
                        {
                            'Name': 'instance-state-name',
                            'Values': [
                                'running',
                            ]
                        },
                    ],
                    NextToken=response["NextToken"]
                )
                for r in response['Reservations']:
                  for i in r['Instances']:
                    running_instance_ids.append(i['InstanceId'])
                
            logger.info('Running Instance Count : ' +str(len(running_instance_ids)))    
            return running_instance_ids
        
    except Exception as e:
        logger.error('Failed while getting running instances list with error :' +str(e))
        raise e

######################### Check if Instance has running SSM ##############################

def check_ssm_status(instance_ids):
    '''
    Function to check if SSM agent is running for given argument
    of running instance IDs which gives a list of instances with 
    SSM online and OS is Linux.
    '''
    try:
        ssm_enabled_instances = []
        logger.info('Checking is instances have SSM agent running')
        for each_instances_list in instance_ids:
            response = ssm.describe_instance_information(
                Filters=[
                    {
                        'Key': 'InstanceIds',
                        'Values': each_instances_list
                    },
                ],
            )
            for each in response['InstanceInformationList']:
                if (each['PingStatus']=='Online' and each['PlatformType']=='Linux'):
                    ssm_enabled_instances.append(each['InstanceId'])
                else:
                    continue
        
        logger.info('SSM enabled instances count : '+str(len(ssm_enabled_instances)))    
        return ssm_enabled_instances
        
    except Exception as e:
        logger.error('Failed while getting SSM status for instances with error :' +str(e))
        raise e
        
############################# List splitter on split count ##########################

def list_splitter(instance_ids):
    '''
    Function to split a given list into multiple list so that the SSM
    commands can be run and checked for the status within 2 seconds.
    '''
    try:
        logger.info('Splitting the list of instance IDs')
        split_count = 10
        list_length = len(instance_ids)
        if list_length >= split_count:
            splitted_instances_list = [instance_ids[i * split_count:(i + 1) * split_count] for i in range((len(instance_ids) + split_count - 1) // split_count )]
        else:
            splitted_instances_list = [instance_ids]
            
        logger.info(splitted_instances_list)
        
        return splitted_instances_list
        
    except Exception as e:
        logger.error('Failed while splitting the list with error :' +str(e))
        raise e

################################## Send Command ######################################

def run_command(instance_ids,commands):
    '''
    Function to run shell command which takes instance ID(s) list and shell command(s) 
    list as input and gives the command ID and status as output.
    '''
    try:
        logger.info('Starting to run command in instances')
        logger.info('Running commands : ')
        logger.info(commands)
        logger.info('Instance list : ')
        logger.info(instance_ids)
        
        response = ssm.send_command(
            InstanceIds=instance_ids,
            DocumentName="AWS-RunShellScript",
            TimeoutSeconds=60,
            Comment='Invoked by AEDL command runner Lambda',
            Parameters={
                'commands': commands
            },
        )
        command_id = response['Command']['CommandId']
        status = response['Command']['Status']
        logger.info('Command ID : '+command_id)
        logger.info('Command Status : '+status)
        
        return command_id,status
        
    except Exception as e:
        logger.error('Failed while invoking command to instance(s) with error :' +str(e))
        raise e

########################### Check Command Status ####################################

def get_command_details(instance_id,command_id):
    '''
    Function to get status of commands per instance ID which takes instance_id and
    command_id as input and give status and stdout/stderr.
    '''
    try:
        logger.info('Getting status for '+command_id+' on instance id : '+instance_id)
        time.sleep(2)
        response = ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        status = response['Status']
        stdout = response['StandardOutputContent']
        stderr = response['StandardErrorContent']
        
        return status, stdout, stderr
        
    except Exception as e:
        logger.error('Failed while getting status and output of command from instance with error :' +str(e))
        raise e

############################# Main lambda handler ###################################

def lambda_handler(event, context):
    '''
    Main lambda handler which gets the event from cloudwatch
    '''
    try:
        load_log_config()
        logger.info('Starting execution..')
        logger.info('Event Received from Cloudwatch :')
        logger.info(json.dumps(event))
        
        
        if "inputs" in event:
            eventbody = event['inputs']
            response_list = []    
            for each_event in eventbody:
                instance_ids = each_event['InstanceIds']
                running_instance_ids = check_running_status(instance_ids)
                logger.info('Running instances :')
                logger.info(running_instance_ids)
                splitted_running_instances_list = list_splitter(running_instance_ids)
                ssm_enabled_instances=check_ssm_status(splitted_running_instances_list)
                logger.info('SSM enabled instances :')
                logger.info(ssm_enabled_instances)
                splitted_ssm_enabled_instances_list = list_splitter(ssm_enabled_instances)
                commands = each_event['Commands']
                for each_ssm_enabled_instance_list in splitted_ssm_enabled_instances_list:
                    command_id,status = run_command(each_ssm_enabled_instance_list,commands)
                    for each_instance in each_ssm_enabled_instance_list:
                        status, stdout, stderr = get_command_details(each_instance,command_id)
                        i = 1
                        while i < 10:
                            if (status == 'Success' or status == 'Failed' or status == 'TimedOut' or status == 'Cancelled'):
                                resp = {
                                    "InstanceId": each_instance,
                                    "Status": status,
                                    "Stdout": stdout,
                                    "Stderr": stderr
                                }
                                response_list.append(resp)
                                logger.info('Output : '+json.dumps(resp))
                                break
                            else:
                                time.sleep(1)
                                status, stdout, stderr = get_command_details(each_instance,command_id)
                                i+=1
                                continue
            
            logger.info('Function execution successful.')
            return {
                "output": response_list
            }

        
    except Exception as e:
        logger.error('Function execution failed.')
        raise e
