# Logging Configuration for Helmax

This document explains how to view and manage logs on both development and production servers.

## Log Files Location

All logs are stored in: `helmax/logs/`

### Available Log Files:

1. **django.log** - General application logs (INFO level and above)
2. **django_errors.log** - Error logs only (ERROR level)
3. **django_debug.log** - Debug logs (only when DEBUG=True)

## Viewing Logs

### Method 1: Using Django Management Command

```bash
# View last 100 lines of general logs
python manage.py viewlogs

# View last 50 lines of error logs
python manage.py viewlogs --type errors --lines 50

# View last 200 lines of debug logs
python manage.py viewlogs --type debug --lines 200 --tail

# View all log types
python manage.py viewlogs --type all --tail --lines 100
```

### Method 2: Direct File Access

**Linux/Production Server:**
```bash
# View last 100 lines
tail -n 100 /path/to/helmax/logs/django.log

# Follow logs in real-time
tail -f /path/to/helmax/logs/django.log

# View errors only
tail -f /path/to/helmax/logs/django_errors.log

# Search for specific error
grep "ERROR" /path/to/helmax/logs/django.log
```

**Windows/Development:**
```powershell
# View last 100 lines
Get-Content helmax\logs\django.log -Tail 100

# Follow logs in real-time
Get-Content helmax\logs\django.log -Wait -Tail 50

# View errors only
Get-Content helmax\logs\django_errors.log -Tail 100
```

### Method 3: Web-based Log Viewer (Production)

Create a simple view for admins to view logs through the browser:

```python
# Add to your admin views
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
import os
from django.conf import settings

@staff_member_required
def view_logs(request):
    log_type = request.GET.get('type', 'django')
    lines = int(request.GET.get('lines', '100'))
    
    log_files = {
        'django': os.path.join(settings.LOGS_DIR, 'django.log'),
        'errors': os.path.join(settings.LOGS_DIR, 'django_errors.log'),
    }
    
    log_file = log_files.get(log_type)
    if not log_file or not os.path.exists(log_file):
        return HttpResponse('Log file not found', status=404)
    
    with open(log_file, 'r') as f:
        content = f.readlines()
        last_lines = ''.join(content[-lines:])
    
    return HttpResponse(f'<pre>{last_lines}</pre>', content_type='text/html')
```

## Log Rotation

Logs automatically rotate when they reach 10MB:
- Maximum 10 backup files for general and error logs
- Maximum 5 backup files for debug logs

Old logs are named: `django.log.1`, `django.log.2`, etc.

## Production Setup

### 1. Ensure Logs Directory Exists

```bash
mkdir -p /path/to/helmax/logs
chmod 755 /path/to/helmax/logs
```

### 2. Set Proper Permissions

```bash
# If using www-data user for web server
chown -R www-data:www-data /path/to/helmax/logs

# Or for your specific user
chown -R your_user:your_group /path/to/helmax/logs
```

### 3. Configure Log Monitoring (Optional)

**Using logrotate (Linux):**

Create `/etc/logrotate.d/helmax`:

```
/path/to/helmax/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

**Using systemd journal (Linux):**

View Django logs via systemd if running as a service:
```bash
journalctl -u helmax.service -f
```

## Logging Levels

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: Something unexpected happened, but the app still works
- **ERROR**: A serious problem occurred
- **CRITICAL**: A very serious error occurred

## Adding Logs to Your Code

```python
import logging

logger = logging.getLogger(__name__)

# In your views or functions
logger.info('User logged in successfully')
logger.warning('Low stock alert for product X')
logger.error('Payment processing failed', exc_info=True)
logger.debug(f'Processing cart: {cart_data}')
```

## Monitoring in Production

### Real-time Monitoring:

```bash
# Watch all logs
tail -f /path/to/helmax/logs/*.log

# Watch only errors
tail -f /path/to/helmax/logs/django_errors.log
```

### Log Analysis:

```bash
# Count errors by type
grep "ERROR" django.log | cut -d' ' -f4 | sort | uniq -c

# Find all 500 errors
grep "500" django.log

# Check last hour of logs
find logs/ -name "*.log" -mmin -60 -exec tail -f {} +
```

## Troubleshooting

### Logs Not Being Created?

1. Check directory permissions:
   ```bash
   ls -la /path/to/helmax/logs/
   ```

2. Verify settings.py has LOGGING configuration

3. Restart your web server:
   ```bash
   sudo systemctl restart gunicorn
   # or
   sudo systemctl restart apache2
   ```

### Log Files Too Large?

1. Check current size:
   ```bash
   du -sh logs/
   ```

2. Manually rotate:
   ```bash
   mv django.log django.log.old
   touch django.log
   sudo systemctl restart gunicorn
   ```

3. Clear old logs:
   ```bash
   find logs/ -name "*.log.*" -mtime +30 -delete
   ```

## Security Notes

- ⚠️ Never commit log files to version control (already in .gitignore)
- ⚠️ Restrict log file access to admin users only
- ⚠️ Sanitize sensitive data before logging (passwords, tokens, etc.)
- ⚠️ Regular review error logs for security issues

## Emergency Access

If you need to quickly check what's wrong on production:

```bash
# SSH into server
ssh user@your-server.com

# Navigate to project
cd /path/to/helmax

# Check last errors
tail -n 50 logs/django_errors.log

# Check if service is running
sudo systemctl status gunicorn

# View service logs
journalctl -u gunicorn -n 100
```
