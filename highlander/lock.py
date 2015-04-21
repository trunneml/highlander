"""
Locks for mutex areas and lock management.
"""
import os
import socket
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

    def acquire(self):
        """
        Try to acquires the lock.
        Returns True when we got the lock, else False.
        """
        lock_time = self.lock_time
        if lock_time < 5:
            lock_time = lock_time * 5
        return self._lock(lock_time, nx_flag=True)

    def refresh(self):
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
