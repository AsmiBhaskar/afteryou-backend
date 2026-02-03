"""
Management command to process pending legacy message deliveries
"""
from django.core.management.base import BaseCommand
from legacy.email_service import LegacyEmailService

class Command(BaseCommand):
    help = 'Process pending legacy message deliveries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--message-id',
            type=str,
            help='Send a specific message by ID',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Send test version of the message',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show delivery statistics',
        )

    def handle(self, *args, **options):
        if options['stats']:
            stats = LegacyEmailService.get_delivery_stats()
            self.stdout.write(f"Delivery Statistics:")
            self.stdout.write(f"  Total messages: {stats['total']}")
            self.stdout.write(f"  Scheduled: {stats['scheduled']}")
            self.stdout.write(f"  Sent: {stats['sent']}")
            self.stdout.write(f"  Failed: {stats['failed']}")
            self.stdout.write(f"  Created: {stats['created']}")
            self.stdout.write(f"  Delivery rate: {stats['delivery_rate']:.1f}%")
            return

        message_id = options.get('message_id')
        is_test = options.get('test', False)

        if message_id:
            if is_test:
                success = LegacyEmailService.send_test_message(message_id)
                action = "Test message sent" if success else "Failed to send test message"
            else:
                success = LegacyEmailService.send_legacy_message(message_id)
                action = "Message sent" if success else "Failed to send message"
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'{action} for message {message_id}'))
            else:
                self.stdout.write(self.style.ERROR(f'{action} for message {message_id}'))
        else:
            # Process all pending deliveries
            results = LegacyEmailService.process_pending_deliveries()
            
            if 'error' in results:
                self.stdout.write(self.style.ERROR(f'Error: {results["error"]}'))
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Processed {results["total_processed"]} messages: '
                        f'{results["successful"]} successful, {results["failed"]} failed'
                    )
                )
