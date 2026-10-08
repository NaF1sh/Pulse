"""Isolated WinRT bridge for Windows toast notifications. Runs outside the Qt GUI process."""
import argparse
import asyncio
import json
import sys


def toast_text(toast):
    try:
        bindings = toast.visual.bindings
        if bindings.size == 0:
            return []
        elements = bindings[0].get_text_elements()
        return [' '.join(elements[index].text.split())
                for index in range(elements.size) if elements[index].text]
    except Exception:
        return []


async def sample_notification(notification):
    try:
        toast = notification.notification
        if toast is None:
            return None
        parts = toast_text(toast)
        if not parts:
            return None
        app = ''
        aumid = ''
        try:
            info = notification.app_info
            app = (info.display_info.display_name if info and info.display_info else '') or ''
            aumid = (info.app_user_model_id if info else '') or ''
        except Exception:
            pass  # AppInfo lookup is best-effort; the notification is still worth showing.
        return dict(id=notification.id, app=' '.join(app.split())[:80] or 'Windows',
                    title=parts[0][:160], body=' '.join(parts[1:])[:600], aumid=aumid[:256])
    except Exception:
        return None


async def snapshot(listener):
    from winrt.windows.ui.notifications import NotificationKinds
    notifications = await listener.get_notifications_async(NotificationKinds.TOAST)
    items = list(notifications)[:32]
    results = [await sample_notification(item) for item in items]
    return [item for item in results if item]


async def run(args):
    from winrt.windows.ui.notifications.management import (
        UserNotificationListener, UserNotificationListenerAccessStatus as Access,
    )
    listener = UserNotificationListener.current
    status = await listener.request_access_async()
    if status != Access.ALLOWED:
        if status == Access.DENIED:
            return {'error': 'Notification access denied. Allow Pulse under Settings > Privacy > '
                              'Notifications, then restart Pulse.'}
        return {'error': 'Notification access unavailable on this system.'}
    if args.remove is not None:
        listener.remove_notification(args.remove)
        return {'ok': True}
    return {'samples': await snapshot(listener)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--remove', type=int, help='clear this notification from Action Center')
    args = parser.parse_args()
    try:
        from pulse.platforms import set_app_user_model_id
        set_app_user_model_id()
        from winrt.runtime import ApartmentType, init_apartment, uninit_apartment
        init_apartment(ApartmentType.MULTI_THREADED)
        try:
            result = asyncio.run(run(args))
        finally:
            uninit_apartment()
    except ImportError:
        result = {'error': 'Windows notification dependencies are missing. Rerun install-windows.cmd '
                            'from the latest download.'}
    except Exception as exc:
        result = {'error': f'Windows notifications unavailable: {str(exc)[:300]}'}
    print(json.dumps(result, ensure_ascii=True), flush=True)
    return 1 if 'error' in result else 0


if __name__ == '__main__':
    sys.exit(main())
