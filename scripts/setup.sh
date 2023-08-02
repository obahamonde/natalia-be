# Update System
sudo apt-get update
sudo apt-get upgrade -y


# Install Bash Tools
sudo apt-get install -y jq
sudo apt-get install -y unzip
sudo apt-get install -y tree
sudo apt-get install -y wget
sudo apt-get install -y curl
sudo apt-get install -y net-tools
sudo apt-get install -y nmap
sudo apt-get install -y nginx

# Install Git
sudo apt-get install -y git

# Install Vim
sudo apt-get install -y vim

# Install python tools
sudo apt-get install -y python3-pip
sudo apt-get install -y python-is-python3
pip install --upgrade pip
pip install virtualenv
pip install poetry
pip install pipenv
pip install docker-compose


# Install Docker
curl -fsSL https://get.docker.com | sh

# Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash

# Install PyEnv
curl https://pyenv.run | bash


# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip 
sudo ./aws/install