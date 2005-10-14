from zope.interface import implements
import pgasync
import itodo

class Todos(object):
    implements(itodo.ITodos)
    def __init__(self, dbname, user, password, host):
        self.original = pgasync.ConnectionPool("pgasync", dbname=dbname, 
                        user=user, password=password, host=host)

    def add(self, description, done):
        query = "INSERT INTO todos (description, done) VALUES (%(description)s,%(done)s)"
        args = dict(description=description, done=done)
        return self.original.runOperation(query, args)
    
    def delete(self, id):
        query="DELETE FROM todos WHERE id=%(id)s"
        args = dict(id=id)
        return self.original.runOperation(query, args)
        
    def update(self, id, state):
        query = "UPDATE todos SET done=%(done)s WHERE id=%(id)s"
        args = dict(id=id, done=state)
        return self.original.runOperation(query, args)

    def findAll(self):
        query = "SELECT * FROM todos"
        return self.original.runQuery(query)
    
