from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import os


@staff_member_required
def view_logs(request):
    """Web-based log viewer for admin users"""
    log_type = request.GET.get('type', 'django')
    lines = int(request.GET.get('lines', '100'))
    download = request.GET.get('download', 'false') == 'true'
    
    log_files = {
        'django': os.path.join(settings.LOGS_DIR, 'django.log'),
        'errors': os.path.join(settings.LOGS_DIR, 'django_errors.log'),
        'debug': os.path.join(settings.LOGS_DIR, 'django_debug.log'),
    }
    
    log_file = log_files.get(log_type)
    
    if not log_file or not os.path.exists(log_file):
        return HttpResponse('Log file not found', status=404)
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.readlines()
            last_lines = content[-lines:] if len(content) > lines else content
            log_content = ''.join(last_lines)
        
        # Get file stats
        file_size = os.path.getsize(log_file) / 1024  # KB
        file_lines = len(content)
        
        if download:
            response = HttpResponse(log_content, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="{log_type}.log"'
            return response
        
        context = {
            'log_content': log_content,
            'log_type': log_type,
            'lines': lines,
            'file_size': f'{file_size:.2f}',
            'total_lines': file_lines,
            'available_types': list(log_files.keys()),
        }
        
        return render(request, 'admin/view_logs.html', context)
        
    except Exception as e:
        return HttpResponse(f'Error reading log: {str(e)}', status=500)


@staff_member_required
def clear_logs(request):
    """Clear log files (admin only)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method required'})
    
    log_type = request.POST.get('type', 'django')
    
    log_files = {
        'django': os.path.join(settings.LOGS_DIR, 'django.log'),
        'errors': os.path.join(settings.LOGS_DIR, 'django_errors.log'),
        'debug': os.path.join(settings.LOGS_DIR, 'django_debug.log'),
    }
    
    log_file = log_files.get(log_type)
    
    if not log_file or not os.path.exists(log_file):
        return JsonResponse({'success': False, 'message': 'Log file not found'})
    
    try:
        # Clear the file
        open(log_file, 'w').close()
        return JsonResponse({'success': True, 'message': f'{log_type} log cleared successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
