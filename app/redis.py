import redis
from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.utils.functional import cached_property

class SessionStore(SessionBase):

    @cached_property
    def _connection(self):
        return redis.Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            db=settings.REDIS_DB,
            decode_responses=True)
       

    def load(self):
        # Loads the session data by the session key.
        # Returns dictionary.
        return self._connection.hgetall(self.session_key)

    def exists(self, session_key):
        # Checks whether the session key already exists
        # in the database or not.
        return self._connection.exists(session_key)

    def create(self):
        # Creates a new session in the database.
        self._session_key = self._get_new_session_key()
        self.save(must_create=True)
        self.modified = True

    def save(self, must_create=False):
        # Saves the session data. If `must_create` is True,
        # creates a new session object. Otherwise, only updates
        # an existing object and doesn't create one.
        if self.session_key is None:
            return self.create()

        data = self._get_session(no_load=must_create)
        session_key = self._get_or_create_session_key()
        self._connection.hset(session_key, 'session_key', session_key, data)
        self._connection.expire(session_key, self.get_expiry_age())

    def delete(self, session_key=None):
        # Deletes the session data under the session key.
        if session_key is None:
            if self.session_key is None:
                return
            session_key = self.session_key
        self._connection.delete(session_key)

    @classmethod
    def clear_expired(cls):
        # There is no need to remove expired sessions by hand
        # because Redis can do it automatically when
        # the session has expired.

        # We set expiration time in `save` method.
        pass
