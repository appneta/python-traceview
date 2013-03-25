# Running the unit tests

## memcache

### setup\_test\_env.sh

Run this first.  This will create a new virtualenv and install all the prereqs for the memcache tests.

### run\_memcache\_tests.sh

This wraps test\_memcache.py, starting and stopping a memcached server so that you don't have to.  `./run_memcache_tests.sh -v` for more detail.
