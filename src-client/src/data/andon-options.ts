// Arquivo: src-client/src/data/andon-options.ts

export interface AndonOption {
  label: string;
  icon: string;
  color: string;
}

export const ANDON_OPTIONS: AndonOption[] = [
  { label: 'Manutenção', icon: 'build', color: 'blue-grey-9' },
  { label: 'Elétrica', icon: 'bolt', color: 'orange-9' },
  { label: 'Logística', icon: 'forklift', color: 'brown-6' },
  { label: 'PCP', icon: 'calendar_month', color: 'deep-purple-7' }, // Adicionado
  { label: 'Qualidade', icon: 'verified', color: 'purple-8' },
  { label: 'Gerente', icon: 'admin_panel_settings', color: 'red-10' },
  { label: 'Segurança', icon: 'health_and_safety', color: 'red-9' },
  { label: 'Processo', icon: 'engineering', color: 'teal-7' }
];