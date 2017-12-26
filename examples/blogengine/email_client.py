import sys, smtplib

fromaddr = input("From: ")
toaddrs  = input("To: ").split(',')
print("Enter message, end with ^D:")
msg = ''
while 1:
    line = sys.stdin.readline()
    if not line:
        break
    msg = msg + line

# The actual mail send
server = smtplib.SMTP('localhost', 2500)
server.sendmail(fromaddr, toaddrs, msg)
server.quit()
