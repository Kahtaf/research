ssh-keygen -y -P '' -f /etc/ssh/ssh_host_ed25519_key | awk '{print "SSH_PUBLIC_FIELDS=" NF,"TYPE=" $1}'
