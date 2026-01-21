// Arquivo: src-client/src/data/sap-stops.ts

export interface SapStopReason {
  code: string;
  label: string;
  category: 'Geral' | 'Operacional' | 'Mecânica' | 'Elétrica' | 'Qualidade' | 'Logística' | 'Pessoal' | 'Outros';
  requiresMaintenance?: boolean; // TRUE = Aciona fluxo de quebra/O.M.
}

export const SAP_STOP_REASONS: SapStopReason[] = [
  // --- LISTA SAP ORIGINAL ---
  { code: '20', label: 'Aguardando ponte rolante', category: 'Logística', requiresMaintenance: false },
  { code: '21', label: 'Máquina em manutenção', category: 'Mecânica', requiresMaintenance: true }, // CRÍTICO
  { code: '22', label: 'Falta de energia elétrica', category: 'Geral', requiresMaintenance: true }, // Crítico externo
  { code: '23', label: 'Aguardando ferramenta/instrumento', category: 'Logística', requiresMaintenance: false },
  { code: '24', label: 'Aguardando informação técnica', category: 'Operacional', requiresMaintenance: false },
  { code: '25', label: 'Aguardando inspeção', category: 'Qualidade', requiresMaintenance: false },
  { code: '26', label: 'Aguardando peça/material', category: 'Logística', requiresMaintenance: false },
  { code: '27', label: 'Arrumação/limpeza', category: 'Geral', requiresMaintenance: false },
  { code: '28', label: 'Aguardando serviço', category: 'Operacional', requiresMaintenance: false },
  { code: '30', label: 'Treinamento', category: 'Pessoal', requiresMaintenance: false },
  { code: '31', label: 'Exame médico', category: 'Pessoal', requiresMaintenance: false },
  { code: '34', label: 'Manutenção predial', category: 'Geral', requiresMaintenance: false },
  { code: '38', label: 'Assistência do cliente', category: 'Operacional', requiresMaintenance: false },
  { code: '39', label: 'Rastreabilidade de materiais', category: 'Qualidade', requiresMaintenance: false },
  { code: '40', label: 'Organização de Instrumentos', category: 'Geral', requiresMaintenance: false },
  { code: '42', label: 'Elaboração de programa CNC', category: 'Operacional', requiresMaintenance: false },
  { code: '50', label: 'Particular Vanderci Escudeiro', category: 'Pessoal', requiresMaintenance: false },
  { code: '51', label: 'Particular Cesar Valochi', category: 'Pessoal', requiresMaintenance: false },
  { code: '60005', label: 'Fabricação de dispositivos', category: 'Operacional', requiresMaintenance: false },

  // --- OPERACIONAL (NÃO QUEBRA A MÁQUINA) ---
  { code: '100', label: 'Setup / Preparação de Máquina', category: 'Operacional', requiresMaintenance: false },
  { code: '101', label: 'Ajuste de Parâmetros', category: 'Operacional', requiresMaintenance: false },
  { code: '102', label: 'Troca de Ferramenta (Desgaste)', category: 'Operacional', requiresMaintenance: false },
  { code: '103', label: 'Troca de Dispositivo', category: 'Operacional', requiresMaintenance: false },
  { code: '104', label: 'Aquecimento de Máquina', category: 'Operacional', requiresMaintenance: false },
  { code: '105', label: 'Teste de Programa', category: 'Operacional', requiresMaintenance: false },
  { code: '106', label: 'Rebarbação Manual na Máquina', category: 'Operacional', requiresMaintenance: false },
  { code: '107', label: 'Abastecimento de Fluido Refrigerante', category: 'Operacional', requiresMaintenance: false },
  { code: '108', label: 'Remoção de Cavacos', category: 'Operacional', requiresMaintenance: false },
  { code: '111', label: 'Troca de Turno', category: 'Operacional', requiresMaintenance: false },
  { code: '112', label: 'Reunião de Produção/DDS', category: 'Operacional', requiresMaintenance: false },

  // --- MANUTENÇÃO MECÂNICA (CRÍTICOS) ---
  { code: '200', label: 'Quebra Mecânica Geral', category: 'Mecânica', requiresMaintenance: true },
  { code: '201', label: 'Vazamento de Óleo Hidráulico', category: 'Mecânica', requiresMaintenance: true },
  { code: '202', label: 'Vazamento de Refrigerante (Grave)', category: 'Mecânica', requiresMaintenance: true },
  { code: '203', label: 'Falha no Eixo Árvore (Spindle)', category: 'Mecânica', requiresMaintenance: true },
  { code: '204', label: 'Falha no Magazine de Ferramentas', category: 'Mecânica', requiresMaintenance: true },
  { code: '205', label: 'Problema na Proteção/Porta Travada', category: 'Mecânica', requiresMaintenance: true },
  { code: '206', label: 'Ruído Anormal / Vibração', category: 'Mecânica', requiresMaintenance: true },
  { code: '207', label: 'Nível de Óleo Baixo (Vazamento)', category: 'Mecânica', requiresMaintenance: true },
  { code: '208', label: 'Falha no Sistema de Fixação', category: 'Mecânica', requiresMaintenance: true },
  { code: '209', label: 'Correia Quebrada/Patim', category: 'Mecânica', requiresMaintenance: true },
  { code: '210', label: 'Travamento de Guias', category: 'Mecânica', requiresMaintenance: true },
  { code: '211', label: 'Falha no Transportador de Cavacos', category: 'Mecânica', requiresMaintenance: true },
  { code: '212', label: 'Aquecimento Excessivo', category: 'Mecânica', requiresMaintenance: true },
  { code: '213', label: 'Manutenção Preventiva Mecânica', category: 'Mecânica', requiresMaintenance: true },
  { code: '214', label: 'Alinhamento/Geometria Fora', category: 'Mecânica', requiresMaintenance: true },

  // --- MANUTENÇÃO ELÉTRICA (CRÍTICOS) ---
  { code: '300', label: 'Pane Elétrica Geral', category: 'Elétrica', requiresMaintenance: true },
  { code: '301', label: 'Falha no Painel de Comando', category: 'Elétrica', requiresMaintenance: true },
  { code: '302', label: 'Servo Motor com Defeito', category: 'Elétrica', requiresMaintenance: true },
  { code: '303', label: 'Sensor Indutivo/Fim de Curso', category: 'Elétrica', requiresMaintenance: true },
  { code: '304', label: 'Fusível Queimado/Disjuntor', category: 'Elétrica', requiresMaintenance: true },
  { code: '305', label: 'Falha no CLP/CNC', category: 'Elétrica', requiresMaintenance: true },
  { code: '306', label: 'Erro de Comunicação de Rede', category: 'Elétrica', requiresMaintenance: true },
  { code: '307', label: 'Iluminação da Máquina (Apagão)', category: 'Elétrica', requiresMaintenance: true },
  { code: '308', label: 'Cabo Rompido/Mau Contato', category: 'Elétrica', requiresMaintenance: true },
  { code: '309', label: 'Bateria do CNC Fraca (Perda de Ref)', category: 'Elétrica', requiresMaintenance: true },
  { code: '310', label: 'Manutenção Preventiva Elétrica', category: 'Elétrica', requiresMaintenance: true },
  { code: '311', label: 'Alarme Crítico Não Reseta', category: 'Elétrica', requiresMaintenance: true },

  // --- QUALIDADE ---
  { code: '400', label: 'Aguardando Inspetor', category: 'Qualidade', requiresMaintenance: false },
  { code: '401', label: 'Inspeção de Primeira Peça', category: 'Qualidade', requiresMaintenance: false },
  { code: '403', label: 'Retrabalho', category: 'Qualidade', requiresMaintenance: false },

  // --- LOGÍSTICA ---
  { code: '500', label: 'Falta de Matéria-Prima', category: 'Logística', requiresMaintenance: false },
  { code: '501', label: 'Aguardando Empilhadeira', category: 'Logística', requiresMaintenance: false },

  // --- OUTROS ---
  { code: '900', label: 'Falta de Ar Comprimido', category: 'Geral', requiresMaintenance: true }, // Impede funcionamento
  { code: '901', label: 'Falta de Água Industrial', category: 'Geral', requiresMaintenance: true },
  { code: '999', label: 'Outros Motivos', category: 'Outros', requiresMaintenance: false }
];

export function getStopLabel(code: string): string {
  const reason = SAP_STOP_REASONS.find(r => r.code === code);
  return reason ? reason.label : `Motivo ${code}`;
}