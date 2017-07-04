#! /usr/bin/env python
# coding=utf-8
import sys
import poplib
import smtplib
import imaplib


# 邮件发送函数
def send_mail():
    try:
        handle = smtplib.SMTP('smtp.mxhichina.com', 25)
        handle.login('jason.lu@linkloving.com', 'Nt5211314!@#')
        msg = 'To: XXXX@qq.com\r\nFrom:XXXX@126.com\r\nSubject:hello1112322323231\r\nContent:12312312312323232'
        handle.sendmail('jason.lu@linkloving.com', '435676558@qq.com', msg)
        handle.close()
        return "1"

    except:
        return "0"


# 邮件接收函数
def accpet_mail():
    try:
        p = poplib.POP3('pop.mxhichina.com')
        p.user('jason.lu@linkloving.com')
        p.pass_('Nt5211314!@#')
        ret = p.stat()  # 返回一个元组:(邮件数,邮件尺寸)
        if(ret):
            print ret.count()
        else:
            print 'null'
        # p.retr('邮件号码')方法返回一个元组:(状态信息,邮件,邮件尺寸)
    except poplib.error_proto, e:
        print "Login failed:", e
        sys.exit(1)


# 运行当前文件时，执行sendmail和accpet_mail函数
if __name__ == "__main__":
    a = send_mail()
    # print  '-----' + a
    # accpet_mail()
