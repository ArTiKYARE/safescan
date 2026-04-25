import { api } from './api';
import type { User } from '@/types';

export interface AdminUser extends User {
  is_blocked: boolean;
  blocked_reason: string | null;
  failed_login_attempts: number;
  locked_until: string | null;
  domain_count?: number;
  scan_count?: number;
}

export interface AdminDomain {
  id: string;
  domain: string;
  is_verified: boolean;
  verification_method: string | null;
  verified_at: string | null;
  created_at: string;
}

export const adminApi = {
  listUsers: () => api.get<AdminUser[]>('/admin/users'),
  getUser: (userId: string) => api.get<AdminUser>(`/admin/users/${userId}`),
  getUserDomains: (userId: string) => api.get<AdminDomain[]>(`/admin/users/${userId}/domains`),
  approveDomain: (userId: string, domainId: string) =>
    api.post(`/admin/users/${userId}/domains/${domainId}/approve`),
  addBalance: (userId: string, amount: number, description?: string) =>
    api.post(`/admin/users/${userId}/balance?amount=${amount}${description ? `&description=${encodeURIComponent(description)}` : ''}`),
  updateUser: (userId: string, params: Record<string, string | boolean>) =>
    api.put(`/admin/users/${userId}`, null, { params }),
  deleteUser: (userId: string) =>
    api.delete(`/admin/users/${userId}`),
  getStats: () => api.get<{ total_users: number; by_role: Record<string, number> }>('/admin/stats'),
};
