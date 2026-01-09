export type CostType = 
  | 'Manutenção Corretiva'
  | 'Manutenção Preventiva'
  | 'Energia Elétrica'
  | 'Peças de Reposição'
  | 'Insumos/Consumíveis'
  | 'Serviços Terceiros'
  | 'Outros'
  // Mantemos os antigos apenas para não quebrar dados legados se existirem no banco
  | 'Manutenção' 
  | 'Combustível' 
  | 'Pedágio' 
  | 'Seguro' 
  | 'Pneu';

export interface VehicleCost {
  id: number;
  vehicle_id: number;
  cost_type: CostType;
  amount: number;
  date: string;
  description?: string;
  created_at?: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  vehicle?: any; 
}

export interface VehicleCostCreate {
  cost_type: CostType;
  amount: number;
  date: string; // YYYY-MM-DD
  description: string;
}