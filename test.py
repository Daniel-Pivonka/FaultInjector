#!/usr/bin/python

import threading
import time

class Fault:
	def stateless(self):
		raise NotImplementedError

	def stateful(self):
		raise NotImplementedError

	def deterministic(self):
		raise NotImplementedError


class Ceph(Fault):

def main():
















# 	print "main"
# 	t1 = threading.Thread(target=thread1)
# 	t2 = threading.Thread(target=thread2)
# 	t3 = threading.Thread(target=thread3)
# 	t1.start()
# 	t2.start()
# 	t3.start()

# 	t1.join()
# 	t2.join()
# 	t3.join()

# 	print "done"

# def thread1():
# 	time.sleep(5)
# 	print "im the thread1"
# 	time.sleep(5)
# 	print "thread1 again"

# def thread2():
# 	time.sleep(5)
# 	print "im the thread2"
# 	time.sleep(5)
# 	print "thread2 again"

# def thread3():
# 	time.sleep(5)
# 	print "im the thread3"
# 	time.sleep(5)
# 	print "thread3 again"


if __name__ == "__main__":
    main()
