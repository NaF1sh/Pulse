"""Isolated WinRT bridge. All Windows calls run outside the Qt GUI process."""
import argparse
import asyncio
from array import array
import base64
import json
import sys


async def thumbnail_url(reference):
    if reference is None:
        return ''
    from winrt.windows.storage.streams import DataReader
    stream = await reference.open_read_async()
    try:
        size = stream.size
        if not 0 < size <= 1024 * 1024:
            return ''
        reader = DataReader(stream)
        try:
            loaded = await reader.load_async(size)
            data = array('B', [0]) * loaded
            reader.read_bytes(data)
            mime = stream.content_type
            if mime not in ('image/jpeg', 'image/png', 'image/webp'):
                return ''
            return f'data:{mime};base64,' + base64.b64encode(data).decode('ascii')
        finally:
            reader.detach_stream()
            reader.close()
    finally:
        stream.close()


async def sample_session(session):
    info = session.get_playback_info()
    status = info.playback_status.name
    if status not in ('PLAYING', 'PAUSED'):
        return None
    props = await asyncio.wait_for(session.try_get_media_properties_async(), 1.5)
    title = ' '.join(props.title.split())[:160]
    if not title:
        return None
    artwork = ''
    try:
        artwork = await asyncio.wait_for(thumbnail_url(props.thumbnail), 1)
    except Exception:
        pass  # An unavailable cover must never hide the track.
    caps = info.controls
    return dict(service=session.source_app_user_model_id, title=title,
                artist=' '.join(props.artist.split())[:400], track=title,
                status='Playing' if status == 'PLAYING' else 'Paused', artwork=artwork,
                capabilities=dict(CanControl=True, CanPlay=caps.is_play_enabled or caps.is_play_pause_toggle_enabled,
                                  CanPause=caps.is_pause_enabled or caps.is_play_pause_toggle_enabled,
                                  CanGoNext=caps.is_next_enabled,
                                  CanGoPrevious=caps.is_previous_enabled))


async def snapshot(manager):
    sessions = list(manager.get_sessions())[:8]
    results = await asyncio.gather(*(sample_session(s) for s in sessions), return_exceptions=True)
    samples = [item for item in results if isinstance(item, dict)]
    # A closing player may fail independently of the others.
    if results and all(isinstance(item, BaseException) for item in results):
        raise RuntimeError('Windows players did not provide their media information.')
    current = manager.get_current_session()
    current_id = current.source_app_user_model_id if current else ''
    samples.sort(key=lambda item: item['service'] != current_id)
    return samples


async def control(manager, service, action):
    matches = [s for s in manager.get_sessions() if s.source_app_user_model_id == service]
    if len(matches) != 1:
        raise RuntimeError('The selected player closed or is ambiguous. Try again.')
    session = matches[0]
    info = session.get_playback_info()
    method, flag = {'previous': ('try_skip_previous_async', 'is_previous_enabled'),
                    'next': ('try_skip_next_async', 'is_next_enabled'),
                    'toggle': ('try_pause_async', 'is_pause_enabled') if info.playback_status.name == 'PLAYING'
                    else ('try_play_async', 'is_play_enabled')}[action]
    if action == 'toggle' and not getattr(info.controls, flag) and info.controls.is_play_pause_toggle_enabled:
        method, flag = 'try_toggle_play_pause_async', 'is_play_pause_toggle_enabled'
    if not getattr(info.controls, flag) or not await asyncio.wait_for(getattr(session, method)(), 2):
        raise RuntimeError('The player did not accept this control.')


async def run(args):
    from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager
    manager = await asyncio.wait_for(GlobalSystemMediaTransportControlsSessionManager.request_async(), 3)
    if args.action:
        await control(manager, args.service, args.action)
        return {'ok': True}
    return {'samples': await snapshot(manager)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', choices=('toggle', 'previous', 'next'))
    parser.add_argument('--service', default='')
    args = parser.parse_args()
    try:
        from winrt.runtime import ApartmentType, init_apartment, uninit_apartment
        init_apartment(ApartmentType.MULTI_THREADED)
        try:
            result = asyncio.run(run(args))
        finally:
            uninit_apartment()
    except ImportError:
        result = {'error': 'Windows music dependencies are missing. Rerun install-windows.cmd from the latest download.'}
    except Exception as exc:
        result = {'error': f'Windows media unavailable: {str(exc)[:300]}'}
    print(json.dumps(result, ensure_ascii=True), flush=True)
    return 1 if 'error' in result else 0


if __name__ == '__main__':
    sys.exit(main())
