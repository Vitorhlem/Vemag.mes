// Arquivo: src-client/src/data/sap-stops.ts

export interface SapStopReason {
  code: string;
  label: string;
  category: 'Geral' | 'Operacional' | 'Mecânica' | 'Elétrica' | 'Qualidade' | 'Logística' | 'Pessoal' | 'Outros';
  requiresMaintenance: boolean; // TRUE = Aciona fluxo de quebra/O.M.
  isProductive: boolean; // TRUE = Operador trabalhando (Setup, Medição), FALSE = Perda (Quebra, Espera)
}

export const SAP_STOP_REASONS: SapStopReason[] = [
  // --- LISTA SAP ORIGINAL (LEGADO/OUTROS) ---
  { code: '20', label: 'Aguardando ponte rolante', category: 'Logística', requiresMaintenance: false, isProductive: false },
  { code: '21', label: 'Máquina em manutenção', category: 'Mecânica', requiresMaintenance: true, isProductive: false }, // CRÍTICO
  { code: '22', label: 'Falta de energia elétrica', category: 'Geral', requiresMaintenance: true, isProductive: false }, // Crítico externo
  { code: '23', label: 'Aguardando ferramenta/instrumento', category: 'Logística', requiresMaintenance: false, isProductive: false },
  { code: '24', label: 'Aguardando informação técnica', category: 'Operacional', requiresMaintenance: false, isProductive: false },
  { code: '25', label: 'Aguardando inspeção', category: 'Qualidade', requiresMaintenance: false, isProductive: false },
  { code: '26', label: 'Aguardando peça/material', category: 'Logística', requiresMaintenance: false, isProductive: false },
  { code: '27', label: 'Arrumação/limpeza', category: 'Geral', requiresMaintenance: false, isProductive: true }, // Limpeza é trabalho
  { code: '28', label: 'Aguardando serviço', category: 'Operacional', requiresMaintenance: false, isProductive: false },
  { code: '30', label: 'Treinamento', category: 'Pessoal', requiresMaintenance: false, isProductive: true }, // Treinamento agrega valor
  { code: '31', label: 'Exame médico', category: 'Pessoal', requiresMaintenance: false, isProductive: false },
  { code: '34', label: 'Manutenção predial', category: 'Geral', requiresMaintenance: false, isProductive: false },
  { code: '38', label: 'Assistência do cliente', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '39', label: 'Rastreabilidade de materiais', category: 'Qualidade', requiresMaintenance: false, isProductive: true },
  { code: '40', label: 'Organização de Instrumentos', category: 'Geral', requiresMaintenance: false, isProductive: true },
  { code: '42', label: 'Elaboração de programa CNC', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '50', label: 'Particular Vanderci Escudeiro', category: 'Pessoal', requiresMaintenance: false, isProductive: false },
  { code: '51', label: 'Particular Cesar Valochi', category: 'Pessoal', requiresMaintenance: false, isProductive: false },
  { code: '60005', label: 'Fabricação de dispositivos', category: 'Operacional', requiresMaintenance: false, isProductive: true },

  // --- OPERACIONAL (NÃO QUEBRA A MÁQUINA) ---
  { code: '100', label: 'Setup / Preparação de Máquina', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '101', label: 'Ajuste de Parâmetros', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '102', label: 'Troca de Ferramenta (Desgaste)', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '103', label: 'Troca de Dispositivo', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '104', label: 'Aquecimento de Máquina', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '105', label: 'Teste de Programa', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '106', label: 'Rebarbação Manual na Máquina', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '107', label: 'Abastecimento de Fluido Refrigerante', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '108', label: 'Remoção de Cavacos', category: 'Operacional', requiresMaintenance: false, isProductive: true },
  { code: '111', label: 'Troca de Turno', category: 'Operacional', requiresMaintenance: false, isProductive: false }, // Neutro/Improdutivo para a máquina
  { code: '112', label: 'Reunião de Produção/DDS', category: 'Operacional', requiresMaintenance: false, isProductive: true },

  // --- MANUTENÇÃO MECÂNICA (CRÍTICOS) ---
  { code: '200', label: 'Quebra Mecânica Geral', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '201', label: 'Vazamento de Óleo Hidráulico', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '202', label: 'Vazamento de Refrigerante (Grave)', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '203', label: 'Falha no Eixo Árvore (Spindle)', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '204', label: 'Falha no Magazine de Ferramentas', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '205', label: 'Problema na Proteção/Porta Travada', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '206', label: 'Ruído Anormal / Vibração', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '207', label: 'Nível de Óleo Baixo (Vazamento)', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '208', label: 'Falha no Sistema de Fixação', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '209', label: 'Correia Quebrada/Patim', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '210', label: 'Travamento de Guias', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '211', label: 'Falha no Transportador de Cavacos', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '212', label: 'Aquecimento Excessivo', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '213', label: 'Manutenção Preventiva Mecânica', category: 'Mecânica', requiresMaintenance: true, isProductive: false },
  { code: '214', label: 'Alinhamento/Geometria Fora', category: 'Mecânica', requiresMaintenance: true, isProductive: false },

  // --- MANUTENÇÃO ELÉTRICA (CRÍTICOS) ---
  { code: '300', label: 'Pane Elétrica Geral', category: 'Elétrica', requiresMaintenance: true, isProductive: false },
  { code: '301', label: 'Falha no Painel de Comando', category: 'Elétrica', requiresMaintenance: true, isProductive: false },
  { code: '302', label: 'Servo Motor com Defeito', category: 'Elétrica', requiresMaintenance: true, isProductive: false },
  { code: '303', label: 'Sensor Indutivo/Fim de Curso', category: 'Elétrica', requiresMaintenance: true, isProductive: false },
  { code: '304', label: 'Fusível Queimado/Disjuntor', category: 'Elétrica', requiresMaintenance: true, isProductive: false },
  { code: '305', label: 'Falha no CLP/CNC', category: 'Elétrica', requiresMaintenance: true, isProductive: false },
  { code: '306', label: 'Erro de Comunicação de Rede', category: 'Elétrica', requiresMaintenance: true, isProductive: false },
  { code: '307', label: 'Iluminação da Máquina (Apagão)', category: 'Elétrica', requiresMaintenance: true, isProductive: false },
  { code: '308', label: 'Cabo Rompido/Mau Contato', category: 'Elétrica', requiresMaintenance: true, isProductive: false },
  { code: '309', label: 'Bateria do CNC Fraca (Perda de Ref)', category: 'Elétrica', requiresMaintenance: true, isProductive: false },
  { code: '310', label: 'Manutenção Preventiva Elétrica', category: 'Elétrica', requiresMaintenance: true, isProductive: false },
  { code: '311', label: 'Alarme Crítico Não Reseta', category: 'Elétrica', requiresMaintenance: true, isProductive: false },

  // --- QUALIDADE ---
  { code: '400', label: 'Aguardando Inspetor', category: 'Qualidade', requiresMaintenance: false, isProductive: false },
  { code: '401', label: 'Inspeção de Primeira Peça', category: 'Qualidade', requiresMaintenance: false, isProductive: true }, // Necessário
  { code: '403', label: 'Retrabalho', category: 'Qualidade', requiresMaintenance: false, isProductive: true },

  // --- LOGÍSTICA ---
  { code: '500', label: 'Falta de Matéria-Prima', category: 'Logística', requiresMaintenance: false, isProductive: false },
  { code: '501', label: 'Aguardando Empilhadeira', category: 'Logística', requiresMaintenance: false, isProductive: false },

  // --- OUTROS ---
  { code: '900', label: 'Falta de Ar Comprimido', category: 'Geral', requiresMaintenance: true, isProductive: false }, // Impede funcionamento
  { code: '901', label: 'Falta de Água Industrial', category: 'Geral', requiresMaintenance: true, isProductive: false },
  { code: '999', label: 'Outros Motivos', category: 'Outros', requiresMaintenance: false, isProductive: false }
];

export function getStopLabel(code: string): string {
  const reason = SAP_STOP_REASONS.find(r => r.code === code);
  return reason ? reason.label : `Motivo ${code}`;
}