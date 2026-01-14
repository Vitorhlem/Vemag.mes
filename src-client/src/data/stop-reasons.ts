export const STOP_REASONS = [
  // --- MECÂNICA ---
  { category: 'Mecânica', label: 'Quebra de Ferramenta' },
  { category: 'Mecânica', label: 'Vazamento de Óleo' },
  { category: 'Mecânica', label: 'Aquecimento do Eixo' },
  { category: 'Mecânica', label: 'Correia Quebrada' },
  { category: 'Mecânica', label: 'Falha Hidráulica' },
  { category: 'Mecânica', label: 'Vibração Excessiva' },
  { category: 'Mecânica', label: 'Problema na Fixação' },
  { category: 'Mecânica', label: 'Desalinhamento' },
  { category: 'Mecânica', label: 'Falha no Rolamento' },
  { category: 'Mecânica', label: 'Proteção Travada' },

  // --- ELÉTRICA ---
  { category: 'Elétrica', label: 'Queda de Energia' },
  { category: 'Elétrica', label: 'Erro no Inversor' },
  { category: 'Elétrica', label: 'Sensor Sujo/Falha' },
  { category: 'Elétrica', label: 'Curto Circuito' },
  { category: 'Elétrica', label: 'Motor Queimado' },
  { category: 'Elétrica', label: 'Painel Apagou' },
  { category: 'Elétrica', label: 'Fusível Queimado' },
  { category: 'Elétrica', label: 'Cabo Rompido' },
  { category: 'Elétrica', label: 'Falha de Comunicação PLC' },
  { category: 'Elétrica', label: 'Botão de Emergência Acionado' },

  // --- OPERACIONAL ---
  { category: 'Operacional', label: 'Troca de Turno' },
  { category: 'Operacional', label: 'Refeição / Intervalo' },
  { category: 'Operacional', label: 'Reunião Diária' },
  { category: 'Operacional', label: 'Ginástica Laboral' },
  { category: 'Operacional', label: 'Treinamento' },
  { category: 'Operacional', label: 'Ausência do Operador' },
  { category: 'Operacional', label: 'Erro Operacional' },
  { category: 'Operacional', label: 'Limpeza do Posto' },
  { category: 'Operacional', label: 'Preenchimento de Documentos' },
  { category: 'Operacional', label: 'Banheiro' },

  // --- LOGÍSTICA ---
  { category: 'Logística', label: 'Falta de Matéria Prima' },
  { category: 'Logística', label: 'Falta de Embalagem' },
  { category: 'Logística', label: 'Aguardando Empilhadeira' },
  { category: 'Logística', label: 'Expedição Lotada' },
  { category: 'Logística', label: 'Peça não chegou' },
  { category: 'Logística', label: 'Retirada de Cavacos' },
  { category: 'Logística', label: 'Falta de Pallet' },
  
  // --- QUALIDADE ---
  { category: 'Qualidade', label: 'Aguardando Aprovação' },
  { category: 'Qualidade', label: 'Medição de Peça' },
  { category: 'Qualidade', label: 'Peça Refugada' },
  { category: 'Qualidade', label: 'Ajuste Dimensional' },
  { category: 'Qualidade', label: 'Teste de Laboratório' },
  { category: 'Qualidade', label: 'Ferramenta de Medição Quebrada' },

  // --- SETUP ---
  { category: 'Setup', label: 'Troca de Modelo' },
  { category: 'Setup', label: 'Ajuste de Máquina' },
  { category: 'Setup', label: 'Troca de Ferramental' },
  { category: 'Setup', label: 'Aquecimento da Máquina' },
  { category: 'Setup', label: 'Carregamento de Programa' },
  
  // --- OUTROS ---
  { category: 'Outros', label: 'Teste de Engenharia' },
  { category: 'Outros', label: 'Falta de Ar Comprimido' },
  { category: 'Outros', label: 'Goteira / Infraestrutura' }
  
];