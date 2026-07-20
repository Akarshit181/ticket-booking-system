import { Role } from '../types/role.type';

export interface User {
  id: string;
  email: string;
  role: Role;
}