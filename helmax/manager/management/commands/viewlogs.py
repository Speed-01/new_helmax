from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'View application logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='django',
            help='Log type to view: django, errors, debug, all'
        )
        parser.add_argument(
            '--lines',
            type=int,
            default=100,
            help='Number of lines to display (default: 100)'
        )
        parser.add_argument(
            '--tail',
            action='store_true',
            help='Show only the last lines'
        )

    def handle(self, *args, **options):
        log_type = options['type']
        lines = options['lines']
        tail = options['tail']

        logs_dir = settings.LOGS_DIR
        
        log_files = {
            'django': os.path.join(logs_dir, 'django.log'),
            'errors': os.path.join(logs_dir, 'django_errors.log'),
            'debug': os.path.join(logs_dir, 'django_debug.log'),
        }

        if log_type == 'all':
            files_to_show = log_files.items()
        elif log_type in log_files:
            files_to_show = [(log_type, log_files[log_type])]
        else:
            self.stdout.write(self.style.ERROR(f'Invalid log type: {log_type}'))
            self.stdout.write('Available types: django, errors, debug, all')
            return

        for log_name, log_file in files_to_show:
            if not os.path.exists(log_file):
                self.stdout.write(self.style.WARNING(f'{log_name.upper()} LOG: File not found'))
                continue

            self.stdout.write(self.style.SUCCESS(f'\n{"="*80}'))
            self.stdout.write(self.style.SUCCESS(f'{log_name.upper()} LOG: {log_file}'))
            self.stdout.write(self.style.SUCCESS(f'{"="*80}\n'))

            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    if tail:
                        # Read last N lines
                        content = f.readlines()
                        display_lines = content[-lines:] if len(content) > lines else content
                    else:
                        # Read first N lines
                        display_lines = []
                        for i, line in enumerate(f):
                            if i >= lines:
                                break
                            display_lines.append(line)
                    
                    for line in display_lines:
                        self.stdout.write(line.rstrip())
                
                # Show file stats
                file_size = os.path.getsize(log_file)
                self.stdout.write(f'\n\nFile size: {file_size / 1024:.2f} KB')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error reading log: {str(e)}'))
