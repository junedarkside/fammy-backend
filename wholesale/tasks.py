# from celery import shared_task
# from django.utils import timezone
# from .models import Wholesaler
# from  .data_sync_service import DataSyncService
# import logging

# logger = logging.getLogger(__name__)


# @shared_task
# def sync_wholesaler_data(wholesaler_id: int):
#     """Celery task to sync data for a specific wholesaler"""
#     try:
#         wholesaler = Wholesaler.objects.get(id=wholesaler_id, is_active=True)
#         sync_service = DataSyncService(wholesaler)
        
#         # Check for updates first
#         if not sync_service.check_for_updates():
#             logger.info(f'No updates available for {wholesaler.name}')
#             return f'No updates for {wholesaler.name}'
        
#         # Sync countries
#         countries_result = sync_service.sync_countries()
        
#         # Sync program tours
#         tours_result = sync_service.sync_program_tours()
        
#         result = {
#             'wholesaler': wholesaler.name,
#             'timestamp': timezone.now().isoformat(),
#             'countries': countries_result,
#             'tours': tours_result
#         }
        
#         logger.info(f'Sync completed for {wholesaler.name}: {result}')
#         return result
        
#     except Wholesaler.DoesNotExist:
#         logger.error(f'Wholesaler with id {wholesaler_id} not found')
#         return f'Wholesaler {wholesaler_id} not found'
#     except Exception as e:
#         logger.error(f'Error syncing wholesaler {wholesaler_id}: {str(e)}')
#         return f'Error: {str(e)}'


# @shared_task
# def sync_all_wholesalers():
#     """Celery task to sync data for all active wholesalers"""
#     wholesalers = Wholesaler.objects.filter(is_active=True)
#     results = []
    
#     for wholesaler in wholesalers:
#         result = sync_wholesaler_data.delay(wholesaler.id)
#         results.append({
#             'wholesaler_id': wholesaler.id,
#             'task_id': result.id
#         })
    
#     return results