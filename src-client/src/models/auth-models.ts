// --- Conteúdo Existente ---
export interface LoginForm {
  email: string;
  password: string;
}

// ATUALIZADO: Adicionados os cargos do sistema MES (Manutenção, Qualidade, etc)
export type UserRole = 
  | 'cliente_ativo' 
  | 'cliente_demo' 
  | 'admin' 
  | 'driver'        // Mantido conforme seu pedido
  | 'operator'      // Novo: Operador de Máquina
  | 'maintenance'   // Novo: Manutenção
  | 'quality'       // Novo: Qualidade
  | 'logistics'     // Novo: Logística Interna
  | 'pcp'           // Novo: PCP
  | 'manager';      // Novo: Gerente Industrial

export type UserSector = 'agronegocio' | 'frete' | 'servicos' | 'construcao_civil' | null;

export interface Organization {
  id: number;
  name: string;
  sector: UserSector;
  part_limit?: number;
}

export interface OrganizationNestedInUser {
  id: number;
  name: string;
  sector: UserSector;
  // --- CAMPOS DE LIMITE ---
  vehicle_limit: number;
  driver_limit: number;
  freight_order_limit: number;
  maintenance_limit: number;
  part_limit?: number;
}

export interface User {
  id: number;
  full_name: string;
  email: string;
  employee_id: string;
  role: UserRole; // Agora aceita os novos cargos
  is_active: boolean;
  is_superuser: boolean;
  avatar_url: string | null;
  notify_in_app: boolean;
  phone: string | null;
  notify_by_email: boolean;
  notification_email: string | null;
  organization: OrganizationNestedInUser | null;
}

export interface TokenData {
  access_token: string;
  token_type: string;
  user: User;
}

export interface PasswordRecoveryRequest {
  email: string;
}

export interface PasswordResetRequest {
  token: string;
  new_password: string;
}

export interface UserRegister {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
  sector: UserSector;
}