# Production Logging Setup - Quick Reference

## Initial Setup on Production Server

```bash
# 1. Create logs directory
cd /path/to/helmax
mkdir -p logs
chmod 755 logs

# 2. Set ownership (adjust user as needed)
chown -R www-data:www-data logs

# 3. Test logging
python manage.py shell
>>> import logging
>>> logger = logging.getLogger('django')
>>> logger.info('Test log message')
>>> exit()

# 4. Verify log file was created
ls -lh logs/
cat logs/django.log
```

## Quick Commands

### View Logs via Management Command
```bash
# View last 100 lines of general logs
python manage.py viewlogs

# View errors only
python manage.py viewlogs --type errors --tail --lines 50

# View debug logs
python manage.py viewlogs --type debug --tail --lines 100
```

### View Logs via Command Line
```bash
# Real-time monitoring
tail -f logs/django.log

# View errors only
tail -f logs/django_errors.log

# Last 100 lines
tail -n 100 logs/django.log

# Search for specific error
grep "ERROR" logs/django.log | tail -20
```

### Web-Based Log Viewer
Access: `https://yourdomain.com/manager/logs/`
- Staff members only
- View, download, and clear logs
- Syntax highlighting

## systemd Service Integration

If running Django with systemd (recommended):

```bash
# View service logs
journalctl -u helmax -f

# View last 100 lines
journalctl -u helmax -n 100

# View errors only
journalctl -u helmax -p err
```

## Common Issues

### Logs not being created?
```bash
# Check permissions
ls -la logs/

# Check settings
python manage.py shell
>>> from django.conf import settings
>>> print(settings.LOGS_DIR)
>>> import os
>>> print(os.path.exists(settings.LOGS_DIR))

# Restart service
sudo systemctl restart gunicorn
```

### Disk space issues?
```bash
# Check log sizes
du -sh logs/*

# Rotate logs manually
cd logs
mv django.log django.log.old
mv django_errors.log django_errors.log.old
sudo systemctl restart gunicorn

# Auto-cleanup old logs (older than 30 days)
find logs/ -name "*.log.*" -mtime +30 -delete
```

## Monitoring Setup (Optional)

### Using cron for daily log reports
```bash
# Edit crontab
crontab -e

# Add daily error report at 9 AM
0 9 * * * cd /path/to/helmax && python manage.py viewlogs --type errors --tail --lines 50 | mail -s "Daily Error Report" admin@example.com
```

### Using logrotate
```bash
# Create /etc/logrotate.d/helmax
sudo nano /etc/logrotate.d/helmax

# Add:
/path/to/helmax/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload gunicorn > /dev/null 2>&1 || true
    endscript
}

# Test logrotate
sudo logrotate -d /etc/logrotate.d/helmax
```

## Security Checklist

- [ ] Logs directory permissions set correctly (755)
- [ ] Log files not in version control (.gitignore updated)
- [ ] Web log viewer restricted to staff only
- [ ] Sensitive data sanitized before logging
- [ ] Regular log rotation configured
- [ ] Disk space monitoring enabled
- [ ] Admin email notifications for critical errors configured

## Performance Tips

1. **Don't log in tight loops** - Can impact performance
2. **Use appropriate log levels** - DEBUG only in development
3. **Rotate logs regularly** - Prevents disk space issues
4. **Monitor log file sizes** - Set up alerts for large files
5. **Use async logging for high-traffic sites** - Consider celery for log processing

## Emergency Access

```bash
# SSH into server
ssh user@your-server.com

# Quick status check
cd /path/to/helmax
tail -n 20 logs/django_errors.log

# Check if service is running
sudo systemctl status gunicorn

# View real-time errors
tail -f logs/django_errors.log | grep ERROR

# Restart if needed
sudo systemctl restart gunicorn
```

## Contact

For issues with logging setup, check LOGGING.md for detailed documentation.
