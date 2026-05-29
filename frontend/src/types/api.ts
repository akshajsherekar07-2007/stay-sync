/**
 * Shared API response type definitions.
 * Matches the response envelope defined in PROJECT_RULES.md §5.3-5.4.
 */

/** Standard success response envelope */
export interface ApiResponse<T> {
  success: true;
  data: T;
  message: string;
  meta?: PaginationMeta;
}

/** Standard error response envelope */
export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}

/** Pagination metadata */
export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

/** Paginated list response */
export interface PaginatedResponse<T> {
  success: true;
  data: T[];
  message: string;
  meta: PaginationMeta;
}
