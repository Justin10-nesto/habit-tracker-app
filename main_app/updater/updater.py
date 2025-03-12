from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore 
from .scheduler import check_and_send_notifications, check_missed_habits
from apscheduler.triggers.cron import CronTrigger

_scheduler = None

def start():
    from django.apps import apps
    if not apps.ready:
        return
        
    global _scheduler
    if _scheduler is not None:
        return
        
    _scheduler = BackgroundScheduler()
    _scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Run daily at 00:01 to check for habits that were missed yesterday
    _scheduler.add_job(
        check_missed_habits,
        trigger=CronTrigger(hour=0, minute=1),
        id="check_missed_habits",
        max_instances=1,
        replace_existing=True,
    )
    
    _scheduler.add_job(
        check_and_send_notifications,
        trigger=CronTrigger(second=0),
        id="check_and_send_notifications",
        max_instances=1,
        replace_existing=True,
    )
    
    _scheduler.start()
