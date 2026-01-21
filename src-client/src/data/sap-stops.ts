// Arquivo: src-client/src/data/sap-stops.ts

export interface SapStopReason {
  code: string;
  label: string;
  category: 'Geral' | 'Operacional' | 'Mecânica' | 'Elétrica' | 'Qualidade' | 'Logística' | 'Pessoal' | 'Outros';
  requiresMaintenance?: boolean; // Se true, sugere abertura de O.M.
}

// AQUI ESTÁ A EXPORTAÇÃO CORRETA QUE O SEU ERRO PEDE:
export const SAP_STOP_REASONS: SapStopReason[] = [
  // --- LISTA SAP ORIGINAL (CÓDIGOS FIXOS 20-60005) ---
  { code: '20', label: 'Aguardando ponte rolante', category: 'Logística' },
  { code: '21', label: 'Máquina em manutenção', category: 'Mecânica', requiresMaintenance: true },
  { code: '22', label: 'Falta de energia elétrica', category: 'Geral' },
  { code: '23', label: 'Aguardando ferramenta/instrumento', category: 'Logística' },
  { code: '24', label: 'Aguardando informação técnica', category: 'Operacional' },
  { code: '25', label: 'Aguardando inspeção', category: 'Qualidade' },
  { code: '26', label: 'Aguardando peça/material', category: 'Logística' },
  { code: '27', label: 'Arrumação/limpeza', category: 'Geral' },
  { code: '28', label: 'Aguardando serviço', category: 'Operacional' },
  { code: '30', label: 'Treinamento', category: 'Pessoal' },
  { code: '31', label: 'Exame médico', category: 'Pessoal' },
  { code: '34', label: 'Manutenção predial', category: 'Geral' },
  { code: '38', label: 'Assistência do cliente', category: 'Operacional' },
  { code: '39', label: 'Rastreabilidade de materiais', category: 'Qualidade' },
  { code: '40', label: 'Organização de Instrumentos', category: 'Geral' },
  { code: '42', label: 'Elaboração de programa CNC', category: 'Operacional' },
  { code: '50', label: 'Particular Vanderci Escudeiro', category: 'Pessoal' },
  { code: '51', label: 'Particular Cesar Valochi', category: 'Pessoal' },
  { code: '60005', label: 'Fabricação de dispositivos', category: 'Operacional' },

  // --- EXPANSÃO OPERACIONAL (100-199) ---
  { code: '100', label: 'Setup / Preparação de Máquina', category: 'Operacional' },
  { code: '101', label: 'Ajuste de Parâmetros', category: 'Operacional' },
  { code: '102', label: 'Troca de Ferramenta (Desgaste)', category: 'Operacional' },
  { code: '103', label: 'Troca de Dispositivo', category: 'Operacional' },
  { code: '104', label: 'Aquecimento de Máquina', category: 'Operacional' },
  { code: '105', label: 'Teste de Programa', category: 'Operacional' },
  { code: '106', label: 'Rebarbação Manual na Máquina', category: 'Operacional' },
  { code: '107', label: 'Abastecimento de Fluido Refrigerante', category: 'Operacional' },
  { code: '108', label: 'Remoção de Cavacos', category: 'Operacional' },
  { code: '109', label: 'Conferência de Medidas (Operador)', category: 'Operacional' },
  { code: '110', label: 'Apontamento de Produção (Sistema)', category: 'Operacional' },
  { code: '111', label: 'Troca de Turno', category: 'Operacional' },
  { code: '112', label: 'Reunião de Produção/DDS', category: 'Operacional' },
  { code: '113', label: 'Ausência de Operador', category: 'Operacional' },
  { code: '114', label: 'Máquina sem Operador Programado', category: 'Operacional' },
  { code: '115', label: 'Organização do Posto de Trabalho (5S)', category: 'Operacional' },
  { code: '116', label: 'Leitura de Desenho Técnico', category: 'Operacional' },
  { code: '117', label: 'Busca de Ferramentas no Almoxarifado', category: 'Operacional' },
  { code: '118', label: 'Preenchimento de Documentação', category: 'Operacional' },
  { code: '119', label: 'Ajuda a outro Operador', category: 'Operacional' },

  // --- EXPANSÃO MANUTENÇÃO MECÂNICA (200-299) ---
  { code: '200', label: 'Quebra Mecânica Geral', category: 'Mecânica', requiresMaintenance: true },
  { code: '201', label: 'Vazamento de Óleo Hidráulico', category: 'Mecânica', requiresMaintenance: true },
  { code: '202', label: 'Vazamento de Refrigerante', category: 'Mecânica', requiresMaintenance: true },
  { code: '203', label: 'Falha no Eixo Árvore (Spindle)', category: 'Mecânica', requiresMaintenance: true },
  { code: '204', label: 'Falha no Magazine de Ferramentas', category: 'Mecânica', requiresMaintenance: true },
  { code: '205', label: 'Problema na Proteção/Porta', category: 'Mecânica', requiresMaintenance: true },
  { code: '206', label: 'Ruído Anormal', category: 'Mecânica', requiresMaintenance: true },
  { code: '207', label: 'Nível de Óleo Baixo', category: 'Mecânica', requiresMaintenance: true },
  { code: '208', label: 'Falha no Sistema de Fixação', category: 'Mecânica', requiresMaintenance: true },
  { code: '209', label: 'Correia Quebrada/Patim', category: 'Mecânica', requiresMaintenance: true },
  { code: '210', label: 'Lubrificação de Guias', category: 'Mecânica', requiresMaintenance: true },
  { code: '211', label: 'Falha no Transportador de Cavacos', category: 'Mecânica', requiresMaintenance: true },
  { code: '212', label: 'Aquecimento Excessivo', category: 'Mecânica', requiresMaintenance: true },
  { code: '213', label: 'Manutenção Preventiva Mecânica', category: 'Mecânica', requiresMaintenance: true },
  { code: '214', label: 'Alinhamento/Geometria', category: 'Mecânica', requiresMaintenance: true },

  // --- EXPANSÃO MANUTENÇÃO ELÉTRICA/ELETRÔNICA (300-399) ---
  { code: '300', label: 'Pane Elétrica Geral', category: 'Elétrica', requiresMaintenance: true },
  { code: '301', label: 'Falha no Painel de Comando', category: 'Elétrica', requiresMaintenance: true },
  { code: '302', label: 'Servo Motor com Defeito', category: 'Elétrica', requiresMaintenance: true },
  { code: '303', label: 'Sensor Indutivo/Fim de Curso', category: 'Elétrica', requiresMaintenance: true },
  { code: '304', label: 'Fusível Queimado/Disjuntor', category: 'Elétrica', requiresMaintenance: true },
  { code: '305', label: 'Falha no CLP/CNC', category: 'Elétrica', requiresMaintenance: true },
  { code: '306', label: 'Erro de Comunicação de Rede', category: 'Elétrica', requiresMaintenance: true },
  { code: '307', label: 'Iluminação da Máquina', category: 'Elétrica', requiresMaintenance: true },
  { code: '308', label: 'Cabo Rompido/Mau Contato', category: 'Elétrica', requiresMaintenance: true },
  { code: '309', label: 'Bateria do CNC Fraca', category: 'Elétrica', requiresMaintenance: true },
  { code: '310', label: 'Manutenção Preventiva Elétrica', category: 'Elétrica', requiresMaintenance: true },
  { code: '311', label: 'Reset de Alarme Crítico', category: 'Elétrica', requiresMaintenance: true },

  // --- EXPANSÃO QUALIDADE (400-499) ---
  { code: '400', label: 'Aguardando Inspetor Volante', category: 'Qualidade' },
  { code: '401', label: 'Inspeção de Primeira Peça', category: 'Qualidade' },
  { code: '402', label: 'Separação de Lote Suspeito', category: 'Qualidade' },
  { code: '403', label: 'Retrabalho na Máquina', category: 'Qualidade' },
  { code: '404', label: 'Aguardando Calibração de Instrumento', category: 'Qualidade' },
  { code: '405', label: 'Análise de Trinca/Material', category: 'Qualidade' },
  { code: '406', label: 'Aguardando Gabarito de Controle', category: 'Qualidade' },
  { code: '407', label: 'Preenchimento de Carta CEP', category: 'Qualidade' },
  { code: '408', label: 'Problema de Qualidade com MP', category: 'Qualidade' },
  { code: '409', label: 'Auditoria de Processo', category: 'Qualidade' },

  // --- EXPANSÃO LOGÍSTICA/MATERIAIS (500-599) ---
  { code: '500', label: 'Falta de Matéria-Prima', category: 'Logística' },
  { code: '501', label: 'Aguardando Empilhadeira', category: 'Logística' },
  { code: '502', label: 'Aguardando Contentor/Caixa', category: 'Logística' },
  { code: '503', label: 'Retirada de Peças Prontas', category: 'Logística' },
  { code: '504', label: 'Aguardando Programação (PCP)', category: 'Logística' },
  { code: '505', label: 'Falta de Consumíveis (EPIs/Outros)', category: 'Logística' },
  { code: '506', label: 'Movimentação de Material Manual', category: 'Logística' },
  { code: '507', label: 'Identificação de Lotes', category: 'Logística' },

  // --- EXPANSÃO PESSOAL/RH (600-699) ---
  { code: '600', label: 'Horário de Refeição', category: 'Pessoal' },
  { code: '601', label: 'Necessidades Fisiológicas', category: 'Pessoal' },
  { code: '602', label: 'Ginástica Laboral', category: 'Pessoal' },
  { code: '603', label: 'Descanso Regulamentar', category: 'Pessoal' },
  { code: '604', label: 'Atendimento no RH/DP', category: 'Pessoal' },
  { code: '605', label: 'Reunião Sindical', category: 'Pessoal' },
  { code: '606', label: 'Mal Estar / Enfermaria', category: 'Pessoal' },
  { code: '607', label: 'Café / Água', category: 'Pessoal' },

  // --- EXPANSÃO OUTROS (900-999) ---
  { code: '900', label: 'Falta de Ar Comprimido', category: 'Geral', requiresMaintenance: true },
  { code: '901', label: 'Falta de Água Industrial', category: 'Geral' },
  { code: '902', label: 'Queda de Sistema / Rede', category: 'Geral' },
  { code: '903', label: 'Limpeza Geral da Fábrica', category: 'Geral' },
  { code: '904', label: 'Obras / Reformas Próximas', category: 'Geral' },
  { code: '905', label: 'Consultoria Externa', category: 'Geral' },
  { code: '906', label: 'Testes de Engenharia', category: 'Geral' },
  { code: '999', label: 'Outros Motivos (Não Listados)', category: 'Outros' }
];

// Função auxiliar para buscar o label pelo código
export function getStopLabel(code: string): string {
  const reason = SAP_STOP_REASONS.find(r => r.code === code);
  return reason ? reason.label : `Motivo ${code}`;
}