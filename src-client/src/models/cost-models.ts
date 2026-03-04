export interface IMachineCost {
  id: number;
  cost_type: string;
  amount: number;
  date: string;
  notes?: string;
  machine_id: number;
}

export interface MachineCost {
  id: number;
  machine_id: number;
  cost_type: string;
  amount: number;
  date: string;
  notes?: string;
}

export type ICostCreate = Omit<IMachineCost, 'id'>;