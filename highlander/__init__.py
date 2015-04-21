"""
Highlander is a helper to start one process only on one server in a cluster.
For example a celery beat process.

   There can be only one!

Copyright 2015 Michael Trunner

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import argparse
import os
import signal
import socket
import subprocess
import sys
import time

import redis


class LockException(Exception):
    """
    Represents an error with the locking.
    """


class RedisLock(object):
    """
    This class implements a semaphore with the help of
    a global redis server.
    """

    def __init__(self, redis_url, lock_identifier, lock_time=5):
        """
        Initializes the RedisLock

        :redis_url: the redis connection url
        :lock_identifier: the lock identifier
        :lock_time: the expiry time of the lock in seconds

        """
        self.redis = redis.Redis.from_url(redis_url)
        self.redis.ping()
        self.lock_identifier = lock_identifier,
        self.lock_time = lock_time
        self.process_identifer = "%s:%s" % (socket.gethostname(), os.getpid())

    def acquire_lock(self):
        """
        Try to acquires the lock.
        Returns True when we got the lock, else False.
        """
        lock_time = self.lock_time
        if lock_time < 5:
            lock_time = lock_time * 5
        return self._lock(lock_time, nx_flag=True)

    def refresh_lock(self):
        """
        Refreshes the lock.
        """
        if self.redis.get(self.lock_identifier) != self.process_identifer:
            raise LockException('Lost the lock')
        if not self._lock(self.lock_time, nx_flag=False):
            raise LockException('Could not refresh lock')

    def _lock(self, lock_time, nx_flag=False):
        """
        Helper method for the redis set lock call.
        """
        return self.redis.set(
            self.lock_identifier, self.process_identifer,
            nx=nx_flag, ex=lock_time)


class Process(object):
    """
    Class that handels out subprocess
    """

    def __init__(self, cmd):
        self.cmd = cmd
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        signal.signal(signal.SIGINT, self.sigterm_handler)
        self.process = subprocess.Popen(self.cmd)
        sys.stdin.close()

    def stop(self):
        """
        Stops the subprocess with SIGTERM
        """
        self.process.terminate()

    def sigterm_handler(self, signum, frame):
        """
        signal handler to forward signals to the subprocess
        """
        # pylint: disable=unused-argument
        self.process.send_signal(signum)

    def return_code(self):
        """
        Returns the return_code if the subprocess has died,
        else None.
        """
        return self.process.poll()


class Highlander(object):

    """ The Highlander main class """

    def __init__(self, lock_manager, cmd, heartbeat_interval):
        """
        Creates a new Highlander instance

        :lock_manager: The used lock manger
        :cmd: The command that should be startet as subprocess
        :heartbeat_interval: The heartbeat interval in seconds

        """
        self._lock_manager = lock_manager
        self._cmd = cmd
        self._heartbeat_interval = heartbeat_interval

    def run(self):
        """
        The mainloop(s) of highlander
        """
        while not self._lock_manager.acquire_lock():
            self.sleep()
        proc = Process(self._cmd)
        while proc.return_code() is None:
            self._lock_manager.refresh_lock()
            self.sleep()
        return proc.return_code()

    def sleep(self):
        """
        Let's the os process sleep for the given heartbeat interval.
        """
        time.sleep(self._heartbeat_interval)


def main():
    """
    Main function called when this python module is called as script.
    """
    parser = argparse.ArgumentParser(
        description='%(prog)s checks that the defind subprocess '
                    'is only started once in a cluster.'
                    '\n\n There can be only one!')
    parser.add_argument('redis_url',
                        help='URL of the Redis server.')
    parser.add_argument('-i', '--lock-identifier',
                        help='The identifier of the lock')
    parser.add_argument('-t', '--heartbeat',
                        dest='heartbeat_interval',
                        default=3, type=int,
                        help='The heartbeat interval in seconds')
    args, cmd = parser.parse_known_args()
    lock_manager = RedisLock(
        args.redis_url, 'HIGHLANDER_%s' % " ".join(cmd),
        args.heartbeat_interval * 2)
    highlander = Highlander(lock_manager, cmd, args.heartbeat_interval)
    sys.exit(highlander.run())


if __name__ == '__main__':
    main()
