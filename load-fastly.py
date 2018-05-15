#!/usr/local/bin/python
#
import requests
import sys
import json
import os
import errno
import getopt

class pfctl(object):
    def __init__(self):
        self.table = "fastlycdn"

    def set_table(self, tbl):
        self.table = tbl

    def add(self, hosts):
        args = [ "pfctl", "-t", self.table, "-T", "add", "-f-" ]
        try:
            self.pfctl(args, hosts)
        except:
            raise

    def flush(self):
        args = [ "pfctl", "-t", self.table, "-T", "flush" ]
        d = []
        try:
            self.pfctl(args, d)
        except:
            raise

    def pfctl(self, args, indata):
        dopipe = 0
        if len(indata) > 0:
            dopipe = 1
            try:
                r, w = os.pipe()
            except OSError as e:
                print "pipe failed"
                raise
        try:
            pid = os.fork()
        except OSError as e:
            print "fork failed"
            raise
        if pid == 0:
            if dopipe == 1:
                os.dup2(r, sys.stdin.fileno())
                os.close(w)
            try:
                os.execv("/sbin/pfctl", args)
            except OSError as e:
                print "exec failed"
                raise
        if dopipe == 1:
            os.close(r)
            for a in indata:
                a = "{}\n".format(a)
                os.write(w, a)
            os.close(w)
        while True:
            try:
                a, b = os.waitpid(pid, 0)
            except OSError as e:
                if e.errno == errno.EINTR:
                    continue
            break

class cmdopt(object):
    table = None
    url = "https://api.fastly.com/public-ip-list"

def main():
    co = cmdopt()
    try:
        opts, args = getopt.getopt(sys.argv[1:], "t:u:")
    except getopt.GetoptError as e:
        print "invalid command line: {}".format(e.msg)
        sys.exit(1)
    for o, a in opts:
        if o == "-t":
            co.table = a
        if o == "-u":
            co.url = a
    try:
        req = requests.get(co.url)
    except:
        print "failed to get IP list"
        sys.exit(1)
    if req.status_code != 200:
        print "got status: {} expected 200".format(req.status_code)
    try:
        jd = json.loads(req.text)
    except:
        print "failed to parse JSON"
        sys.exit(1)
    if "addresses" not in jd.keys():
        print "unexpected JSON data"
        sys.exit(1)
    alist = jd['addresses']
    data = []
    for spec in alist:
        data.append(spec)
    pfo = pfctl()
    if co.table != None:
        pfo.set_table(co.table)
    try:
        pfo.flush()
        pfo.add(data) 
    except Exception as e:
        print "PF operation failed: {}".format(e)
    return 0

if __name__ == "__main__":
    main()
