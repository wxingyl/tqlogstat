#! /bin/bash

DATE=`date '+%F %T'`
ISERVER_HOST='http://10.168.86.137:8080'

function print_help()
{
	echo "1: 添加黑名单, 指定黑名单uid list, 多个用户通过','分隔"
	echo "2: 清除黑名单"
	echo "3: 更新lottery_log表中的status，从0更新为1，必须指定活动actId"
	echo "4: allowed_user表中的status加100, 必须指定活动actId"
	echo "5: 修改batch_size, 默认1000"
	echo "6: 清除客户列表打标的缓存, 必须指定actId"
	echo "7: 获取allowed_user中的userId和优质客户打标的交集列表, 必须指定actId"
}

echo "执行时间："$DATE
if [ $# -eq 0 ]; then
	echo "必须指定action才能执行开奖程序, 详情查看-h"
	exit 0
fi
case $1 in
	"1")
		url="1&blackIds="$2
	;;
	"2")
		url="2"
	;;
	"3")
		url="3&actId="$2
	;;
	"4")
		url="4&actId="$2
	;;
	"5")
		url="5&batchSize="$2
	;;
	"6")
		url="6&actId="$2
	;;
	"7")
		url="7&actId="$2
	;;
	"-h")
		print_help
	;;
	*)
		echo "输入参数有误，如下："
		print_help
	 ;;
esac
if [ 'X'$url != 'X' ]; then
	curl "$ISERVER_HOST/lottery/config?action=$url"
fi
echo