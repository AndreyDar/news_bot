from xmlrpc.client import Boolean
from sqlalchemy import create_engine, MetaData, Table, Column, BigInteger, Date,  Integer, String, Boolean
from sqlalchemy.orm import declarative_base, registry, sessionmaker
engine = create_engine("postgresql://user:password@hostname/database_name")


# declarative base class
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key = True)
    first_name = Column(String, nullable = True)
    second_name = Column(String, nullable = True)
    tg_name = Column(String, nullable = True)
    role = Column(String, nullable = True)
    in_editing = Column(String, nullable = True)
    is_banned = Column(Boolean, nullable = True)
    news_in_process = Column(String, nullable = True)


    def __init__(self, id, first_name, second_name, tg_name, role, in_editing, is_banned):
        self.id = id
        self.first_name = first_name
        self.second_name = second_name
        self.tg_name = tg_name
        self.role = role
        self.in_editing = in_editing
        self.is_banned = is_banned

    def __repr__(self):
        return self.tg_name



class Post(Base):
    __tablename__ = 'news'
    id = Column(String, primary_key = True)
    is_posted = Column(Boolean, nullable = True)
    proсessing_by = Column(String, nullable = True)
    posted_by = Column(String, nullable = True)
    on_approval = Column(Boolean, nullable = True)
    is_approved = Column(Boolean, nullable = True)
    msgs_number = Column(Integer, nullable = True)
    first_msg_id = Column(String, nullable = True)

    

    
    def __init__(self, id, is_posted, proсessing_by, posted_by, on_approval, is_approved, msgs_number, first_msg_id):
        self.id = id
        self.proсessing_by = proсessing_by
        self.is_posted = is_posted
        self.posted_by = posted_by
        self.on_approval = on_approval
        self.is_approved = is_approved
        self.msgs_number = msgs_number
        self.first_msg_id = first_msg_id

    def __repr__(self):
        return self.id


class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key = True)
    category = Column(String, nullable = True)
    name = Column(String, nullable = True)
    source = Column(String, nullable = True)

    def __init__(self, id, category, name, source):
        self.id = id
        self.category = category
        self.name = name
        self.source = source

    def __repr__(self):
        return self.id




Base.metadata.create_all(engine)



'''
Session = sessionmaker(engine)
session = Session()

cur_news = session.query(Post).filter(Post.proсessing_by == "andr3y_dar").all()
print(cur_news)
for item in cur_news:
    item.proсessing_by = None


session.commit()
'''

'''
Session = sessionmaker(engine)
session = Session()

user = session.query(User).filter(User.tg_name == 'andr3y_dar').first()
user.role = "admin"


session.commit()
'''