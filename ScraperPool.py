import threading, time, copy, string, random, os

class JobThread(threading.Thread):
    def __init__(self, parentPool, threadID):
        threading.Thread.__init__(self)
        self.pool = parentPool
        self.myId = threadID

    def run(self):
        while True:
            job = self.pool.getJob()
            if (job == None):
                #print "Thread %d : NO MORE JOBS" % (self.myId)
                break
            #print "Thread %d : got new job" % (self.myId)
            self.pool.pushResult(job())
        return

class ThreadPool(object):
    def __init__(self, poolsize):
        self.results = []
        self.res_lock = threading.Lock()
        self.nbthreads = poolsize
        self.jobsLock = threading.Lock()
        self.finiEvent = threading.Event()

    def getJob(self):
        return None

    def signalFinished(self):
        self.finiEvent.set()
    
    def pushResult(self, res):
        self.res_lock.acquire()
        self.results.append(res)
        self.res_lock.release()

    def executeJobs(self):
        # Starting Threads
        self.threads = []
        for i in range(self.nbthreads):
            t = JobThread(self, i)
            t.start()
            self.threads.append(t)
        
        # Waiting to finish
        self.finiEvent.wait()
            
        #print "Gave everything out, waiting for threads to finish ..."
        for t in self.threads:
            t.join()
        #print "Cleaned up threads!"
        return self.results
            

class FetcherPool(ThreadPool):
    def __init__(self, fetcher, urls, poolsize, savePath=None):
        ThreadPool.__init__(self, poolsize)
        self.fetcher = fetcher
        self.urls = urls
        self.path = savePath

    def finished(self):
        return len(self.urls) == 0

    def random_key(self, length):
        key = ''
        for i in range(length):
            key += random.choice(string.lowercase + string.uppercase + string.digits)
        return key

    def exists(self, filename):
        contents = os.listdir(self.path)
        for name in contents:
            if name.find(filename) != -1:
                return True
        return False
    
    def getJob(self):
        self.jobsLock.acquire()
        if (len(self.urls) == 0):
            job = None
        else:
            url = copy.deepcopy(self.urls[0])
            if (self.path != None):
                fileId = self.random_key(10)
                while self.exists(fileId):
                    fileId = self.random_key(10)
                filename = self.path + "img_" + fileId + ".jpg"
                job = lambda: self.fetcher(url, filename)
            else:
                job = lambda: self.fetcher(url)
            self.urls.pop(0)
            if (len(self.urls) == 0):
                self.signalFinished()
        self.jobsLock.release()
        return job

