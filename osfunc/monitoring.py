import time
import datetime

from os import environ

from functools import wraps
from random import randint
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, Float, Integer, String, Sequence,
                        Text, DateTime, ForeignKey, Boolean)
from sqlalchemy.exc import OperationalError

try:
    db_string = environ['OS_DB_STRING']
except KeyError:
    db_string = None

sql_conn = False
Base = declarative_base()

if db_string is not None:
    engine = create_engine(db_string,
                           connect_args={'connect_timeout': 5})

    Session = sessionmaker(bind=engine)
    session = Session()
    sql_conn = True


class ModuleRecs(Base):

    """
    This class is responsible for creating the DB tables - if they don't already exist

    Database Configuration
    To log to a DB, export OS_DB_STRING as defined in:
    http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html
    For example: export OS_DB_STRING=mysql://<user>:<password>@<host>/<db_name>

    """

    __tablename__ = 'module_recs'

    id = Column(Integer, primary_key=True)
    service = Column(String(128))
    exec_time = Column(DateTime)
    name = Column(String(128))
    run_time = Column(Float)
    success = Column(Boolean)
    failure_reason = Column(Text)
    zone = Column(Text)
    region = Column(Text)
    tenant_name = Column(Text)
    function_run_time = Column(DateTime)

if db_string is not None:
    try:
        Base.metadata.create_all(engine)
    except OperationalError:
        sql_conn = False


def timeit(f):
    """

    Decorator function which times the function being
    decorated and displays a boolean for success or failure
    The function optionally inserts the timestamp, service name,
    run time, and success / failure into the DB

    """

    @wraps(f)
    def timed(self):
        st = time.time()
        result = f(self)
        en = time.time()

        function_run_time = datetime.datetime.now()

        self.logger.warn('<*> {0} - Executed in: {1:.2f} sec - {2}'.
                         format(f.__name__, en - st, self.success))

        message = {
            'service': self.service,
            'exec_time': str(self.exec_time),
            'name': f.__name__,
            'run_time': '{0:.2f}'.format(en - st),
            'success': self.success,
            'failure_reason': str(self.failure)
        }

        run = {
            'msg_type': 'snapshot',
            'record_id': self.service + '_OperationalMonitoring-{}'.format(randint(1, 10**10)),
            'source':
                {
                    'system': 'jenkins.noctesting.com',
                    'type': 'jenkins',
                    'location': 'AE1'
                },
            'batch_ts': int(self.exec_time.strftime('%s')),
            'record_ts': int(self.exec_time.strftime('%s')),
            'version':
                {
                    'major': '0.0.1'
                },
            'payload': message
        }
        if sql_conn:
            entry = ModuleRecs(service=self.service,
                               exec_time=self.exec_time,
                               name=f.__name__,
                               run_time='{0:.2f}'.format(en - st),
                               success=self.success,
                               failure_reason=self.failure,
                               zone=self.zone,
                               region=self.region,
                               tenant_name=self.tenant_name,
                               function_run_time=function_run_time)

            session.add(entry)
            session.commit()

        self.failure = None

        return result
    return timed
