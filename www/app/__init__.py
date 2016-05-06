#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-05-05 14:32:46
# @Author  : moling (365024424@qq.com)
# @Link    : #
# @Version : 0.1
import logging, os
from aiohttp import web
from jinja2 import Environment, FileSystemLoader

from config import COOKIE_NAME, COOKIE_KEY
from app.frame import add_routes, add_static
from app.frame.orm import create_pool
from app.factorys import logger_factory, auth_factory, response_factory, datetime_filter


logging.basicConfig(level=logging.INFO)

def init_jinja2(app, **kw):
    logging.info('init jinja2...')
    options = dict(
        autoescape = kw.get('autoescape', True),
        block_start_string = kw.get('block_start_string', '{%'),
        block_end_string = kw.get('block_end_string', '%}'),
        variable_start_string = kw.get('variable_start_string', '{{'),
        variable_end_string = kw.get('variable_end_string', '}}'),
        auto_reload = kw.get('auto_reload', True)
    )
    path = kw.get('path', os.path.join(__path__[0], 'templates'))
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters')
    if filters is not None:
        for name, ftr in filters.items():
            env.filters[name] = ftr
    app['__templating__'] = env

async def create_server(loop, config_mod):
    try:
        config = __import__(config_mod, fromlist=['get_config'])
    except ImportError as e:
        raise e

    await create_pool(loop, **config.db_config)
    app = web.Application(loop=loop, middlewares=[
        logger_factory, auth_factory, response_factory])
    for mod in config.modules:
        add_routes(app, mod)
    add_static(app)
    init_jinja2(app, filters=dict(datetime=datetime_filter), **config.jinja2_config)
    server = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return server