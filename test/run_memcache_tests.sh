memcached -p 5679 &
memcached_pid=$!
source venv-oboeware-test/bin/activate
python unit/test_memcache.py $@
kill $memcached_pid
wait $memcached_pid 2>/dev/null
