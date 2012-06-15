# Running the unit tests

## memcache

### setup_test_env.sh

Run this first.  This will create a new virtualenv and install all the prereqs for the memcache tests.

### run_memcache_tests.sh

This wraps test_memcache.py, starting and stopping a memcached server so that you don't have to.  `./run_memcache_tests.sh -v` for more detail.
