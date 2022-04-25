from netmiko import ConnectHandler
from datetime import datetime
import sys,time,getpass,argparse,socket

# Set the base device dictionary for ConnectHandler kwargs
device = {
    "device_type":"cisco_ios",
    "host":"",
    "username":"",
    "password":"",
}

# Parse CLI arguments (nargs='+' imports the arg as a list. Important as we want to treat file based and cli based args with the same for loop.)
parser = argparse.ArgumentParser(description="Backup multiple IOS device configs and info to file.")
parser.add_argument('--devices','-d', nargs='?', help='File containing list of devices on which to run commands. Is overridden by --device. If not specified, uses BulkBackupIOS.hosts file. Format is <ip/hostname>,<file prefix>. If no prefix is specified, <ip/hostname> is used to name the files.')
parser.add_argument('--device','-D', nargs='+', help='Name of device on which to run commands. Overrides --devices.')
parser.add_argument('--user','-u', nargs='?', help='User with which to run the command. If not specified, you will be prompted.')
parser.add_argument('--password','-p', nargs='?', help='Password with which to run the command. If not specified you will be prompted.')
args = parser.parse_args()

# Check if you have the args you need and, if not, get them. Used to populate the device dictionary above.
if args.user:
    device["username"] = args.user
else:
    device["username"] = input("User: ")

if args.password:
    device["password"] = args.password
else:
    device["password"] = getpass.getpass()

# Populate the hosts variable.
if args.device:
    hosts = args.device
elif args.devices:
    hosts = open(args.devices)
else:
    hosts = open('./BulkBackupIOS.hosts')
   
# Set the date and time
now = datetime.now()

# Start looping throught hosts one at a time
for host in hosts:
    # Strip and split the csv data
    host = host.strip().split(',')
    device['host'] = host[0]
    desc = host[-1] # last item
    
    # Define filename
    filename = desc+now.strftime("_%Y%m%d_%H%M")

    # Use a context handler (with/as) to cleanly close ssh when done.  Passing kwargs from device dictionary.
    with ConnectHandler(**device) as ssh:
        output_config = ""   # define output, as we only append to it later
        output_info = now.strftime("Información recopilada el %d/%m/%Y, a las %H:%M:%S\n\n")
        
        # Define commands
        commands_config = ['show startup-config']
        commands_info = ['show version','show switch','show vlan','show interface status','show ip interface brief','show cdp neighbor','show cdp neighbor detail','show license all','show ap summary','show ap tag summary','show ap uptime','show redundancy','show chassis']
        
        # Execute config retreival commands
        for command in commands_config:
            output_config += ssh.send_command(command)
        
        # Execute info retreival commands
        for command in commands_info:
            temp_output = ssh.send_command(command)
            if not 'Invalid input detected' in temp_output:
                output_info += "###############################\n"
                output_info += command+"\n"
                output_info += "###############################\n\n"
                output_info += temp_output
                output_info += "\n\n\n"
            
        
        # Write files using context manager
        with open(f"./{filename}.conf",'w') as open_file:
            open_file.write(output_config)
        with open(f"./{filename}.info",'w') as open_file:
            open_file.write(output_info)
