#!/usr/bin/env python
import signal, os, sys
    
def wait(wait_max):
    pid = os.fork()
    if pid == 0:
        signal.alarm(wait_max)
        fd = os.open("/tmp/FIFO", os.O_RDONLY)
        sys.exit(0)
    (wpid, status) = os.waitpid(pid, 0)
    signo = status & 255
    if signo:
        print("timeout")
        return False

    return True


release = wait(5)
print("release="+str(release))

