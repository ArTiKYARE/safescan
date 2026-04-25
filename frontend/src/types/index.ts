// SafeScan — Complete TypeScript Types

// ==================== Auth ====================

export interface User {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  mfa_enabled: boolean;
  email_verified: boolean;
  role: string;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
  balance: number;
  free_scans_remaining: number;
}

export interface LoginRequest {
  email: string;
  password: string;
  mfa_token?: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// ==================== Domain ====================

export interface Domain {
  id: string;
  domain: string;
  is_verified: boolean;
  verification_method: string | null;
  verified_at: string | null;
  scan_consent_required: boolean;
  created_at: string;
  updated_at: string;
  // API key fields (returned when verification_method is api_token)
  api_key?: string;
  api_key_prefix?: string;
  env_line?: string;
}

export interface DomainCreate {
  domain: string;
  verification_method: "dns" | "file" | "email" | "api_token";
}

export interface DomainVerificationStatus {
  domain_id: string;
  domain: string;
  is_verified: boolean;
  verification_method: string | null;
  verification_token: string | null;
  dns_record_name: string | null;
  dns_record_value: string | null;
  verification_file_path: string | null;
  verification_email_sent_to: string | null;
  instructions: string;
}

// ==================== Scan ====================

export type ScanStatus = "pending" | "queued" | "running" | "completed" | "failed" | "cancelled";
export type ScanType = "full" | "quick" | "custom";

export interface Scan {
  id: string;
  domain_id: string;
  domain: string;
  user_id: string;
  scan_type: ScanType;
  status: ScanStatus;
  modules_enabled: string[] | null;
  current_module: string | null;
  progress_percentage: number;
  pages_crawled: number;
  requests_made: number;
  total_findings: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  risk_score: number | null;
  grade: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  error_message: string | null;
}

export interface ScanSummary {
  id: string;
  domain: string;
  scan_type: ScanType;
  status: ScanStatus;
  total_findings: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  grade: string | null;
  completed_at: string | null;
}

export interface ScanCreate {
  domain_id: string;
  scan_type: ScanType;
  modules?: string[];
  consent_acknowledged: boolean;
}

export interface ScanStatusResponse {
  scan_id: string;
  status: ScanStatus;
  current_module: string | null;
  progress_percentage: number;
  pages_crawled: number;
  requests_made: number;
  estimated_completion: string | null;
}

// ==================== Vulnerability ====================

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export interface Vulnerability {
  id: string;
  scan_id: string;
  module: string;
  title: string;
  description: string;
  severity: Severity;
  cvss_score: number | null;
  cvss_vector: string | null;
  affected_url: string | null;
  affected_parameter: string | null;
  evidence: string | null;
  remediation: string | null;
  remediation_priority: string | null;
  cwe_id: string | null;
  cwe_name: string | null;
  owasp_category: string | null;
  owasp_name: string | null;
  nist_control: string | null;
  pci_dss_req: string | null;
  false_positive: boolean;
  is_resolved: boolean;
  created_at: string;
}

export interface VulnerabilitySummary {
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  risk_score: number | null;
  grade: string | null;
}

// ==================== Report ====================

export interface ReportJSON {
  report: {
    metadata: {
      scan_id: string;
      domain: string;
      scan_date: string;
      scan_duration: string;
      scanner_version: string;
    };
    summary: {
      total_findings: number;
      critical: number;
      high: number;
      medium: number;
      low: number;
      info: number;
      risk_score: number;
      grade: string;
    };
    vulnerabilities: Array<{
      id: string;
      module: string;
      title: string;
      description: string;
      severity: Severity;
      cvss: { score: number | null; vector: string | null } | null;
      affected: string | null;
      evidence: string | null;
      remediation: string | null;
      cwe: string | null;
      owasp: string | null;
    }>;
    compliance: {
      owasp_top_10: Record<string, string>;
      pci_dss: { compliant: boolean; failures: string[] };
    };
  };
}

// ==================== API Key ====================

export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  secret: string | null;
  scopes: string;
  expires_at: string | null;
  last_used_at: string | null;
  is_active: boolean;
  is_revoked: boolean;
  usage_count: number;
  created_at: string;
}

export interface APIKeyWithSecret extends APIKey {
  secret: string;
}

export interface APIKeyCreate {
  name: string;
  scopes: string;
  expires_in_days?: number;
  allowed_ips?: string;
}

// ==================== Dashboard ====================

export interface DashboardStats {
  total_scans: number;
  active_scans: number;
  total_domains: number;
  verified_domains: number;
  total_vulnerabilities: number;
  critical_vulnerabilities: number;
  severity_distribution: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
  recent_scans: ScanSummary[];
}

// ==================== Settings ====================

export interface UserSettings {
  notifications: {
    email: boolean;
    webhook: boolean;
    slack: boolean;
  };
  scan_defaults: {
    scan_type: ScanType;
    consent_required: boolean;
  };
}

// ==================== Misc ====================

export interface ApiError {
  detail: string;
}

export interface MessageResponse {
  message: string;
}
