"""
Locks for mutex areas and lock management.
"""
import os
import socket


class LockException(Exception):
    """
    Represents an error with the locking.
    """


class RedisLock(object):
    """
    This class implements a semaphore with the help of
    a global redis server.
    """

    lua_refresh = """
        if redis.call("get", KEYS[1]) == ARGV[1]
        then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
    """

    def __init__(self, redis, lock_identifier, lock_time=5):
        """
        Initializes the RedisLock

        :redis: the redis connection
        :lock_identifier: the lock identifier
        :lock_time: the expiry time of the lock in seconds

        """
        self.redis = redis
        self.lock_identifier = lock_identifier
        self.lock_time = lock_time
        self.process_identifer = "%s:%s" % (socket.gethostname(), os.getpid())
        # Register the lua refresh script

    def acquire(self):
        """
        Try to acquires the lock.
        Returns True when we got the lock, else False.
        """
        return self.redis.set(
            self.lock_identifier, self.process_identifer,
            nx=True,
            ex=self.lock_time if self.lock_time > 5 else self.lock_time * 5)

    def refresh(self):
        """
        Refreshes the lock.
        """
        if not self.redis.eval(self.lua_refresh, 1, [self.lock_identifier,
                                                     self.process_identifer,
                                                     self.lock_time]):
            raise LockException('Could not refresh lock')
