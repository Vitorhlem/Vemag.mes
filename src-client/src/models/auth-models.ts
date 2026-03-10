// --- Conteúdo Existente ---
export interface LoginForm {
  email: string;
  password: string;
}

export type UserRole = 
  | 'admin'   
  | 'operator'      
  | 'maintenance'   
  | 'quality'       
  | 'logistics'     
  | 'pcp'           
  | 'manager';      

export type UserSector = 'manufatura' | null;

export interface Organization {
  id: number;
  name: string;
  sector: UserSector;
}

export interface OrganizationNestedInUser {
  id: number;
  name: string;
  sector: UserSector;
}

export interface User {
  id: number;
  full_name: string;
  email: string;
  employee_id: string;
  role: UserRole; 
  is_active: boolean;
  is_superuser: boolean;
  avatar_url: string | null;
  phone: string | null;
  organization: OrganizationNestedInUser | null;
}

export interface TokenData {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UserRegister {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
  sector: UserSector;
}