import orm, asyncio
from models import User, Blog, Comment

@asyncio.coroutine
def test(loop):
    yield from orm.create_pool(loop=loop, user='root', password='aptx4869', db='pythonwebapp')

    u = User(name='Test2', email='test2@example.com', passwd='1234567890', image='about:blank')

    yield from u.save()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()