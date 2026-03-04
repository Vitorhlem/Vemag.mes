export type CostType = 
  | 'Manutenção Corretiva'
  | 'Manutenção Preventiva'
  | 'Energia Elétrica'
  | 'Peças de Reposição'
  | 'Insumos/Consumíveis'
  | 'Serviços Terceiros'
  | 'Outros'
  | 'Manutenção' 
  | 'Seguro';

export interface MachineCost {
  id: number;
  machine_id: number;
  cost_type: CostType;
  amount: number;
  date: string;
  description?: string;
  created_at?: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  machine?: any; 
}

export interface MachineCostCreate {
  cost_type: CostType;
  amount: number;
  date: string; 
  description: string;
}