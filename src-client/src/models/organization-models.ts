import type { UserRole, UserSector } from './auth-models';

export interface OrganizationNestedInUser {
  id: number;
  name: string;
  sector: UserSector;
}

export interface UserNestedInOrganization {
  id: number;
  role: UserRole;
}

export interface OrganizationBase {
  name: string;
  sector: UserSector;
  cnpj?: string;
  address?: string;
  contact_phone?: string;
  website?: string;
  // ------------------------------------------
}

export interface Organization extends OrganizationBase {
  id: number;
  users: UserNestedInOrganization[];

}

export type OrganizationPublic = Organization;
// ------------------------

export interface OrganizationUpdate {
  name?: string;
  sector?: UserSector;
  cnpj?: string;
  address?: string;
  contact_phone?: string;
  website?: string;
  // ------------------------------------
}
