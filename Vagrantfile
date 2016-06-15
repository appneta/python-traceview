#
# This Vagrantfile builds a dev box with all the parts needed for testing
#
$script = <<-BASH
# Add Mongo repo
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list

# Update and upgrade
sudo apt-get -y update
sudo apt-get -y upgrade

# Install basics
# export DEBIAN_FRONTEND=noninteractive # Needed to skip mysql password prompt

echo mysql-server mysql-server/root_password select | sudo debconf-set-selections
echo mysql-server mysql-server/root_password_again select | sudo debconf-set-selections

sudo DEBIAN_FRONTEND=noninteractive apt-get -y install \
  build-essential swig git software-properties-common \
  python-dev python-pip python-tox python-software-properties \
  libmysqlclient-dev libmemcached-dev libpq-dev libkrb5-dev \
  mongodb-org mysql-server-5.6 postgresql postgresql-contrib \
  memcached redis-server

# Grant password-less access to postgres, for test suite
echo "local all all  trust" | sudo tee /etc/postgresql/9.3/main/pg_hba.conf
echo "host all all 127.0.0.1/32 trust" | sudo tee -a /etc/postgresql/9.3/main/pg_hba.conf
sudo service postgresql restart

# Tracelyzer
wget https://files.appneta.com/install_appneta.sh
sudo sh ./install_appneta.sh f08da708-7f1c-4935-ae2e-122caf1ebe31

# Old python
sudo add-apt-repository ppa:fkrull/deadsnakes
sudo apt-get -y update
sudo apt-get -y install python2.6 python2.6-dev
BASH

Vagrant.configure(2) do |config|
  config.vm.box = 'ubuntu/trusty64'

  config.vm.network 'private_network', type: 'dhcp'
  config.vm.synced_folder '.', '/vagrant', id: 'core', nfs: true

  config.vm.provision 'shell', privileged: false, inline: $script

  # Virtualbox VM
  config.vm.provider :virtualbox do |provider|
    # Cap cpu and memory usage
    provider.customize [
      'modifyvm', :id,
      '--memory', 4096,
      '--cpuexecutioncap', 75
    ]

    # Enable symlink support
    provider.customize [
      'setextradata', :id,
      'VBoxInternal2/SharedFoldersEnableSymlinksCreate/v-root', '1'
    ]
  end
end
