mkdir -p ~/venv
virtualenv ~/venv/oboeware-test
source ~/venv/oboeware-test/bin/activate

wget ftp://ftp.tummy.com/pub/python-memcached/python-memcached-latest.tar.gz
tar xzf python-memcached-latest.tar.gz
rm python-memcached-latest.tar.gz
cd python-memcached-1.48
python setup.py install
cd ..
rm -rf python-memcached-1.48

pip install -r requirements.txt
