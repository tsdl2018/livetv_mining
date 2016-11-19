# -*- coding: UTF-8 -*-
from flask import request, current_app, url_for
from flask_restful import abort

from ..models import LiveTVSite, LiveTVChannel, LiveTVRoom
from . import main_api, Resource


class MainApiMixin(object):

    @classmethod
    def _format_site(cls, site):
        return {
            'id': site.id,
            'name': site.name,
            'code': site.code,
            'url': site.url,
            'image': site.image,
            'description': site.description,
            'link': {
                'detail': url_for('main.site_detail', site_id=site.id)
            },
            'rest': {
                'channel': main_api.url_for(ChannelMultiple, site_id=site.id),
                'room': main_api.url_for(RoomMultiple, site_id=site.id)
            }
        }

    @classmethod
    def _format_channel(cls, channel):
        return {
            'id': channel.id,
            'office_id': channel.office_id,
            'short': channel.short,
            'name': channel.name,
            'url': channel.url,
            'image': channel.image,
            'total': channel.total,
            'crawl_date': channel.crawl_date.strftime('%Y-%m-%d %H:%M:%S'),
            'site': channel.site.name,
            'link': {
                'detail': url_for('main.channel_detail', channel_id=channel.id),
                'site': url_for('main.site_detail', site_id=channel.site_id)
            },
            'rest': {
                'room': main_api.url_for(RoomMultiple, channel_id=channel.id)
            }
        }

    @classmethod
    def _format_room(cls, room):
        return {
            'id': room.id,
            'office_id': room.office_id,
            'name': room.name,
            'url': room.url,
            'image': room.image,
            'online': room.online,
            'opened': room.opened,
            'host': room.host,
            'crawl_date': room.crawl_date.strftime('%Y-%m-%d %H:%M:%S'),
            'channel': room.channel.name,
            'site': room.site.name,
            'link': {
                'detail': url_for('main.room_detail', room_id=room.id),
                'site': url_for('main.site_detail', site_id=room.site_id),
                'channel': url_for('main.channel_detail', channel_id=room.channel_id)
            }
        }

    @classmethod
    def _format_pagination(cls, pagination):
        if pagination.has_next:
            links_to = pagination.page * pagination.per_page
        else:
            links_to = pagination.total - (pagination.page - 1) * pagination.per_page
        return {
            'links': {
                'pagination': {
                    'total': pagination.total,
                    'per_page': pagination.per_page,
                    'current_page': pagination.page,
                    'last_page': pagination.pages,
                    'from': (pagination.page - 1) * pagination.per_page + 1,
                    'to': links_to
                }
            }
        }


@main_api.resource('/site')
class SiteMultiple(Resource, MainApiMixin):

    def get(self):
        site_query = LiveTVSite.query.filter_by(valid=True).order_by(LiveTVSite.show_seq.asc())
        return [self._format_site(site) for site in site_query.all()]


@main_api.resource('/site/<int:site_id>')
class Site(Resource, MainApiMixin):

    def get(self, site_id):
        site = LiveTVSite.query.filter_by(id=site_id).one_or_none()
        if not site:
            abort(400, message='Can not find site by site_id {}'.format(str(site_id)))
        site_dict = self._format_site(site)
        site_dict['channel_total'] = site.channels.filter_by(valid=True).count()
        site_dict['room_total'] = site.rooms.filter_by(opened=True).count()
        return site_dict


@main_api.resource('/site/<int:site_id>/channel')
class ChannelMultiple(Resource, MainApiMixin):

    def get(self, site_id):
        isvue = request.args.get('isvue', False, type=bool)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', current_app.config['FLASK_CHANNEL_PER_PAGE'], type=int)
        channel_query = LiveTVChannel.query.filter_by(site_id=site_id).filter_by(valid=True)
        pagination = channel_query.order_by(LiveTVChannel.total.desc()) \
                                  .paginate(page=page, error_out=False, per_page=per_page)
        pagiitems = [self._format_channel(item) for item in pagination.items]
        if isvue:
            return dict(self._format_pagination(pagination), data=pagiitems)
        else:
            return pagiitems


@main_api.resource('/site/<int:site_id>/channel/<int:channel_id>',
                   '/channel/<int:channel_id>')
class Channel(Resource, MainApiMixin):

    def get(self, channel_id, site_id=None):
        channel_query = LiveTVChannel.query.filter_by(id=channel_id)
        if site_id:
            channel_query = channel_query.filter_by(site_id=site_id)
        channel = channel_query.one_or_none()
        if not channel:
            abort(400, message='Can not find channel record by channel: {}.'.format(str(channel_id)))
        return self._format_channel(channel)


@main_api.resource('/site/<int:site_id>/channel/<int:channel_id>/room',
                   '/site/<int:site_id>/room',
                   '/channel/<int:channel_id>/room')
class RoomMultiple(Resource, MainApiMixin):

    def get(self, site_id=None, channel_id=None):
        isvue = request.args.get('isvue', False, type=bool)
        page = request.args.get('page', 1, type=int)
        name = request.args.get('name', '', type=str)
        host = request.args.get('host', '', type=str)
        per_page = request.args.get('per_page', current_app.config['FLASK_ROOM_PER_PAGE'], type=int)
        room_query = LiveTVRoom.query.filter_by(opened=True)
        if site_id:
            room_query = room_query.filter_by(site_id=site_id)
        if channel_id:
            room_query = room_query.filter_by(channel_id=channel_id)
        if name:
            room_query = room_query.filter(LiveTVRoom.name.like('%{}%'.format(name)))
        if host:
            room_query = room_query.filter(LiveTVRoom.host.like('%{}%'.format(host)))
        pagination = room_query.order_by(LiveTVRoom.online.desc()) \
            .paginate(page=page, error_out=False, per_page=per_page)
        pagiitems = [self._format_room(item) for item in pagination.items]
        if isvue:
            return dict(self._format_pagination(pagination), data=pagiitems)
        else:
            return pagiitems


@main_api.resource('/site/<int:site_id>/channel/<int:channel_id>/room/<int:room_id>',
                   '/site/<int:site_id>/room/<int:room_id>',
                   '/channel/<int:channel_id>/room/<int:room_id>',
                   '/room/<int:room_id>')
class Room(Resource, MainApiMixin):

    def get(self, room_id, site_id=None, channel_id=None):
        room_query = LiveTVRoom.query.filter_by(id=room_id)
        if site_id:
            room_query = room_query.filter_by(site_id=site_id)
        if channel_id:
            room_query = room_query.filter_by(channel_id=channel_id)
        room = room_query.one_or_none()
        if not room:
            abort(400, message='Can not find room record by room: {}.'.format(str(room_id)))
        roomdict = self._format_room(room)
        roomdict['median'] = room.median
        return roomdict
