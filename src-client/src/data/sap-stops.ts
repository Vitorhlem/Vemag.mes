export interface SapStopReason {
  code: string;
  label: string;
  category: 'Operacional' | 'Manutenção' | 'Qualidade' | 'Logística' | 'Pessoal' | 'Outros';
  requiresMaintenance: boolean; 
  isProductive: boolean;
  isSpecial?: boolean; 
}

export const SAP_STOP_REASONS: SapStopReason[] = [
  // --- ITENS MANTIDOS (CONFORME SOLICITADO) ---
  { code: '52', label: 'Preparação / Setup', category: 'Operacional', requiresMaintenance: false, isProductive: false, isSpecial: true }, // ✅ NOVO
  { code: '111', label: 'Troca de Turno', category: 'Operacional', requiresMaintenance: false, isProductive: false, isSpecial: true },
  { code: '21', label: 'Manutenção / Conserto', category: 'Manutenção', requiresMaintenance: true, isProductive: false, isSpecial: true },

  // --- OPERACIONAL / PRODUÇÃO (LISTA SAP) ---
  { code: '42', label: 'Elaboração de Programa CNC', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '22', label: 'Falta de Energia Elétrica', category: 'Operacional', requiresMaintenance: false, isProductive: false },
  { code: '28', label: 'Aguardando Serviço', category: 'Operacional', requiresMaintenance: false, isProductive: false },
  { code: '38', label: 'Assistência do Cliente', category: 'Operacional', requiresMaintenance: false, isProductive: false },
  { code: '60005', label: 'Fabricação de dispositivos', category: 'Operacional', requiresMaintenance: false, isProductive: true },

  // --- LOGÍSTICA ---
  { code: '20', label: 'Aguardando ponte rolante', category: 'Logística', requiresMaintenance: false, isProductive: false },
  { code: '23', label: 'Aguardando ferramenta/instrumento', category: 'Logística', requiresMaintenance: false, isProductive: false },
  { code: '24', label: 'Aguardando informação técnica', category: 'Logística', requiresMaintenance: false, isProductive: false },
  { code: '26', label: 'Aguardando peça/material', category: 'Logística', requiresMaintenance: false, isProductive: false },

  // --- QUALIDADE ---
  { code: '25', label: 'Aguardando inspeção', category: 'Qualidade', requiresMaintenance: false, isProductive: false },
  { code: '27', label: 'Arrumação/limpeza', category: 'Qualidade', requiresMaintenance: false, isProductive: true },
  { code: '39', label: 'Rastreabilidade de materiais', category: 'Qualidade', requiresMaintenance: false, isProductive: true },
  { code: '40', label: 'Organização de Instrumentos', category: 'Qualidade', requiresMaintenance: false, isProductive: true },

  // --- PESSOAL / MANUTENÇÃO EXTRA ---
  { code: '30', label: 'Treinamento', category: 'Pessoal', requiresMaintenance: false, isProductive: true },
  { code: '31', label: 'Exame médico', category: 'Pessoal', requiresMaintenance: false, isProductive: false },
  { code: '34', label: 'Manutenção predial', category: 'Manutenção', requiresMaintenance: false, isProductive: false },
  { code: '50', label: 'Particular Vanderci Escudeiro', category: 'Pessoal', requiresMaintenance: false, isProductive: false },
  { code: '51', label: 'Particular Cesar Valochi', category: 'Pessoal', requiresMaintenance: false, isProductive: false },

  // --- GENÉRICO ---
  { code: '999', label: 'Outros Motivos', category: 'Outros', requiresMaintenance: false, isProductive: false }
];