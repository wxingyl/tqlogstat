#! /bin/bash

osname=`uname`
if [ $osname == 'Linux' ]; then
	DATE_STR=`date --date="1 day ago" +"%Y-%m-%d"`
	NOW_TIME=`date "+%F-%T"`
elif [ $osname == 'Darwin' ]; then
	DATE_STR=`date -v-1d "+%Y-%m-%d"`
	NOW_TIME=`date "+%Y-%m-%d-%H:%M:%S"`
else
	echo "当前操作系统:"$osname"不支持"
	exit
fi
echo '开始执行：'$NOW_TIME', 参数: '$*

function get_log_file()
{
    shop_host='10.162.51.140'
    shop_beta='10.168.86.137'
    stall_host='10.168.86.137'
    stall_beat='10.165.6.247'
	#    先获取error log
	log_path='/data/app_server/logs/error.'$DATE_STR'.log'
	scp -P 22222  'tqmall.app@'$shop_host':'$log_path $1
	scp -P 22222 'tqmall.app@'$shop_beta':'$log_path tmp_error.log
	cat tmp_error.log >> $1
	log_path='/data/stall_server/logs/error.'$DATE_STR'.log'
	scp -P 22222 'tqmall.stall@'$stall_host':'$log_path tmp_error.log
	cat tmp_error.log >> $1
	scp -P 22222 'tqmall.stall@'$stall_beat':'$log_path tmp_error.log
	cat tmp_error.log >> $1
	rm tmp_error.log
	if [ -n "$2" ]; then
		#    再获取common log
		log_path='/data/app_server/logs/common.'$DATE_STR'.log'
		scp -P 22222  'tqmall.app@'$shop_beat':'$log_path $2
		scp -P 22222 'tqmall.app@'$shop_host':'$log_path tmp_common.log
		cat tmp_common.log >> $2
		log_path='/data/stall_server/logs/common.'$DATE_STR'.log'
		scp -P 22222 'tqmall.stall@'$stall_host':'$log_path tmp_common.log
		cat tmp_common.log >> $2
		scp -P 22222 'tqmall.stall@'$stall_beat':'$log_path tmp_common.log
		cat tmp_common.log >> $2
		rm tmp_common.log
	fi
}

function get_nginx_log()
{
   nginx_log='/data/log/nginx/access.log'
   ip='10.162.51.140'
   scp -P 22222 'tqmall.app@'$ip':'$nginx_log $1
}

function print_help()
{
	echo '-a: action, 操作类型,必传参数,可取值:'
	echo '      stat: 执行log分析统计'
	echo '      user: 执行获取优质客户'
	echo '      hits: 执行nginx分享次数统计'
	echo '      coupon: 根据分享次数插入优惠劵'
	echo '-w: workspace, 当前代码主目录,必传参数'
	echo '-date: 统计指定日期的log，默认昨天'
	echo '-c: 执行程序的config文件，必须参数'
	echo '-d: debug, 调试模式'
	echo '-h: help, 查看帮助'
}


while [ $# -gt 0 ]
do
	tmp=$1
	shift
	case $tmp in
	'-a')
		action=$1
		;;
	'-w')
		dir=$1
		;;
	'-date')
	    DATE_STR=$1
	    ;;
	'-c')
	    conf=$1
	    ;;
	'-h')
		print_help
		exit
		;;
	*)
	    ext_arg=$tmp' '$@
		break
		;;
	esac
	shift
done

if [ -z "$dir" ]; then
	dir=`pwd`
fi

if [ -z "$conf" ]; then
	conf=$dir'/stat.conf'
fi

if [ -z "$dir" ] || [ -z "$action" ] || [ -z "$conf" ]; then
    echo '参数有误，详情查看-h'
    exit
fi

echo 'dir = '$dir', DATE_STR = '$DATE_STR', conf = '$conf

python_file=$dir'/src/stat.py'
case $action in
'stat')
	source_file=$dir'/data/error.'$NOW_TIME'.log'
	common_file=$dir'/data/common.'$NOW_TIME'.log'
	tmp_result=$dir'/data/tmp_result'
	get_log_file $source_file

#	jpush的统计暂时关掉
#	get_log_file $source_file $common_file
#	echo "JPush stat start" > $tmp_result
#    cat $common_file | grep "调用JPush接口发生异常" -B 3 >> $tmp_result
#	echo "JPush stat end" >> $tmp_result
	args='-f '$source_file' -t '$DATE_STR
	;;
'user')
	source_file=$dir'/data/high_quality_user'
	$dir/lottery/change_conf.sh 7 245 > $source_file
	echo 'user_file: '$source_file
	args='-f '$source_file
	;;
'hits')
    source_file=$dir'/data/nginx.log'
    get_nginx_log $source_file
    echo 'nginx log: '$source_file
    args='-f '$source_file
    ;;
*)
	echo '指定操作类型错误，查看-h'
	exit
	;;
esac
/usr/local/bin/python2.7 $python_file -a $action -c $conf $args $ext_arg
#python $python_file -a $action -c $conf $args $ext_arg


if [ $osname == 'Linux' ]; then
	NOW_TIME=`date "+%F %T"`
else
	NOW_TIME=`date "+%Y-%m-%d %H:%M:%S"`
fi
echo '执行完成, 当前时间: '$NOW_TIME
echo
echo
