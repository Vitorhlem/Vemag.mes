export interface SapStopReason {
  code: string;
  label: string;
  category: 'Operacional' | 'Manutenção' | 'Qualidade' | 'Logística' | 'Pessoal' | 'Outros';
  requiresMaintenance: boolean; 
  isProductive: boolean;
  isSpecial?: boolean; 
}

export const SAP_STOP_REASONS: SapStopReason[] = [
  // --- ESPECIAIS (Destaque Visual) ---
  { code: '111', label: 'Troca de Turno', category: 'Operacional', requiresMaintenance: false, isProductive: false, isSpecial: true },
  { code: '21', label: 'Manutenção / Conserto', category: 'Manutenção', requiresMaintenance: true, isProductive: false, isSpecial: true },

  // --- PRODUÇÃO / SETUP ---
  { code: '100', label: 'Setup / Preparação', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '101', label: 'Ajuste de Parâmetros', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '112', label: 'Reunião / DDS', category: 'Operacional', requiresMaintenance: false, isProductive: true },

  // --- LOGÍSTICA ---
  { code: '26', label: 'Aguardando Material', category: 'Logística', requiresMaintenance: false, isProductive: false },
  { code: '20', label: 'Aguardando Ponte', category: 'Logística', requiresMaintenance: false, isProductive: false },
  { code: '504', label: 'Aguardando PCP', category: 'Logística', requiresMaintenance: false, isProductive: false },
  { code: '24', label: 'Informação Técnica', category: 'Logística', requiresMaintenance: false, isProductive: false },

  // --- QUALIDADE ---
  { code: '25', label: 'Aguardando Inspeção', category: 'Qualidade', requiresMaintenance: false, isProductive: false },
  { code: '401', label: 'Inspeção 1ª Peça', category: 'Qualidade', requiresMaintenance: false, isProductive: true },
  { code: '27', label: 'Limpeza / 5S', category: 'Qualidade', requiresMaintenance: false, isProductive: true },

  // --- PESSOAL / OUTROS ---
  { code: '600', label: 'Refeição / Café', category: 'Pessoal', requiresMaintenance: false, isProductive: false },
  { code: '30', label: 'Treinamento', category: 'Pessoal', requiresMaintenance: false, isProductive: true },
  { code: '999', label: 'Outros Motivos', category: 'Outros', requiresMaintenance: false, isProductive: false }
];