/**
 * Shared API response type definitions.
 * Matches the response envelope defined in backend/app/schemas/common.py.
 */

/** Response metadata attached to every API response */
export interface ResponseMeta {
  request_id: string;
  api_version: string;
}

/** Standard success response envelope */
export interface ApiResponse<T> {
  success: true;
  data: T;
  error: null;
  meta: ResponseMeta;
}

/** Simple message response (logout, delete, etc.) */
export interface MessageResponse {
  success: true;
  message: string;
  error: null;
  meta: ResponseMeta;
}

/** Pagination metadata */
export interface PaginationInfo {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

/** Paginated list response */
export interface PaginatedResponse<T> {
  success: true;
  data: T[];
  pagination: PaginationInfo;
  error: null;
  meta: ResponseMeta;
}

/** Structured error detail */
export interface ErrorDetail {
  code: string;
  message: string;
  details: Record<string, unknown>;
}

/** Standard error response envelope */
export interface ApiErrorResponse {
  success: false;
  data: null;
  error: ErrorDetail;
  meta: ResponseMeta;
}
