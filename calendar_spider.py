"""
获取网络节日日历数据，构建苹果日历数据
from url: https://www.rili.com.cn/jieridaquan/
to: calendar_{year}_jr.ics
"""
from datetime import datetime
import re
import httpx
from faker import Faker
from lxml import etree

now = datetime.now().strftime('%Y%m%dT%H:%M:%S')


def set_ics_header(year):
    return "BEGIN:VCALENDAR\n" \
           + "PRODID:NULL\n" \
           + "VERSION:2.0\n" \
           + "CALSCALE:GREGORIAN\n" \
           + "METHOD:PUBLISH\n" \
           + f"X-WR-CALNAME:{year}年节假日\n" \
           + "X-WR-TIMEZONE:Asia/Shanghai\n" \
           + f"X-WR-CALDESC:{year}年节假日\n" \
           + "BEGIN:VTIMEZONE\n" \
           + "TZID:Asia/Shanghai\n" \
           + "X-LIC-LOCATION:Asia/Shanghai\n" \
           + "BEGIN:STANDARD\n" \
           + "TZOFFSETFROM:+0800\n" \
           + "TZOFFSETTO:+0800\n" \
           + "TZNAME:CST\n" \
           + "DTSTART:19700101T000000\n" \
           + "END:STANDARD\n" \
           + "END:VTIMEZONE\n"

  
def set_jr_ics(jr, date, uid):  # jr: 节日，date：日期，uid：编序
    return "BEGIN:VEVENT\n" \
           + f"DTSTART;VALUE=DATE:{date}\n" \
           + f"DTEND;VALUE=DATE:{date}\n" \
           + f"DTSTAMP:{date}T000001\n" \
           + f"UID:{date}T{uid:0>6}_jr\n" \
           + f"CREATED:{date}T000001\n" \
           + f"DESCRIPTION:{jr}\n" \
           + f"LAST-MODIFIED:{now}\n" \
           + "SEQUENCE:0\n" \
           + "STATUS:CONFIRMED\n" \
           + f"SUMMARY:{jr}\n" \
           + "TRANSP:TRANSPARENT\n" \
           + "END:VEVENT\n"
  

def get_url():
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'User-Agent': Faker().chrome(version_from=98, version_to=100, build_from=4800, build_to=5000),
        'Host': 'www.rili.com.cn',
        'Referer': 'https://www.rili.com.cn'
    }

    url = 'https://www.rili.com.cn/jieridaquan/'
    try:
        response = httpx.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except Exception as e:
        print(e)
        return None


def parse_jr_date(text, y):
    jr, dt = text.split('[')
    dt = f'{y}年' + re.search(r'\d{1,2}月\d{1,2}日', dt).group()
    dt = datetime.strptime(dt, '%Y年%m月%d日').strftime('%Y%m%d')
    return jr, dt


def parse_html(html):
    html = etree.HTML(html)
    date = html.xpath('//meta[@name="LastUpdate"]/@content')[0]
    y = datetime.strptime(date, '%Y/%m/%d %H:%M:%S').year
    jr_rili = ''.join(html.xpath('//li[@class="jr1"]//text()')).split(']')[:-1]
    # 规避gitee代码审查ics文件部分
    jr_rili = [i for i in jr_rili if '逝' not in i or '世' not in i]
    jr_rili = [i for i in jr_rili if '毛' not in i or '东' not in i or '泽' not in i]
    return y, jr_rili


def concat_ics(y, jr):  # 返回一个完整的ics文件内容
    header = set_ics_header(y)
    jr_rq = list(map(parse_jr_date, jr, [y] * len(jr)))
    # 将同一天的节日进行编号
    jr_rq.sort(key=lambda x: x[1])
    pre_num = 0
    for num in range(len(jr_rq)):
        if jr_rq[num][1] != jr_rq[pre_num][1]:
            pre_num = num
        jr_rq[num] += (num - pre_num + 1,)
    jr_ics = ''.join(map(lambda x: set_jr_ics(*x), jr_rq))
    return header + jr_ics + 'END:VCALENDAR'


def save_ics(fname, text):
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(text)


if __name__ == '__main__':
    rl_html = get_url()
    assert rl_html, '数据获取失败'
    year, jr_list = parse_html(rl_html)
    jr_ics = concat_ics(year, jr_list)
    filename = f'calendar_{year}_jr.ics'
    save_ics(filename, jr_ics)
