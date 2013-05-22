'''
Created on May 12, 2013

@author: GoldRatio
'''
    
import functools
from tornado.web import HTTPError

def authenticatedRepository(method):
    """Decorate methods with this to require that the user be logged in.

    If the user is not logged in, they will be redirected to the configured
    `login url <RequestHandler.get_login_url>`.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        currentProjectId = int(args[0])
        if currentProjectId not in self.current_user.projects:
            raise HTTPError(404)
        return method(self, *args, **kwargs)
    return wrapper

