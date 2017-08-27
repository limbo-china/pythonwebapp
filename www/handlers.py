#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re, time, json, logging, hashlib, base64, asyncio
from aiohttp import web

from webframe import get, post

from models import User, Comment, Blog, Schedule, Reading, Book, next_id
from apis import Page, APIValueError
import markdown2

' url handlers ' 

COOKIE_NAME = 'limboCookie'
_COOKIE_KEY = 'limboKey'

def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

async def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None

@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
    }
@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r

@post('/api/authenticate')
async def authenticate(*, name, passwd):
    if not name:
        raise APIValueError('name', 'Invalid name.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    users = await User.findAll('name=?', [name])
    if len(users) == 0:
        raise APIValueError('user', 'User not exist.')
    user = users[0]
    # check passwd:
    if user.passwd != passwd:
        raise APIValueError('passwd', 'Invalid password.')
    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 3600), max_age=3600, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p
@get('/')
async def index(*,action='books',page='1'):

    page_index = get_page_index(page)
    if action == 'blogs':
        num = await Blog.findNumber('count(id)')
        p = Page(num,page_index,5)
        if num == 0:
            blogs = []
        else:
            blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
        return {
            '__template__': 'blogs.html',
            'page': p,
            'blogs': blogs
            }
    elif action == 'books':
        num = await Book.findNumber('count(id)')
        p = Page(num,page_index,5)
        if num == 0:
            books = []
        else:
            books = await Book.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
        return {
            '__template__': 'books.html',
            'page': p,
            'books': books
            }
    elif action == 'schedules':
        num = await Schedule.findNumber('count(id)')
        p = Page(num,page_index,5)
        if num == 0:
            schedules = []
        else:
            schedules = await Schedule.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
        return {
            '__template__': 'schedules.html',
            'page': p,
            'page_index': get_page_index(page)
        }
    elif action == 'readings':
        num = await Reading.findNumber('count(id)')
        p = Page(num,page_index,5)
        if num == 0:
            readings = []
        else:
            readings = await Reading.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
        return {
            '__template__': 'readings.html',
            'page': p,
            'readings': readings
            }

@get('/api/users')
async def api_get_users(*, page='1'):
    users = await User.findAll(orderBy='created_at desc')
    for u in users:
        u.passwd = '******'
    return dict(page=page, users=users)

@get('/manage/blog/create')
def manage_create_blog():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blog'
    }

@get('/manage/book/create')
def manage_create_book():
    return {
        '__template__': 'manage_book_edit.html',
        'id': '',
        'action': '/api/book'
    }

@get('/manage/schedule/create')
def manage_create_schedule():
    return {
        '__template__': 'manage_schedule_edit.html',
        'id': '',
        'action': '/api/schedule'
    }

@get('/manage/reading/create')
def manage_create_reading():
    return {
        '__template__': 'manage_reading_edit.html',
        'id': '',
        'action': '/api/reading'
    }

@get('/manage/blogs')
async def manage_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page),
        'page': p,
    }

@get('/manage/books')
async def manage_books(*, page='1'):
    page_index = get_page_index(page)
    num = await Book.findNumber('count(id)')
    p = Page(num, page_index)
    return {
        '__template__': 'manage_books.html',
        'page_index': get_page_index(page),
        'page': p,
    }

@get('/manage/schedules')
async def manage_schedules(*, page='1'):
    page_index = get_page_index(page)
    num = await Schedule.findNumber('count(id)')
    p = Page(num, page_index)
    return {
        '__template__': 'manage_schedules.html',
        'page_index': get_page_index(page),
        'page': p,
    }

@get('/manage/readings')
async def manage_readings(*, page='1'):
    page_index = get_page_index(page)
    num = await Reading.findNumber('count(id)')
    p = Page(num, page_index)
    return {
        '__template__': 'manage_readings.html',
        'page_index': get_page_index(page),
        'page': p,
    }

@get('/api/blog/{id}')
async def api_get_blog(*, id):
    blog = await Blog.find(id)
    return blog

@get('/api/book/{id}')
async def api_get_book(*, id):
    book = await Book.find(id)
    return book

@get('/api/schedule/{id}')
async def api_get_schedule(*, id):
    schedule = await Schedule.find(id)
    return schedule

@get('/api/reading/{id}')
async def api_get_reading(*, id):
    reading = await Reading.find(id)
    return reading

@post('/api/blog')
async def api_create_blog(request, *, name, summary, content):
    #check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog = Blog(user_id='limbo', user_name='limbo', user_image='limbo', name=name.strip(), summary=summary.strip(), content=content.strip())
    await blog.save()
    return blog

@post('/api/book')
async def api_create_book(request, *, name, author, content):
    #check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    book = Book(name=name.strip(), author=author.strip(), content=content.strip())
    await book.save()
    return book

@post('/api/schedule')
async def api_create_schedule(request, *, schedule):
    #check_admin(request)
    if not schedule or not schedule.strip():
        raise APIValueError('content', 'content cannot be empty.')
    schedule = Schedule(schedule=schedule.strip())
    await schedule.save()
    return schedule

@post('/api/reading')
async def api_create_reading(request, *, name, author, content):
    #check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not author or not author.strip():
        raise APIValueError('author', 'author cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    reading = Reading(name=name.strip(), author=author.strip(), content=content.strip())
    await reading.save()
    return reading

@get('/api/blogs')
async def api_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)

@get('/api/books')
async def api_books(*, page='1'):
    page_index = get_page_index(page)
    num = await Book.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, books=())
    books = await Book.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, books=books)

@get('/api/schedules')
async def api_schedules(*, page='1'):
    page_index = get_page_index(page)
    num = await Schedule.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, schedules=())
    schedules = await Schedule.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, schedules=schedules)

@get('/api/readings')
async def api_readings(*, page='1'):
    page_index = get_page_index(page)
    num = await Reading.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, readings=())
    readings = await Reading.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, readings=readings)

@get('/blog/{id}')
async def get_blog(*,id):
    blog = await Blog.find(id)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'blog.html', 
        'blog': blog,
    }

@get('/book/{id}')
async def get_book(*,id):
    book = await Book.find(id)
    book.html_content = markdown2.markdown(book.content)
    return {
        '__template__': 'book.html', 
        'book': book,
    }


@get('/schedule/{id}')
async def get_schedule(*,id):
    schedule = await Schedule.find(id)
    schedule.html_content = markdown2.markdown(schedule.schedule)
    return {
        '__template__': 'schedule.html',
        'schedule': schedule,
    }

@get('/reading/{id}')
async def get_reading(*,id):
    reading = await Reading.find(id)
    reading.html_content = markdown2.markdown(reading.content)
    return {
        '__template__': 'reading.html', 
        'reading': reading,
    }

@get('/manage/blog/edit')
def manage_edit_blog(*, id):
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id,
        'action': '/api/blog/%s' % id
    }

@get('/manage/book/edit')
def manage_edit_book(*, id):
    return {
        '__template__': 'manage_book_edit.html',
        'id': id,
        'action': '/api/book/%s' % id
    }

@get('/manage/schedule/edit')
def manage_edit_schedule(*, id):
    return {
        '__template__': 'manage_schedule_edit.html',
        'id': id,
        'action': '/api/schedule/%s' % id
    }

@get('/manage/reading/edit')
def manage_edit_reading(*, id):
    return {
        '__template__': 'manage_reading_edit.html',
        'id': id,
        'action': '/api/reading/%s' % id
    }

@post('/api/blog/{id}')
async def api_update_blog(id, request, *, name, summary, content):
    #check_admin(request)
    blog = await Blog.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    await blog.update()
    return blog

@post('/api/book/{id}')
async def api_update_book(id, request, *, name, summary, content):
    #check_admin(request)
    book = await Book.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    book.name = name.strip()
    book.summary = summary.strip()
    book.content = content.strip()
    await book.update()
    return book

@post('/api/schedule/{id}')
async def api_update_schedule(id, request, *, schedule):
    #check_admin(request)
    sche = await Schedule.find(id)
    if not schedule or not schedule.strip():
        raise APIValueError('content', 'content cannot be empty.')
    sche.schedule = schedule.strip()
    await sche.update()
    return sche

@post('/api/reading/{id}')
async def api_update_reading(id, request, *, name, author, content):
    #check_admin(request)
    reading = await Reading.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not author or not author.strip():
        raise APIValueError('author', 'author cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    reading.name = name.strip()
    reading.author = author.strip()
    reading.content = content.strip()
    await reading.update()
    return reading


@post('/api/blog/{id}/delete')
async def api_delete_blog(request, *, id):
    #check_admin(request)
    blog = await Blog.find(id)
    await blog.remove()
    return dict(id=id)

@post('/api/book/{id}/delete')
async def api_delete_book(request, *, id):
    #check_admin(request)
    book = await Book.find(id)
    await book.remove()
    return dict(id=id)

@post('/api/schedule/{id}/delete')
async def api_delete_schedule(request, *, id):
    #check_admin(request)
    schedule = await Schedule.find(id)
    await schedule.remove()
    return dict(id=id)

@post('/api/reading/{id}/delete')
async def api_delete_reading(request, *, id):
    #check_admin(request)
    reading = await Reading.find(id)
    await reading.remove()
    return dict(id=id)
