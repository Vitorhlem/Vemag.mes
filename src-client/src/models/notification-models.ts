export interface Notification {
  id: number;
  message: string;
  is_read: boolean;
  created_at: string; 
  related_machine_id?: number;
  

  notification_type: 
    | 'maintenance_due_date'
    | 'document_expiring'
    | 'low_stock'
    | 'cost_exceeded'
    | 'maintenance_request_new'
    | 'maintenance_request_status_update'
    | 'maintenance_request_new_comment'
    | (string & {}); 

  related_entity_type?: string; 
  related_entity_id?: number; 
}

export interface NotificationCreate {
  message: string;
  related_machine_id?: number;
  notification_type?: string;
}