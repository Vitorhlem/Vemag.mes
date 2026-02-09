import Dexie, { type Table } from 'dexie';

export interface SyncQueueItem {
  id?: number;
  type: 'APPOINTMENT' | 'EVENT';
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  payload: any;
  timestamp: string;
  status: 'pending' | 'syncing';
}

export interface OrderCache {
  code: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any;
  last_updated: string;
}

export class VemagOfflineDB extends Dexie {
  sync_queue!: Table<SyncQueueItem>;
  orders_cache!: Table<OrderCache>;

  constructor() {
    super('VemagOfflineDB');
    this.version(1).stores({
      sync_queue: '++id, type, status',
      orders_cache: 'code'
    });
  }
}

export const db = new VemagOfflineDB();