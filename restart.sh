kill -s 9 `ps -aux | grep uwsgi | awk '{print $2}'`
source activate mini_program
uwsgi --ini mini_program.ini