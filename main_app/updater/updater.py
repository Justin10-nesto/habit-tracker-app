from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore 
from .scheduler import check_and_send_notifications, check_missed_habits
from apscheduler.triggers.cron import CronTrigger

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Run daily at 00:01 to check for habits that were missed yesterday
    scheduler.add_job(
        check_missed_habits,
        trigger=CronTrigger(hour=0, minute=1),
        id="check_missed_habits",
        max_instances=1,
        replace_existing=True,
    )
    
    scheduler.add_job(
        check_and_send_notifications,
        trigger=CronTrigger(second=0),
        id="check_and_send_notifications",
        max_instances=1,
        replace_existing=True,
    )
    
    scheduler.start()
