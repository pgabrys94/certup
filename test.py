import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
ssh.connect("172.17.191.169", 22, "root", input("Password"))

sftp = ssh.open_sftp()
test = sftp.stat("/root/certup")
print(test, type(test))